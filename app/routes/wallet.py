# app/routes/wallet.py
# Billetera, reportes y gastos

# Importaciones estándar
from datetime import datetime, date, timedelta
from decimal import Decimal
import os
import uuid
import holidays
import io

# Importaciones de SQLAlchemy
from sqlalchemy import func, case, join, tuple_, and_, or_
from sqlalchemy.orm import joinedload

# Importaciones de Flask
from flask import (
    request, render_template, session, redirect,
    url_for, flash, abort, jsonify, send_file
)
import pandas as pd
from werkzeug.utils import secure_filename

# Importaciones de modelos
from app.models import (
    db, User, Client, Loan, Employee, LoanInstallment,
    InstallmentStatus, Concept, Transaction, Role, Manager,
    Payment, Salesman, TransactionType, ApprovalStatus, EmployeeRecord
)

# Importar el blueprint
from app.routes import routes

# Importar funciones auxiliares
from app.routes.helpers import (
    safe_cache, BOX_STATUS, calculate_status_box, is_workday,
    generate_loan_installments, distribute_advance_payment,
    recalculate_loan_installments, get_loan_details,
    validate_coordinator_access, get_coordinator_data,
    get_pure_salesmen_ids, calculate_daily_transaction_totals,
    get_salesman_daily_collections, get_salesman_new_clients_data,
    get_salesman_renewals_data, get_salesman_transaction_data,
    get_salesman_customers_data, get_salesman_pending_installments,
    check_all_loans_paid_today, calculate_box_value,
    get_salesman_transaction_details, get_salesman_collected_clients,
    get_coordinator_expenses, get_all_salesmen_data_optimized,
    get_all_salesmen_additional_data_optimized,
    get_all_salesmen_data_optimized_history,
    get_all_salesmen_additional_data_optimized_history,
    calculate_daily_transaction_totals_history,
    validate_coordinator_employee_access,
    process_salesman_record, process_coordinator_hierarchy
)

@routes.route('/wallet')
def wallet():
    try:
        # Verificar si el usuario está logueado
        if 'user_id' not in session:
            return redirect(url_for('routes.home'))
        
        # Initialize variables
        total_cash = 0
        total_active_sellers = 0
        user_id = session.get('user_id')

        # Obtener el employee_id asociado al user_id
        employee = Employee.query.filter_by(user_id=user_id).first()
        
        if not employee:
            return jsonify({'message': 'Empleado no encontrado'}), 404

        # Obtener el administrador principal (usuario logueado)
        main_admin = Manager.query.filter_by(employee_id=employee.id).first()
        
        # Obtener sub-administradores activos (con employee.status = True)
        # Solo aquellos que están bajo la jerarquía del main_admin
        subadmins = []
        if main_admin:
            def get_subordinate_managers(manager_id, visited=None):
                if visited is None:
                    visited = set()
                sub_mgrs = []
                if manager_id in visited:
                    return sub_mgrs
                visited.add(manager_id)
                
                salesmen = Salesman.query.filter_by(manager_id=manager_id).all()
                for s in salesmen:
                    if s.employee:
                        mgr = Manager.query.filter_by(employee_id=s.employee_id).first()
                        if mgr and mgr.id not in visited:
                            sub_mgrs.append(mgr)
                            sub_mgrs.extend(get_subordinate_managers(mgr.id, visited))
                return sub_mgrs
                
            all_sub_mgrs = get_subordinate_managers(main_admin.id)
            seen = {main_admin.id}  # Evitar que el main_admin aparezca como subadmin de sí mismo si hay un ciclo
            for m in all_sub_mgrs:
                if m.id not in seen:
                    subadmins.append(m)
                    seen.add(m.id)

        def get_all_subordinate_employee_ids(manager_id, visited=None):
            if visited is None:
                visited = set()
            if manager_id in visited:
                return []
            visited.add(manager_id)
            
            emp_ids = []
            mgr = Manager.query.get(manager_id)
            if mgr and mgr.employee_id:
                emp_ids.append(mgr.employee_id)
            
            salesmen = Salesman.query.filter_by(manager_id=manager_id).all()
            for s in salesmen:
                if s.employee_id:
                    emp_ids.append(s.employee_id)
                    sub_mgr = Manager.query.filter_by(employee_id=s.employee_id).first()
                    if sub_mgr:
                        emp_ids.extend(get_all_subordinate_employee_ids(sub_mgr.id, visited))
            return list(set(emp_ids))

        def get_wallet_data_optimized(employee_ids):
            """Obtiene datos de cartera optimizados en consultas bulk para evitar N+1"""
            if not employee_ids:
                return {}
            
            # 1. Obtener todos los clientes con préstamos activos en una sola consulta
            # Solo incluir clientes de empleados
            clients_with_loans = db.session.query(
                Client.employee_id,
                Client.id.label('client_id'),
                Loan.id.label('loan_id'),
                Loan.amount.label('loan_amount'),
                Loan.interest.label('loan_interest')
            ).join(
                Loan, Loan.client_id == Client.id
            ).join(
                Employee, Client.employee_id == Employee.id
            ).filter(
                Client.employee_id.in_(employee_ids),
                Loan.status == True  # Solo préstamos activos
            ).all()
            
            # 2. Obtener todas las primeras cuotas en una sola consulta
            today = date.today()
            loan_ids = [row.loan_id for row in clients_with_loans]
            first_installments = {}
            first_inst_overdue_amounts = {}  # Montos de primeras cuotas que están vencidas
            if loan_ids:
                # Subconsulta para obtener el ID de la primera cuota de cada préstamo
                subquery = db.session.query(
                    LoanInstallment.loan_id,
                    func.min(LoanInstallment.due_date).label('min_due_date')
                ).filter(
                    LoanInstallment.loan_id.in_(loan_ids)
                ).group_by(LoanInstallment.loan_id).subquery()
                
                # Obtener las primeras cuotas con datos adicionales
                first_inst_query = db.session.query(
                    LoanInstallment.loan_id,
                    LoanInstallment.fixed_amount,
                    LoanInstallment.due_date,
                    LoanInstallment.amount,
                    LoanInstallment.status
                ).join(
                    subquery,
                    and_(
                        LoanInstallment.loan_id == subquery.c.loan_id,
                        LoanInstallment.due_date == subquery.c.min_due_date
                    )
                ).all()
                
                for row in first_inst_query:
                    first_installments[row.loan_id] = row.fixed_amount
            
            # 3. Obtener todas las cuotas pendientes, en mora y abonadas para calcular balance
            # Se incluye ABONADA porque las cuotas parcialmente pagadas aún tienen saldo por cobrar
            installments_data = {}
            if loan_ids:
                installments_query = db.session.query(
                    LoanInstallment.loan_id,
                    LoanInstallment.status,
                    func.sum(LoanInstallment.amount).label('total_amount')
                ).filter(
                    LoanInstallment.loan_id.in_(loan_ids),
                    LoanInstallment.status.in_([InstallmentStatus.PENDIENTE, InstallmentStatus.MORA, InstallmentStatus.ABONADA])
                ).group_by(
                    LoanInstallment.loan_id,
                    LoanInstallment.status
                ).all()
                
                for row in installments_query:
                    if row.loan_id not in installments_data:
                        installments_data[row.loan_id] = {'PENDIENTE': 0, 'MORA': 0, 'ABONADA': 0}
                    installments_data[row.loan_id][row.status.value] = float(row.total_amount or 0)
            
            # 4. Obtener cuotas vencidas para calcular "Vencido"
            # Fórmula: Para préstamos con al menos una cuota en MORA, 
            # sumar todas las cuotas MORA + PENDIENTE con due_date < hoy
            overdue_installments = {}
            if loan_ids:
                # Encontrar préstamos que tienen al menos una cuota en MORA
                mora_loans_subquery = db.session.query(LoanInstallment.loan_id).filter(
                    LoanInstallment.loan_id.in_(loan_ids),
                    LoanInstallment.status == InstallmentStatus.MORA
                ).distinct().subquery()
                
                overdue_query = db.session.query(
                    LoanInstallment.loan_id,
                    LoanInstallment.amount
                ).join(
                    Loan, Loan.id == LoanInstallment.loan_id
                ).join(
                    mora_loans_subquery, mora_loans_subquery.c.loan_id == LoanInstallment.loan_id
                ).filter(
                    Loan.status == True,
                    or_(
                        LoanInstallment.status == InstallmentStatus.MORA,
                        and_(
                            LoanInstallment.status == InstallmentStatus.PENDIENTE,
                            LoanInstallment.due_date < today
                        )
                    )
                ).all()
                
                # Sumar el monto de cada cuota vencida
                for row in overdue_query:
                    if row.loan_id not in overdue_installments:
                        overdue_installments[row.loan_id] = 0
                    overdue_installments[row.loan_id] += float(row.amount or 0)
            
            # 5. Obtener pagos realizados hoy para calcular porcentaje de recaudación
            collections_today = {}
            collections_query = db.session.query(
                Client.employee_id,
                func.sum(Payment.amount).label('total_collected')
            ).join(
                Loan, Loan.client_id == Client.id
            ).join(
                LoanInstallment, LoanInstallment.loan_id == Loan.id
            ).join(
                Payment, Payment.installment_id == LoanInstallment.id
            ).join(
                Employee, Client.employee_id == Employee.id
            ).filter(
                Client.employee_id.in_(employee_ids),
                func.date(Payment.payment_date) == today
            ).group_by(Client.employee_id).all()
            
            for row in collections_query:
                collections_today[row.employee_id] = float(row.total_collected or 0)
            
            # 6. Organizar datos por employee_id
            result = {}
            for emp_id in employee_ids:
                result[emp_id] = {
                    'active_clients': set(),
                    'total_portfolio_value': 0,
                    'total_pending_installments': 0,
                    'balance': 0,
                    'total_overdue_installments': 0,  # Total de cuotas vencidas
                    'collected_today': collections_today.get(emp_id, 0)
                }
            
            # 7. Procesar los datos
            for row in clients_with_loans:
                emp_id = row.employee_id
                loan_id = row.loan_id
                
                # Sumar cuotas vencidas (sin excluir la primera cuota, ya que la fórmula es total)
                if loan_id in overdue_installments:
                    result[emp_id]['total_overdue_installments'] += overdue_installments[loan_id]
                
                # Solo contar si tiene primera cuota
                if loan_id in first_installments:
                    result[emp_id]['active_clients'].add(row.client_id)
                    # Calcular el valor total con intereses: amount + (amount * interest / 100)
                    loan_amount = float(row.loan_amount or 0)
                    loan_interest = float(row.loan_interest or 0)
                    total_with_interest = loan_amount + (loan_amount * loan_interest / 100)
                    result[emp_id]['total_portfolio_value'] += total_with_interest
                    result[emp_id]['total_pending_installments'] += float(first_installments[loan_id] or 0)
                    
                    # Calcular balance (cuotas pendientes + cuotas en mora + cuotas abonadas)
                    # Se incluye ABONADA porque aún tienen saldo restante por cobrar
                    if loan_id in installments_data:
                        loan_inst_data = installments_data[loan_id]
                        result[emp_id]['balance'] += loan_inst_data.get('PENDIENTE', 0)
                        result[emp_id]['balance'] += loan_inst_data.get('MORA', 0)
                        result[emp_id]['balance'] += loan_inst_data.get('ABONADA', 0)
            
            return result
        
        def get_boxes_for_manager(manager, wallet_data=None):
            if not manager:
                return []
            try:
                sellers = Salesman.query.filter_by(manager_id=manager.id).all()
                
                # Incluir la propia caja del manager (sub-administrador)
                own_seller = Salesman.query.filter_by(employee_id=manager.employee_id).first()
                if own_seller and own_seller not in sellers:
                    # Lo convertimos a lista si no lo es, para poder hacer append
                    sellers = list(sellers)
                    sellers.insert(0, own_seller)
                
                # Obtener employee_ids y pre-cargar datos si no se proporcionaron
                employee_ids = [s.employee_id for s in sellers if s.employee]
                if wallet_data is None and employee_ids:
                    wallet_data = get_wallet_data_optimized(employee_ids)
                
                boxes = []
                for seller in sellers:
                    if not seller.employee or not seller.employee.user:
                        continue
                    
                    emp_id = seller.employee.id
                    
                    # Verificar si este vendedor es administrador/coordinador (manager)
                    is_mgr = Manager.query.filter_by(employee_id=emp_id).first()
                    if is_mgr:
                        sub_emp_ids = get_all_subordinate_employee_ids(is_mgr.id)
                        active_clients = set()
                        total_overdue = 0
                        projected_value = 0
                        portfolio_value = 0
                        balance = 0
                        collected_today = 0
                        for sub_id in sub_emp_ids:
                            sub_data = wallet_data.get(sub_id, {})
                            active_clients.update(sub_data.get('active_clients', set()))
                            total_overdue += sub_data.get('total_overdue_installments', 0)
                            projected_value += sub_data.get('total_pending_installments', 0)
                            portfolio_value += sub_data.get('total_portfolio_value', 0)
                            balance += sub_data.get('balance', 0)
                            collected_today += sub_data.get('collected_today', 0)
                        
                        collection_percentage = (collected_today / projected_value * 100) if projected_value > 0 else 0
                        
                        seller_info = {
                            'Employee ID': emp_id,
                            'First Name': seller.employee.user.first_name or '',
                            'Last Name': seller.employee.user.last_name or '',
                            'Number of Active Loans': len(active_clients),
                            'Total Amount of Overdue Loans': total_overdue,
                            'Total Amount of Pending Installments': projected_value,
                            'Total Portfolio Value': portfolio_value,
                            'Balance': balance,
                            'Collection Percentage': collection_percentage,
                            'is_consolidated': True
                        }
                    else:
                        emp_data = wallet_data.get(emp_id, {})
                        projected_value = emp_data.get('total_pending_installments', 0)
                        collected_today = emp_data.get('collected_today', 0)
                        collection_percentage = (collected_today / projected_value * 100) if projected_value > 0 else 0
                        
                        seller_info = {
                            'Employee ID': emp_id,
                            'First Name': seller.employee.user.first_name or '',
                            'Last Name': seller.employee.user.last_name or '',
                            'Number of Active Loans': len(emp_data.get('active_clients', set())),
                            'Total Amount of Overdue Loans': emp_data.get('total_overdue_installments', 0),
                            'Total Amount of Pending Installments': projected_value,
                            'Total Portfolio Value': emp_data.get('total_portfolio_value', 0),
                            'Balance': emp_data.get('balance', 0),
                            'Collection Percentage': collection_percentage,
                            'is_consolidated': False
                        }
                    boxes.append(seller_info)
                return boxes
            except Exception as e:
        
                return []


        def get_only_sellers_boxes(wallet_data=None):
            """Obtiene solo las cajas de vendedores que pertenecen directamente al administrador principal y la suya propia"""
            try:
                if not main_admin:
                    return []
                all_sellers = Salesman.query.all()
                
                # Obtener employee_ids relevantes
                relevant_employee_ids = []
                for seller in all_sellers:
                    if seller.employee:
                        is_own_box = (seller.employee_id == main_admin.employee_id)
                        is_direct_subordinate = (seller.manager_id == main_admin.id)
                        
                        if is_own_box:
                            relevant_employee_ids.append(seller.employee_id)
                        elif is_direct_subordinate:
                            is_manager = Manager.query.filter_by(employee_id=seller.employee.id).first()
                            if not is_manager:
                                relevant_employee_ids.append(seller.employee_id)
                
                # Pre-cargar datos si no se proporcionaron
                if wallet_data is None and relevant_employee_ids:
                    wallet_data = get_wallet_data_optimized(relevant_employee_ids)
                
                boxes = []
                for seller in all_sellers:
                    if not seller.employee or not seller.employee.user:
                        continue
                        
                    is_own_box = (seller.employee_id == main_admin.employee_id)
                    is_direct_subordinate = (seller.manager_id == main_admin.id)
                    
                    include_seller = False
                    if is_own_box:
                        include_seller = True
                    elif is_direct_subordinate:
                        is_manager = Manager.query.filter_by(employee_id=seller.employee.id).first()
                        if not is_manager:  # Solo incluir si NO es un manager
                            include_seller = True
                            
                    if include_seller:
                        manager_name = 'Sin administrador'
                        if seller.manager and seller.manager.employee and seller.manager.employee.user:
                            manager_name = f"{seller.manager.employee.user.first_name or ''} {seller.manager.employee.user.last_name or ''}"
                            
                        emp_id = seller.employee.id
                        
                        # Verificar si este vendedor es administrador/coordinador (manager)
                        is_mgr = Manager.query.filter_by(employee_id=emp_id).first()
                        if is_mgr:
                            sub_emp_ids = get_all_subordinate_employee_ids(is_mgr.id)
                            active_clients = set()
                            total_overdue = 0
                            projected_value = 0
                            portfolio_value = 0
                            balance = 0
                            collected_today = 0
                            for sub_id in sub_emp_ids:
                                sub_data = wallet_data.get(sub_id, {})
                                active_clients.update(sub_data.get('active_clients', set()))
                                total_overdue += sub_data.get('total_overdue_installments', 0)
                                projected_value += sub_data.get('total_pending_installments', 0)
                                portfolio_value += sub_data.get('total_portfolio_value', 0)
                                balance += sub_data.get('balance', 0)
                                collected_today += sub_data.get('collected_today', 0)
                            
                            collection_percentage = (collected_today / projected_value * 100) if projected_value > 0 else 0
                            
                            seller_info = {
                                'Employee ID': emp_id,
                                'First Name': seller.employee.user.first_name or '',
                                'Last Name': seller.employee.user.last_name or '',
                                'Manager Name': manager_name,
                                'Number of Active Loans': len(active_clients),
                                'Total Amount of Overdue Loans': total_overdue,
                                'Total Amount of Pending Installments': projected_value,
                                'Total Portfolio Value': portfolio_value,
                                'Balance': balance,
                                'Collection Percentage': collection_percentage,
                                'is_consolidated': True
                            }
                        else:
                            emp_data = wallet_data.get(emp_id, {})
                            projected_value = emp_data.get('total_pending_installments', 0)
                            collected_today = emp_data.get('collected_today', 0)
                            collection_percentage = (collected_today / projected_value * 100) if projected_value > 0 else 0
                            
                            seller_info = {
                                'Employee ID': emp_id,
                                'First Name': seller.employee.user.first_name or '',
                                'Last Name': seller.employee.user.last_name or '',
                                'Manager Name': manager_name,
                                'Number of Active Loans': len(emp_data.get('active_clients', set())),
                                'Total Amount of Overdue Loans': emp_data.get('total_overdue_installments', 0),
                                'Total Amount of Pending Installments': projected_value,
                                'Total Portfolio Value': emp_data.get('total_portfolio_value', 0),
                                'Balance': emp_data.get('balance', 0),
                                'Collection Percentage': collection_percentage,
                                'is_consolidated': False
                            }
                        boxes.append(seller_info)
                return boxes
            except Exception as e:
        
                return []

        # Pre-cargar todos los datos de cartera en una sola vez (optimización)
        all_sellers = Salesman.query.all()
        all_employee_ids = [s.employee_id for s in all_sellers if s.employee]
        wallet_data_cache = get_wallet_data_optimized(all_employee_ids) if all_employee_ids else {}
        
        # Cajas del admin principal - incluir solo las cajas de vendedores (no sub-administradores)
        if main_admin:
            # Si es el administrador principal, mostrar solo las cajas de vendedores
            main_admin_boxes = get_only_sellers_boxes(wallet_data_cache)
        else:
            main_admin_boxes = []
        
        # Cajas de subadmins
        subadmins_list = []
        for subadmin in subadmins:
            if subadmin.employee and subadmin.employee.user:
                boxes = get_boxes_for_manager(subadmin, wallet_data_cache)
                # Solo agregar si tiene cajas
                if boxes:
                    subadmins_list.append({
                        'name': f"{subadmin.employee.user.first_name or ''} {subadmin.employee.user.last_name or ''}",
                        'boxes': boxes
                    })

        # Totales generales del header:
        # 1. Contar vendedores directos + sub-administradores directos
        only_sellers_boxes = get_only_sellers_boxes(wallet_data_cache)
        num_direct_sellers = len(only_sellers_boxes)
        num_direct_subadmins = len(subadmins_list)
        total_active_sellers = num_direct_sellers + num_direct_subadmins
        
        # 2. Sumar "Debido Cobrar" de todas las cajas en la jerarquía (evitando doble contabilidad de cajas consolidadas)
        if main_admin:
            sub_emp_ids = get_all_subordinate_employee_ids(main_admin.id)
            total_cash = sum([wallet_data_cache.get(emp_id, {}).get('total_pending_installments', 0) for emp_id in sub_emp_ids])
        else:
            total_cash = sum([b.get('Total Amount of Pending Installments', 0) for b in only_sellers_boxes])

        # Porcentaje de recaudación del día - Monto cobrado HOY vs Monto esperado HOY
        try:
            today = date.today()
            
            # Obtener pagos realizados el día de hoy
            payments_today = Payment.query.filter(
                func.date(Payment.payment_date) == today
            ).all()
            amount_collected_today = sum([float(p.amount or 0) for p in payments_today])
            
            # Obtener cuotas con vencimiento hoy (pendientes o en mora)
            installments_due_today = LoanInstallment.query.filter(
                func.date(LoanInstallment.due_date) == today,
                LoanInstallment.status.in_([InstallmentStatus.PENDIENTE, InstallmentStatus.MORA])
            ).all()
            amount_due_today = sum([float(i.amount or 0) for i in installments_due_today])
            
            # Calcular porcentaje de recaudación del día
            day_collection = (amount_collected_today / amount_due_today * 100) if amount_due_today > 0 else 0
            
            # Calcular el saldo de deuda total (cuotas pendientes + cuotas en mora)
            all_pending_installments = LoanInstallment.query.filter(
                LoanInstallment.status.in_([InstallmentStatus.PENDIENTE, InstallmentStatus.MORA])
            ).all()
            debt_balance = sum([float(i.amount or 0) for i in all_pending_installments])
        except Exception as e:
    
            day_collection = 0
            debt_balance = 0

        # Construir el nombre del administrador principal de forma segura
        main_admin_name = 'Sin administrador'
        if main_admin and main_admin.employee and main_admin.employee.user:
            first_name = main_admin.employee.user.first_name or ''
            last_name = main_admin.employee.user.last_name or ''
            main_admin_name = f"{first_name} {last_name}".strip()

        wallet_data = {
            'main_admin': {
                'name': main_admin_name,
                'boxes': main_admin_boxes
            },
            'subadmins': subadmins_list,
            'Total Cash Value': total_cash,  # Mantener como número para que el filtro moneda_cl funcione
            'Total Sellers with Active Loans': total_active_sellers,
            'Percentage of Day Collection': f'{day_collection:.2f}%',
            'Debt Balance': debt_balance  # Mantener como número
        }

        return render_template('wallet.html', wallet_data=wallet_data, user_id=user_id)
    except Exception as e:

        return jsonify({'message': 'Error interno del servidor', 'error': str(e)}), 500


@routes.route('/wallet-detail/<int:employee_id>', methods=['GET'])
def wallet_detail(employee_id):
    show_all = request.args.get('show_all', '0') == '1'
    search_term = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Mostrar 20 préstamos por página
    
    today = date.today()
    
    # Obtener el empleado
    employee = Employee.query.filter_by(id=employee_id).first()
    if not employee:
        return jsonify({'message': 'Empleado no encontrado'}), 404

    # Construir query base con joins para optimizar
    loans_query = db.session.query(Loan).join(
        Client, Loan.client_id == Client.id
    ).join(
        Salesman, Loan.employee_id == Salesman.employee_id
    ).join(
        Employee, Salesman.employee_id == Employee.id
    ).join(
        User, Employee.user_id == User.id
    )

    # Filtrar por empleado/ruta específico
    loans_query = loans_query.filter(Loan.employee_id == employee_id)

    # Filtrar por estado según el toggle
    if not show_all:
        loans_query = loans_query.filter(Loan.status == True)

    # Filtrar por nombre del cliente si hay búsqueda
    if search_term:
        loans_query = loans_query.filter(
            (Client.first_name.ilike(f'%{search_term}%')) |
            (Client.last_name.ilike(f'%{search_term}%'))
        )

    # Paginar los resultados
    loans_paginated = loans_query.order_by(Loan.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Inicializar variables para totales
    total_loans = 0
    total_overdue_amount = 0
    loans_detail = []

    # Procesar cada préstamo de la página actual
    for loan in loans_paginated.items:
        # Obtener el vendedor asociado al préstamo
        seller = Salesman.query.filter_by(employee_id=loan.employee_id).first()
        # Obtener el cliente asociado al préstamo
        client = Client.query.filter_by(id=loan.client_id).first()
        
        # Calcular el valor total del préstamo (suma de cuotas en PENDIENTE o MORA)
        total_loan_amount = 0
        total_overdue_amount_loan = 0
        total_overdue_installments_loan = 0
        total_paid_installments_loan = 0
        # Obtener el total de cuotas del préstamo
        total_installments_loan = len(loan.installments)
        
        has_mora = any(i.status == InstallmentStatus.MORA for i in loan.installments)
        
        for installment in loan.installments:
            total_loan_amount += float(installment.amount)
            if has_mora and (installment.status == InstallmentStatus.MORA or (installment.status == InstallmentStatus.PENDIENTE and installment.due_date < today)):
                total_overdue_amount_loan += float(installment.amount)
                total_overdue_installments_loan += 1
            elif installment.status == InstallmentStatus.PAGADA:
                total_paid_installments_loan += 1
        # Detalle de cada préstamo
        loan_info = {
            'Seller First Name': seller.employee.user.first_name if seller and seller.employee else '',
            'Seller Last Name': seller.employee.user.last_name if seller and seller.employee else '',
            'Client First Name': client.first_name if client else '',
            'Client Last Name': client.last_name if client else '',
            'Loan ID': loan.id,
            'Loan Amount': str(loan.amount),
            'Total Overdue Amount': str(total_overdue_amount_loan),
            'Overdue Installments Count': total_overdue_installments_loan,
            'Paid Installments Count': total_paid_installments_loan,
            'Total Installments': total_installments_loan
        }
        loans_detail.append(loan_info)
        # Incrementar el contador de préstamos y el valor total de préstamos pendientes o en mora
        total_loans += 1
        total_overdue_amount += total_overdue_amount_loan

    # Calcular totales de todos los préstamos (no solo la página actual)
    total_query = db.session.query(Loan).join(
        Client, Loan.client_id == Client.id
    )
    # Filtrar por empleado/ruta específico
    total_query = total_query.filter(Loan.employee_id == employee_id)
    if not show_all:
        total_query = total_query.filter(Loan.status == True)
    if search_term:
        total_query = total_query.filter(
            (Client.first_name.ilike(f'%{search_term}%')) |
            (Client.last_name.ilike(f'%{search_term}%'))
        )
    all_loans = total_query.all()
    
    # Obtener IDs de préstamos para buscar primeras cuotas
    loan_ids = [loan.id for loan in all_loans]
    first_installments = {}
    if loan_ids:
        # Subconsulta para obtener la primera cuota de cada préstamo
        subquery = db.session.query(
            LoanInstallment.loan_id,
            func.min(LoanInstallment.due_date).label('min_due_date')
        ).filter(
            LoanInstallment.loan_id.in_(loan_ids)
        ).group_by(LoanInstallment.loan_id).subquery()
        
        # Obtener las primeras cuotas
        first_inst_query = db.session.query(
            LoanInstallment.loan_id,
            LoanInstallment.fixed_amount
        ).join(
            subquery,
            and_(
                LoanInstallment.loan_id == subquery.c.loan_id,
                LoanInstallment.due_date == subquery.c.min_due_date
            )
        ).all()
        
        first_installments = {row.loan_id: row.fixed_amount for row in first_inst_query}
    
    total_all_loans = 0
    total_all_overdue = 0
    total_portfolio_value = 0  # Valor de cartera usando la misma fórmula que wallet
    for loan in all_loans:
        # Solo contar préstamos que tienen primera cuota (igual que en wallet)
        if loan.id in first_installments:
            total_all_loans += 1
            # Calcular el valor total con intereses: amount + (amount * interest / 100)
            loan_amount = float(loan.amount or 0)
            loan_interest = float(loan.interest or 0)
            total_with_interest = loan_amount + (loan_amount * loan_interest / 100)
            total_portfolio_value += total_with_interest
        
        # Calcular monto vencido
        has_mora = any(i.status == InstallmentStatus.MORA for i in loan.installments)
        if has_mora:
            for installment in loan.installments:
                if installment.status == InstallmentStatus.MORA or (installment.status == InstallmentStatus.PENDIENTE and installment.due_date < today):
                    total_all_overdue += float(installment.amount)

    # Crear un diccionario con los datos solicitados
    wallet_detail_data = {
        'Total Loans': total_all_loans,
        'Total Overdue Amount': str(int(total_all_overdue)),
        'Total Portfolio Value': str(int(total_portfolio_value)),  # Valor de cartera usando la misma fórmula que wallet
        'Loans Detail': loans_detail,
    }
    return render_template('wallet-detail.html', 
                         wallet_detail_data=wallet_detail_data, 
                         user_id=employee_id, 
                         show_all=show_all,
                         search=search_term,
                         pagination=loans_paginated)


@routes.route('/list-expenses')
def list_expenses():
    try:
        # Obtener el user_id de la sesión
        user_id = session.get('user_id')
        user_role = session.get('role')

        if user_id is None:
            return jsonify({'message': 'Usuario no encontrado en la sesión'}), 401

        # Buscar al empleado correspondiente al user_id de la sesión
        empleado = Employee.query.filter_by(user_id=user_id).first()

        if not empleado:
            return jsonify({'message': 'Empleado no encontrado'}), 404

        # OPTIMIZACIÓN: Una sola consulta con JOIN para obtener transacciones y conceptos
        # Agregar paginación para mejorar el rendimiento
        page = request.args.get('page', 1, type=int)
        per_page = 20  # Mostrar 20 transacciones por página
        
        transacciones_con_conceptos = db.session.query(Transaction, Concept).outerjoin(
            Concept, Transaction.concept_id == Concept.id
        ).filter(
            Transaction.employee_id == empleado.id,
            ~Transaction.description.like('[ELIMINADA]%')
        ).order_by(Transaction.creation_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        # Crear una lista para almacenar los detalles de las transacciones
        detalles_transacciones = []

        for transaccion, concepto in transacciones_con_conceptos.items:
            # Crear un diccionario con los detalles de la transacción
            detalle_transaccion = {
                'id': transaccion.id,
                'tipo': transaccion.transaction_types.name if transaccion.transaction_types else 'N/A',
                'concepto': concepto.name if concepto else 'N/A',
                'descripcion': transaccion.description or 'Sin descripción',
                'monto': transaccion.amount,
                'attachment': transaccion.attachment or None,
                'status': transaccion.approval_status.value if transaccion.approval_status else 'N/A',
                'fecha': transaccion.creation_date.strftime('%d/%m/%Y %H:%M') if transaccion.creation_date else 'N/A'
            }

            # Agregar los detalles a la lista
            detalles_transacciones.append(detalle_transaccion)

        return render_template('list-expenses.html', 
                             detalles_transacciones=detalles_transacciones, 
                             user_role=user_role, 
                             user_id=user_id,
                             pagination=transacciones_con_conceptos)

    except Exception as e:
        return jsonify({'message': 'Error interno del servidor', 'error': str(e)}), 500



@routes.route('/reports', methods=['GET'])
def reports():
    # Obtener el user_id del usuario desde la sesión
    user_id = session.get('user_id')
    try:
        # Buscar el manager_id asociado al user_id en la tabla Salesman
        salesman = Salesman.query.filter_by(employee_id=user_id).first()
        if not salesman:
            return {"error": "No se encontró el vendedor asociado al usuario"}, 404

        manager_id = salesman.manager_id

        
        # Obtener parámetros de la solicitud
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        salesman_id = request.args.get('salesman_id')

        # Si no se han seleccionado fechas, mostrar solo el formulario
        if not start_date or not end_date:
            salesmen = db.session.query(Employee.id, User.first_name + ' ' + User.last_name).join(User, User.id == Employee.user_id).join(Salesman, Salesman.employee_id == Employee.id).filter(Salesman.manager_id == manager_id).all()
            return render_template("reports.html", salesmen=salesmen, report_data=None, user_id=user_id)
        
        # Validar fechas
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        # Obtener todos los vendedores asociados al coordinador
        salesmen = Salesman.query.filter_by(manager_id=manager_id).all()
        if salesman_id:
            salesmen = [s for s in salesmen if s.employee_id == int(salesman_id)]

        report_data = []
        current_date = start_date
        while current_date <= end_date:
            for salesman in salesmen:
                # Obtener el empleado
                employee = Employee.query.get(salesman.employee_id)
                
                # Obtener el valor inicial de la caja
                employee_record = EmployeeRecord.query.filter(
                    EmployeeRecord.employee_id == salesman.employee_id,
                    func.date(EmployeeRecord.creation_date) == current_date
                ).order_by(EmployeeRecord.id.desc()).first()
                
                initial_box_value = float(employee_record.closing_total) if employee_record else 0.0

                # Obtener gastos del día
                daily_expenses = float(Transaction.query.filter(
                    Transaction.employee_id == salesman.employee_id,
                    Transaction.transaction_types == TransactionType.GASTO,
                    Transaction.approval_status == ApprovalStatus.APROBADA,
                    func.date(Transaction.creation_date) == current_date
                ).with_entities(func.sum(Transaction.amount)).scalar() or 0)

                # Obtener ingresos del día
                daily_incomes = float(Transaction.query.filter(
                    Transaction.employee_id == salesman.employee_id,
                    Transaction.transaction_types == TransactionType.INGRESO,
                    Transaction.approval_status == ApprovalStatus.APROBADA,
                    func.date(Transaction.creation_date) == current_date
                ).with_entities(func.sum(Transaction.amount)).scalar() or 0)

                # Obtener retiros del día
                daily_withdrawals = float(Transaction.query.filter(
                    Transaction.employee_id == salesman.employee_id,
                    Transaction.transaction_types == TransactionType.RETIRO,
                    Transaction.approval_status == ApprovalStatus.APROBADA,
                    func.date(Transaction.creation_date) == current_date
                ).with_entities(func.sum(Transaction.amount)).scalar() or 0)

                # Obtener ventas del día (préstamos nuevos)
                daily_sales = float(Loan.query.filter(
                    Loan.client.has(employee_id=salesman.employee_id),
                    Loan.is_renewal == False,
                    Loan.status == True,  # Solo préstamos activos
                    func.date(Loan.creation_date) == current_date
                ).with_entities(func.sum(Loan.amount)).scalar() or 0)

                # Obtener renovaciones del día
                daily_renewals = float(Loan.query.filter(
                    Loan.client.has(employee_id=salesman.employee_id),
                    Loan.is_renewal == True,
                    func.date(Loan.creation_date) == current_date
                ).with_entities(func.sum(Loan.amount)).scalar() or 0)

                # Obtener número de no pagos del día
                no_payments = db.session.query(func.count(LoanInstallment.id)).join(
                    Loan, Loan.id == LoanInstallment.loan_id
                ).join(
                    Client, Client.id == Loan.client_id
                ).filter(
                    Client.employee_id == salesman.employee_id,
                    LoanInstallment.status == InstallmentStatus.MORA,
                    func.date(LoanInstallment.due_date) == current_date
                ).scalar() or 0

                # Obtener recaudo del día
                daily_collections = float(Payment.query.join(
                    LoanInstallment, LoanInstallment.id == Payment.installment_id
                ).join(
                    Loan, Loan.id == LoanInstallment.loan_id
                ).join(
                    Client, Client.id == Loan.client_id
                ).filter(
                    Client.employee_id == salesman.employee_id,
                    func.date(Payment.payment_date) == current_date
                ).with_entities(func.sum(Payment.amount)).scalar() or 0)

                # Obtener saldo por cobrar
                due_to_collect = float(db.session.query(func.sum(LoanInstallment.amount)).join(
                    Loan, Loan.id == LoanInstallment.loan_id
                ).join(
                    Client, Client.id == Loan.client_id
                ).filter(
                    Client.employee_id == salesman.employee_id,
                    LoanInstallment.status.in_([InstallmentStatus.PENDIENTE, InstallmentStatus.MORA]),
                    func.date(LoanInstallment.due_date) <= current_date
                ).scalar() or 0)

                # Calcular caja final
                final_box_value = initial_box_value + daily_incomes - daily_expenses - daily_withdrawals - daily_sales - daily_renewals

                report_data.append({
                    'ruta': f"{employee.user.first_name} {employee.user.last_name}",
                    'fecha': current_date.strftime('%Y-%m-%d'),
                    'gasto': f"$ {daily_expenses:,.0f}",
                    'ingreso': f"$ {daily_incomes:,.0f}",
                    'retiro': f"$ {daily_withdrawals:,.0f}",
                    'ventas': f"$ {daily_sales:,.0f}",
                    'renovaciones': f"$ {daily_renewals:,.0f}",
                    'no_pago': no_payments,
                    'recaudo': f"$ {daily_collections:,.0f}",
                    'debido_cobrar': f"$ {due_to_collect:,.0f}",
                    'caja_inicial': f"$ {initial_box_value:,.0f}",
                    'caja_final': f"$ {final_box_value:,.0f}"
                })

            current_date += timedelta(days=1)

        # Obtener lista de vendedores para el selector
        salesmen = db.session.query(Employee.id, User.first_name + ' ' + User.last_name).join(User, User.id == Employee.user_id).join(Salesman, Salesman.employee_id == Employee.id).filter(Salesman.manager_id == manager_id).all()

        return render_template("reports.html", report_data=report_data, salesmen=salesmen, user_id=user_id)

    except Exception as e:
        return render_template("reports.html", user_id=user_id)



@routes.route('/reports/download', methods=['GET'])
def download_report():
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        salesman_id = request.args.get('salesman_id')

        if not start_date or not end_date:
            return {"error": "Debe proporcionar un rango de fechas"}, 400

        # Convertir las fechas
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        # Obtener el user_id de la sesión
        user_id = session.get('user_id')
        if not user_id:
            return {"error": "Usuario no autenticado"}, 401

        # Buscar el manager_id asociado al user_id en la tabla Salesman
        salesman = Salesman.query.filter_by(employee_id=user_id).first()
        if not salesman:
            return {"error": "No se encontró el vendedor asociado al usuario"}, 404

        manager_id = salesman.manager_id

        # Obtener todos los vendedores asociados al coordinador
        salesmen = Salesman.query.filter_by(manager_id=manager_id).all()
        if salesman_id:
            salesmen = [s for s in salesmen if s.employee_id == int(salesman_id)]

        report_data = []
        current_date = start_date
        while current_date <= end_date:
            for salesman in salesmen:
                # Obtener el empleado
                employee = Employee.query.get(salesman.employee_id)
                
                # Obtener el valor inicial de la caja
                employee_record = EmployeeRecord.query.filter(
                    EmployeeRecord.employee_id == salesman.employee_id,
                    func.date(EmployeeRecord.creation_date) == current_date
                ).order_by(EmployeeRecord.id.desc()).first()
                
                initial_box_value = float(employee_record.closing_total) if employee_record else 0.0

                # Obtener gastos del día
                daily_expenses = float(Transaction.query.filter(
                    Transaction.employee_id == salesman.employee_id,
                    Transaction.transaction_types == TransactionType.GASTO,
                    Transaction.approval_status == ApprovalStatus.APROBADA,
                    func.date(Transaction.creation_date) == current_date
                ).with_entities(func.sum(Transaction.amount)).scalar() or 0)

                # Obtener ingresos del día
                daily_incomes = float(Transaction.query.filter(
                    Transaction.employee_id == salesman.employee_id,
                    Transaction.transaction_types == TransactionType.INGRESO,
                    Transaction.approval_status == ApprovalStatus.APROBADA,
                    func.date(Transaction.creation_date) == current_date
                ).with_entities(func.sum(Transaction.amount)).scalar() or 0)

                # Obtener retiros del día
                daily_withdrawals = float(Transaction.query.filter(
                    Transaction.employee_id == salesman.employee_id,
                    Transaction.transaction_types == TransactionType.RETIRO,
                    Transaction.approval_status == ApprovalStatus.APROBADA,
                    func.date(Transaction.creation_date) == current_date
                ).with_entities(func.sum(Transaction.amount)).scalar() or 0)

                # Obtener ventas del día (préstamos nuevos)
                daily_sales = float(Loan.query.filter(
                    Loan.client.has(employee_id=salesman.employee_id),
                    Loan.is_renewal == False,
                    Loan.status == True,  # Solo préstamos activos
                    func.date(Loan.creation_date) == current_date
                ).with_entities(func.sum(Loan.amount)).scalar() or 0)

                # Obtener renovaciones del día
                daily_renewals = float(Loan.query.filter(
                    Loan.client.has(employee_id=salesman.employee_id),
                    Loan.is_renewal == True,
                    func.date(Loan.creation_date) == current_date
                ).with_entities(func.sum(Loan.amount)).scalar() or 0)

                # Obtener número de no pagos del día
                no_payments = db.session.query(func.count(LoanInstallment.id)).join(
                    Loan, Loan.id == LoanInstallment.loan_id
                ).join(
                    Client, Client.id == Loan.client_id
                ).filter(
                    Client.employee_id == salesman.employee_id,
                    LoanInstallment.status == InstallmentStatus.MORA,
                    func.date(LoanInstallment.due_date) == current_date
                ).scalar() or 0

                # Obtener recaudo del día
                daily_collections = float(Payment.query.join(
                    LoanInstallment, LoanInstallment.id == Payment.installment_id
                ).join(
                    Loan, Loan.id == LoanInstallment.loan_id
                ).join(
                    Client, Client.id == Loan.client_id
                ).filter(
                    Client.employee_id == salesman.employee_id,
                    func.date(Payment.payment_date) == current_date
                ).with_entities(func.sum(Payment.amount)).scalar() or 0)

                # Obtener saldo por cobrar
                due_to_collect = db.session.query(func.sum(LoanInstallment.amount)).join(
                    Loan, Loan.id == LoanInstallment.loan_id
                ).join(
                    Client, Client.id == Loan.client_id
                ).filter(
                    Client.employee_id == salesman.employee_id,
                    LoanInstallment.status.in_([InstallmentStatus.PENDIENTE, InstallmentStatus.MORA]),
                    func.date(LoanInstallment.due_date) <= current_date
                ).scalar() or 0

                # Calcular caja final
                final_box_value = initial_box_value + daily_incomes - daily_expenses - daily_withdrawals - daily_sales - daily_renewals

                report_data.append({
                    'Ruta': f"{employee.user.first_name} {employee.user.last_name}",
                    'Fecha': current_date.strftime('%Y-%m-%d'),
                    'Gasto': daily_expenses,
                    'Ingreso': daily_incomes,
                    'Retiro': daily_withdrawals,
                    'Ventas': daily_sales,
                    'Renovaciones': daily_renewals,
                    '# No pago': no_payments,
                    'Recaudo': daily_collections,
                    'Debido Cobrar': due_to_collect,
                    'Caja Inicial': initial_box_value,
                    'Caja Final': final_box_value
                })

            current_date += timedelta(days=1)

        if not report_data:
            return {"error": "No hay datos para exportar"}, 404

        # Convertir datos a un DataFrame de Pandas
        df = pd.DataFrame(report_data)

        # Crear un archivo Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Reporte")
            
            # Obtener el libro y la hoja de trabajo
            workbook = writer.book
            worksheet = writer.sheets['Reporte']
            
            # Formato para números con separador de miles y símbolo de moneda
            money_format = workbook.add_format({'num_format': '$#,##0'})
            
            # Aplicar el formato a las columnas monetarias
            for col in ['Gasto', 'Ingreso', 'Retiro', 'Ventas', 'Renovaciones', 'Recaudo', 'Debido Cobrar', 'Caja Inicial', 'Caja Final']:
                col_idx = df.columns.get_loc(col)
                worksheet.set_column(col_idx, col_idx, None, money_format)
        
        output.seek(0)

        # Enviar el archivo como respuesta
        return send_file(output, download_name="reporte.xlsx", as_attachment=True, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    except Exception as e:
        return {"error": str(e)}, 500

