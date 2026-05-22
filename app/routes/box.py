# app/routes/box.py
# Vista de caja actual (coordinador y vendedor)

# Importaciones estándar
from datetime import datetime, date, timedelta
from decimal import Decimal
import os
import uuid
import holidays
import io

# Importaciones de SQLAlchemy
from sqlalchemy import func, case, join, tuple_, and_
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

@routes.route('/box', methods=['GET'])
def box():
    try:
        # Validar acceso del coordinador
        user_id, user = validate_coordinator_access()
        
        # Obtener datos del coordinador y sus vendedores
        coordinator, coordinator_cash, coordinator_name, manager_id, salesmen = get_coordinator_data(user_id)
        
        current_date = datetime.now().date()
        
        # Calcular totales de transacciones del coordinador (excluyendo subcoordinadores)
        salesman_incomes, salesman_withdrawals, coordinator_incomes, coordinator_withdrawals = calculate_daily_transaction_totals(manager_id, current_date, coordinator.id)
        
        # Inicializar lista para estadísticas de vendedores
        salesmen_stats = []
        
        # OPTIMIZACIÓN: Obtener todos los datos de vendedores en consultas optimizadas
        salesmen_data = get_all_salesmen_data_optimized(salesmen, current_date)
        
        # OPTIMIZACIÓN: Obtener datos adicionales en una sola consulta para todos los vendedores
        employee_ids = [salesman[0].employee_id for salesman in salesmen]
        additional_data = get_all_salesmen_additional_data_optimized(employee_ids, current_date)
        
        
        # Procesar cada vendedor con datos pre-cargados
        for salesman, employee, user in salesmen:
            employee_id = salesman.employee_id
            data = salesmen_data[employee_id]
            additional = additional_data[employee_id]
            
            # Actualizar datos con información adicional optimizada
            data.update(additional)
            
            # Verificar si es un subcoordinador (Manager)
            is_subcoordinator = Manager.query.filter_by(employee_id=employee_id).first()
            
            # Inicializar variables para valores de coordinador
            daily_withdrawals = data['daily_withdrawals']
            daily_withdrawals_count = data['daily_withdrawals_count']
            daily_collections_made = data['daily_collection']
            daily_collection_count = data['daily_collection_count']
            daily_expenses_amount = data['daily_expenses_amount']
            daily_expenses_count = data['daily_expenses_count']
            
            if is_subcoordinator:
                # Es un subcoordinador: usar fórmula de coordinador
                subcoord_manager_id = db.session.query(Manager.id).filter_by(employee_id=employee_id).scalar()
                if subcoord_manager_id:
                    # Calcular totales de transacciones del subcoordinador (excluyendo subcoordinadores de nivel inferior)
                    subcoord_salesman_incomes, subcoord_salesman_withdrawals, subcoord_incomes, subcoord_withdrawals = calculate_daily_transaction_totals(subcoord_manager_id, current_date, employee_id)
                    # Obtener gastos del subcoordinador
                    subcoord_expenses, subcoord_expense_details = get_coordinator_expenses(employee_id, current_date)
                    
                    # Calcular valores para mostrar en la card (suma de todos los movimientos)
                    daily_withdrawals = float(subcoord_salesman_incomes + subcoord_withdrawals)  # Ingresos de vendedores + retiros del subcoordinador
                    daily_collections_made = float(subcoord_salesman_withdrawals + subcoord_incomes)  # Retiros de vendedores + ingresos del subcoordinador
                    daily_expenses_amount = float(subcoord_expenses)
                    
                    # Contar transacciones para mostrar en la card
                    start_of_day = datetime.combine(current_date, datetime.min.time())
                    end_of_day = datetime.combine(current_date, datetime.max.time())
                    
                    # Contar retiros (transacciones INGRESO de subordinados)
                    daily_withdrawals_count = db.session.query(
                        func.count(Transaction.id)
                    ).join(Salesman, Transaction.employee_id == Salesman.employee_id).filter(
                        Transaction.transaction_types == 'INGRESO',
                        Transaction.approval_status == 'APROBADA',
                        Salesman.manager_id == subcoord_manager_id,
                        Transaction.creation_date.between(start_of_day, end_of_day)
                    ).scalar() or 0
                    
                    # Contar ingresos (transacciones RETIRO de subordinados)
                    daily_collection_count = db.session.query(
                        func.count(Transaction.id)
                    ).join(Salesman, Transaction.employee_id == Salesman.employee_id).filter(
                        Transaction.transaction_types == 'RETIRO',
                        Transaction.approval_status == 'APROBADA',
                        Salesman.manager_id == subcoord_manager_id,
                        func.date(Transaction.creation_date) == current_date
                    ).scalar() or 0
                    
                    # Contar gastos
                    daily_expenses_count = len(subcoord_expense_details)
                    
                    # Obtener valor inicial de caja (del último registro del día anterior o box_value actual)
                    initial_box_value = data.get('initial_box_value', 0)
                    if initial_box_value == 0:
                        # Si no hay registro previo, usar box_value actual
                        initial_box_value = float(employee.box_value)
                    
                    # Calcular valor de caja usando fórmula de coordinador
                    # Valor inicial - ingresos vendedores + retiros vendedores - gastos + ingresos coordinador - retiros coordinador
                    box_value = float(initial_box_value) \
                               - float(subcoord_salesman_incomes) \
                               + float(subcoord_salesman_withdrawals) \
                               - float(subcoord_expenses) \
                               + float(subcoord_incomes) \
                               - float(subcoord_withdrawals)
                else:
                    # Si no se encuentra manager_id, usar fórmula de vendedor como fallback
                    box_value = calculate_box_value(
                        data['initial_box_value'], data['total_collections_today'], 
                        data['daily_withdrawals'], data['daily_expenses_amount'],
                        data['daily_collection'], data['new_clients_loan_amount'],
                        data['total_renewal_loans_amount'], data['existing_record_today']
                    )
            else:
                # Es un vendedor regular: usar fórmula de vendedor
                box_value = calculate_box_value(
                    data['initial_box_value'], data['total_collections_today'], 
                    data['daily_withdrawals'], data['daily_expenses_amount'],
                    data['daily_collection'], data['new_clients_loan_amount'],
                    data['total_renewal_loans_amount'], data['existing_record_today']
                )
            
            # Determinar estado de la caja
            if data['employee_status'] == False and data['all_loans_paid_today'] == True:
                status_box = "Cerrada"
            elif data['employee_status'] == False and data['all_loans_paid_today'] == False:
                status_box = "Desactivada"
            elif data['employee_status'] == True and data['all_loans_paid_today'] == False:
                status_box = "Activa"
            else:
                status_box = "Activa"
            
            # Crear datos del vendedor
            salesman_data = {
                'salesman_name': data['salesman_name'],
                'username': user.username,
                'employee_id': employee_id,
                'employee_status': data['employee_status'],
                'total_collections_today': data['total_collections_today'],
                'new_clients': data['new_clients'],
                'daily_expenses': daily_expenses_count,
                'daily_expenses_amount': daily_expenses_amount,
                'daily_withdrawals': daily_withdrawals,
                'daily_collections_made': daily_collections_made,
                'total_number_of_customers': data['total_customers'],
                'customers_in_arrears_for_the_day': data['customers_in_arrears'],
                'total_renewal_loans': data['total_renewal_loans'],
                'total_new_clients_loan_amount': data['new_clients_loan_amount'],
                'total_renewal_loans_amount': data['total_renewal_loans_amount'],
                'daily_withdrawals_count': daily_withdrawals_count,
                'daily_collection_count': daily_collection_count,
                'total_pending_installments_amount': data['total_pending_installments_amount'],
                'all_loans_paid_today': data['all_loans_paid_today'],
                'total_clients_collected': data['total_clients_collected'],
                'status_box': status_box,
                'box_value': box_value,
                'initial_box_value': data['initial_box_value'],
                'expense_details': data['expense_details'],
                'income_details': data['income_details'],
                'withdrawal_details': data['withdrawal_details'],
                'role_employee': data['role_employee'],
                'total_pending_installments_loan_close_amount': data['total_pending_installments_loan_close_amount']
            }
            
            salesmen_stats.append(salesman_data)
        
        # Procesar búsqueda
        search_term = request.args.get('salesman_name', '')
        if search_term:
            salesmen_stats = [salesman for salesman in salesmen_stats if
                              search_term.lower() in salesman['salesman_name'].lower()]
        
        # Verificar si todas las cajas están cerradas
        all_boxes_closed = all(
            salesman_data['status_box'] == 'Cerrada' for salesman_data in salesmen_stats)
        
        # Obtener gastos del coordinador
        total_expenses, coordinator_expense_details = get_coordinator_expenses(coordinator.id, current_date)
        
        # Calcular valor final de la caja del coordinador según las reglas de negocio:
        # Valor inicial - ingresos vendedores + retiros vendedores - gastos coordinador + ingresos coordinador - retiros coordinador
        final_box_value = float(coordinator_cash) \
                         - float(salesman_incomes) \
                         + float(salesman_withdrawals) \
                         - float(total_expenses) \
                         + float(coordinator_incomes) \
                         - float(coordinator_withdrawals)
        
        # Crear datos de la caja del coordinador
        coordinator_box = {
            'maximum_cash': float(coordinator_cash),
            'total_outbound_amount': float(salesman_incomes + coordinator_withdrawals),  # Para compatibilidad con template
            'total_inbound_amount': float(salesman_withdrawals + coordinator_incomes),  # Para compatibilidad con template
            'final_box_value': final_box_value,
        }
        
        # Renderizar la plantilla
        return render_template('box.html', 
                             coordinator_box=coordinator_box, 
                             salesmen_stats=salesmen_stats,
                             search_term=search_term, 
                             all_boxes_closed=all_boxes_closed,
                             coordinator_name=coordinator_name, 
                             coordinator_id=coordinator.id,
                             user_id=user_id, 
                             expense_details=coordinator_expense_details, 
                             total_expenses=total_expenses,
                             redirect_url='/box')
                             
    except ValueError as e:
        return jsonify({'message': str(e)}), 401 if 'Usuario no encontrado' in str(e) else 403
    except Exception as e:
        return jsonify({'message': 'Error interno del servidor', 'error': str(e)}), 500



@routes.route('/box-detail-admin/<int:employee_id>', methods=['GET'])
def box_detail_admin(employee_id):
    try:
        # Obtener el user_id de la sesión
        user_id = session.get('user_id')

        if user_id is None:
            return jsonify({'message': 'Usuario no encontrado en la sesión'}), 401

        # Verificar si el usuario es un coordinador
        user = User.query.get(user_id)
        if user is None or user.role != Role.COORDINADOR:
            return jsonify({'message': 'El usuario no es un coordinador válido'}), 403

        # Obtener el empleado sub-administrador por su ID
        sub_admin_employee = Employee.query.get(employee_id)
        if not sub_admin_employee:
            return jsonify({'message': 'Empleado sub-administrador no encontrado'}), 404

        # Obtener el usuario del sub-administrador
        sub_admin_user = User.query.get(sub_admin_employee.user_id)
        if not sub_admin_user:
            return jsonify({'message': 'Usuario del sub-administrador no encontrado'}), 404

        # Obtener la fecha actual
        current_date = datetime.now().date()

        # Obtener la información de la caja del sub-administrador
        # Obtener el valor inicial del último registro del día anterior, o usar box_value si no hay registro
        last_record = EmployeeRecord.query.filter_by(employee_id=sub_admin_employee.id) \
            .filter(func.date(EmployeeRecord.creation_date) < current_date) \
            .order_by(EmployeeRecord.creation_date.desc()).first()
        
        if last_record:
            sub_admin_cash = float(last_record.closing_total)
        else:
            sub_admin_cash = sub_admin_employee.box_value
        
        sub_admin_name = f"{sub_admin_user.first_name} {sub_admin_user.last_name}"

        # Obtener el ID del manager del sub-administrador
        manager_id = db.session.query(Manager.id).filter_by(
            employee_id=sub_admin_employee.id).scalar()

        if not manager_id:
            return jsonify({'message': 'No se encontró ningún manager asociado a este empleado'}), 404

        # OPTIMIZACIÓN: Cargar vendedores con sus relaciones en una sola consulta (JOIN)
        salesmen = db.session.query(Salesman, Employee, User).join(
            Employee, Salesman.employee_id == Employee.id
        ).join(
            User, Employee.user_id == User.id
        ).filter(Salesman.manager_id == manager_id).all()

        # Calcular totales de transacciones del sub-administrador (excluyendo subcoordinadores)
        salesman_incomes, salesman_withdrawals, coordinator_incomes, coordinator_withdrawals = calculate_daily_transaction_totals(manager_id, current_date, sub_admin_employee.id)

        # OPTIMIZACIÓN: Obtener todos los datos de vendedores en consultas batch
        salesmen_data = get_all_salesmen_data_optimized(salesmen, current_date)

        # OPTIMIZACIÓN: Obtener datos adicionales en una sola consulta para todos los vendedores
        employee_ids_list = [salesman[0].employee_id for salesman in salesmen]
        additional_data = get_all_salesmen_additional_data_optimized(employee_ids_list, current_date)

        # Inicializa la lista para almacenar las estadísticas de los vendedores
        salesmen_stats = []

        # Procesar cada vendedor con datos pre-cargados
        for salesman, employee, user in salesmen:
            emp_id = salesman.employee_id
            data = salesmen_data[emp_id]
            additional = additional_data[emp_id]

            # Actualizar datos con información adicional optimizada
            data.update(additional)

            # Verificar si es un subcoordinador (Manager)
            is_subcoordinator = Manager.query.filter_by(employee_id=emp_id).first()

            # Inicializar variables para valores de coordinador
            daily_withdrawals = data['daily_withdrawals']
            daily_withdrawals_count = data['daily_withdrawals_count']
            daily_collections_made = data['daily_collection']
            daily_collection_count = data['daily_collection_count']
            daily_expenses_amount = data['daily_expenses_amount']
            daily_expenses_count = data['daily_expenses_count']

            if is_subcoordinator:
                # Es un subcoordinador: usar fórmula de coordinador
                subcoord_manager_id = db.session.query(Manager.id).filter_by(employee_id=emp_id).scalar()
                if subcoord_manager_id:
                    # Calcular totales de transacciones del subcoordinador (excluyendo subcoordinadores de nivel inferior)
                    subcoord_salesman_incomes, subcoord_salesman_withdrawals, subcoord_incomes, subcoord_withdrawals = calculate_daily_transaction_totals(subcoord_manager_id, current_date, emp_id)
                    # Obtener gastos del subcoordinador
                    subcoord_expenses, subcoord_expense_details = get_coordinator_expenses(emp_id, current_date)

                    # Calcular valores para mostrar en la card (suma de todos los movimientos)
                    daily_withdrawals = float(subcoord_salesman_incomes + subcoord_withdrawals)
                    daily_collections_made = float(subcoord_salesman_withdrawals + subcoord_incomes)
                    daily_expenses_amount = float(subcoord_expenses)

                    # Contar transacciones para mostrar en la card
                    start_of_day = datetime.combine(current_date, datetime.min.time())
                    end_of_day = datetime.combine(current_date, datetime.max.time())

                    # Contar retiros (transacciones INGRESO de subordinados)
                    daily_withdrawals_count = db.session.query(
                        func.count(Transaction.id)
                    ).join(Salesman, Transaction.employee_id == Salesman.employee_id).filter(
                        Transaction.transaction_types == 'INGRESO',
                        Transaction.approval_status == 'APROBADA',
                        Salesman.manager_id == subcoord_manager_id,
                        Transaction.creation_date.between(start_of_day, end_of_day)
                    ).scalar() or 0

                    # Contar ingresos (transacciones RETIRO de subordinados)
                    daily_collection_count = db.session.query(
                        func.count(Transaction.id)
                    ).join(Salesman, Transaction.employee_id == Salesman.employee_id).filter(
                        Transaction.transaction_types == 'RETIRO',
                        Transaction.approval_status == 'APROBADA',
                        Salesman.manager_id == subcoord_manager_id,
                        func.date(Transaction.creation_date) == current_date
                    ).scalar() or 0

                    # Contar gastos
                    daily_expenses_count = len(subcoord_expense_details)

                    # Obtener valor inicial de caja (del último registro del día anterior o box_value actual)
                    initial_box_value = data.get('initial_box_value', 0)
                    if initial_box_value == 0:
                        initial_box_value = float(employee.box_value)

                    # Calcular valor de caja usando fórmula de coordinador
                    box_value = float(initial_box_value) \
                               - float(subcoord_salesman_incomes) \
                               + float(subcoord_salesman_withdrawals) \
                               - float(subcoord_expenses) \
                               + float(subcoord_incomes) \
                               - float(subcoord_withdrawals)
                else:
                    box_value = calculate_box_value(
                        data['initial_box_value'], data['total_collections_today'],
                        data['daily_withdrawals'], data['daily_expenses_amount'],
                        data['daily_collection'], data['new_clients_loan_amount'],
                        data['total_renewal_loans_amount'], data['existing_record_today']
                    )
            else:
                # Es un vendedor regular: usar fórmula de vendedor
                box_value = calculate_box_value(
                    data['initial_box_value'], data['total_collections_today'],
                    data['daily_withdrawals'], data['daily_expenses_amount'],
                    data['daily_collection'], data['new_clients_loan_amount'],
                    data['total_renewal_loans_amount'], data['existing_record_today']
                )

            # Determinar estado de la caja
            if data['employee_status'] == False and data['all_loans_paid_today'] == True:
                status_box = "Cerrada"
            elif data['employee_status'] == False and data['all_loans_paid_today'] == False:
                status_box = "Desactivada"
            elif data['employee_status'] == True and data['all_loans_paid_today'] == False:
                status_box = "Activa"
            else:
                status_box = "Activa"

            # Crear datos del vendedor
            salesman_data = {
                'salesman_name': data['salesman_name'],
                'username': user.username,
                'employee_id': emp_id,
                'employee_status': data['employee_status'],
                'total_collections_today': data['total_collections_today'],
                'new_clients': data['new_clients'],
                'daily_expenses': daily_expenses_count,
                'daily_expenses_amount': daily_expenses_amount,
                'daily_withdrawals': daily_withdrawals,
                'daily_collections_made': daily_collections_made,
                'total_number_of_customers': data['total_customers'],
                'customers_in_arrears_for_the_day': data['customers_in_arrears'],
                'total_renewal_loans': data['total_renewal_loans'],
                'total_new_clients_loan_amount': data['new_clients_loan_amount'],
                'total_renewal_loans_amount': data['total_renewal_loans_amount'],
                'daily_withdrawals_count': daily_withdrawals_count,
                'daily_collection_count': daily_collection_count,
                'total_pending_installments_amount': data['total_pending_installments_amount'],
                'all_loans_paid_today': data['all_loans_paid_today'],
                'total_clients_collected': data['total_clients_collected'],
                'status_box': status_box,
                'box_value': box_value,
                'initial_box_value': data['initial_box_value'],
                'expense_details': data['expense_details'],
                'income_details': data['income_details'],
                'withdrawal_details': data['withdrawal_details'],
                'role_employee': data['role_employee'],
                'total_pending_installments_loan_close_amount': data['total_pending_installments_loan_close_amount']
            }

            salesmen_stats.append(salesman_data)

        # Procesar búsqueda
        search_term = request.args.get('salesman_name', '')
        if search_term:
            salesmen_stats = [salesman for salesman in salesmen_stats if
                              search_term.lower() in salesman['salesman_name'].lower()]

        # Verificar si todas las cajas están cerradas
        all_boxes_closed = all(
            salesman_data['status_box'] == 'Cerrada' for salesman_data in salesmen_stats)

        # Obtener gastos del sub-administrador usando función optimizada
        total_expenses, expense_details = get_coordinator_expenses(sub_admin_employee.id, current_date)

        # Calcular valor final de la caja del sub-administrador según las reglas de negocio
        final_box_value = float(sub_admin_cash) \
                         - float(salesman_incomes) \
                         + float(salesman_withdrawals) \
                         - float(total_expenses) \
                         + float(coordinator_incomes) \
                         - float(coordinator_withdrawals)

        sub_admin_box = {
            'maximum_cash': float(sub_admin_cash),
            'total_outbound_amount': float(salesman_incomes + coordinator_withdrawals),  # Para compatibilidad con template
            'total_inbound_amount': float(salesman_withdrawals + coordinator_incomes),  # Para compatibilidad con template
            'final_box_value': final_box_value,
        }

        # Renderizar la plantilla con las variables
        return render_template('box.html', coordinator_box=sub_admin_box, salesmen_stats=salesmen_stats,
                               search_term=search_term, all_boxes_closed=all_boxes_closed,
                               coordinator_name=sub_admin_name, user_id=user_id, expense_details=expense_details, 
                               total_expenses=total_expenses, manager_id=manager_id,
                               redirect_url='/box-detail-admin/' + str(employee_id))
    except Exception as e:
        return jsonify({'message': 'Error interno del servidor', 'error': str(e)}), 500



@routes.route('/create-box')
def create_box():
    return render_template('create-box.html')



@routes.route('/box-archive')
def box_archive():
    return render_template('box-archive.html')



@routes.route('/box-detail', methods=['GET'])
def box_detail():
    user_role = session.get('role')
    user_id = session.get('user_id')

    # Obtener el employee_id del vendedor desde la solicitud
    employee_id = request.args.get('employee_id')

    # Verificar si el employee_id existe en la base de datos
    employee = Employee.query.get(employee_id)
    if not employee:
        return jsonify({'error': 'Empleado no encontrado'}), 404

    # Obtener todos los préstamos asociados a ese vendedor
    loans = Loan.query.filter_by(employee_id=employee_id).all()

    # Recopilar detalles de los préstamos
    loan_details = []
    renewal_loan_details = []  # Detalles de los préstamos que son renovaciones activas

    for loan in loans:
        loan_date = loan.creation_date.date() # Obtener solo la fecha del préstamo
        if loan_date == datetime.today().date() and loan.is_renewal == 0 and loan.status:  # Verificar si el préstamo se realizó hoy y está activo
            loan_detail = {
                'client_name': loan.client.first_name + ' ' + loan.client.last_name,
                'loan_amount': loan.amount,
                'loan_dues': loan.dues,
                'loan_interest': loan.interest,
                # Agregar la fecha del préstamo
                'loan_date': loan_date.strftime('%d/%m/%Y'),
                'loan_id': loan.id
            }
            loan_details.append(loan_detail)

        # Si el préstamo es una renovación activa y se realizó hoy, recopilar detalles adicionales
        if loan.is_renewal and loan.status:
            # Obtener solo la fecha de la renovación
            renewal_date = loan.creation_date.date()
            if renewal_date >= datetime.today().date():  # Verificar si la renovación se realizó hoy
                renewal_loan_detail = {
                    'client_name': loan.client.first_name + ' ' + loan.client.last_name,
                    'loan_amount': loan.amount,
                    'loan_dues': loan.dues,
                    'loan_interest': loan.interest,
                    # Agregar la fecha de la renovación
                    'renewal_date': renewal_date.strftime('%d/%m/%Y'),
                    'loan_id': loan.id
                }
                renewal_loan_details.append(renewal_loan_detail)

    # Calcular el valor total para cada préstamo
    for loan_detail in loan_details:
        loan_amount = float(loan_detail['loan_amount'])
        loan_interest = float(loan_detail['loan_interest'])
        loan_detail['total_amount'] = loan_amount + \
            (loan_amount * loan_interest / 100)

    # Calcular el valor total para cada préstamo de renovación activa
    for renewal_loan_detail in renewal_loan_details:
        loan_amount = float(renewal_loan_detail['loan_amount'])
        loan_interest = float(renewal_loan_detail['loan_interest'])
        renewal_loan_detail['total_amount'] = loan_amount + \
            (loan_amount * loan_interest / 100)

    # Obtener detalles de gastos, ingresos y retiros asociados a ese vendedor y ordenar por fecha de creación descendente
    transactions = Transaction.query.filter(
        Transaction.employee_id == employee_id,
        ~Transaction.description.like('[ELIMINADA]%')
    ).order_by(Transaction.creation_date.desc()).all()

    # Filtrar transacciones por tipo y fecha
    today = datetime.today().date()
    expenses = [trans for trans in transactions if
                trans.transaction_types == TransactionType.GASTO and trans.approval_status == ApprovalStatus.APROBADA and trans.creation_date.date() == today]
    incomes = [trans for trans in transactions if
               trans.transaction_types == TransactionType.INGRESO and trans.approval_status == ApprovalStatus.APROBADA and trans.creation_date.date() == today]
    withdrawals = [trans for trans in transactions if
                   trans.transaction_types == TransactionType.RETIRO and trans.approval_status == ApprovalStatus.APROBADA and trans.creation_date.date() == today]

    # Recopilar detalles con formato de fecha y clases de Bootstrap
    expense_details = [
        {'description': trans.description, 'amount': trans.amount, 'approval_status': trans.approval_status.name,
         'attachment': trans.attachment, 'date': trans.creation_date.strftime('%d/%m/%Y')} for trans in expenses]
    income_details = [
        {'description': trans.description, 'amount': trans.amount, 'approval_status': trans.approval_status.name,
         'attachment': trans.attachment, 'date': trans.creation_date.strftime('%d/%m/%Y')} for trans in incomes]
    withdrawal_details = [
        {'description': trans.description, 'amount': trans.amount, 'approval_status': trans.approval_status.name,
         'attachment': trans.attachment, 'date': trans.creation_date.strftime('%d/%m/%Y')} for trans in withdrawals]

    # Calcular clientes con cuotas en mora gestionadas hoy (con pago de $0)
    clients_in_arrears = []
    for loan in loans:
        for installment in loan.installments:
            if installment.status == InstallmentStatus.MORA:
                # Buscar si hay un pago de $0 registrado hoy para esta cuota
                payment_today = Payment.query.filter(
                    Payment.installment_id == installment.id,
                    Payment.amount == 0,
                    func.date(Payment.payment_date) == today
                ).first()
                
                if payment_today:  # Solo incluir si fue gestionada hoy
                    # Buscar si ya agregamos este cliente para evitar duplicados
                    existing_client = next((client for client in clients_in_arrears if client['loan_id'] == loan.id), None)
                    
                    if existing_client:
                        # Actualizar el cliente existente
                        existing_client['arrears_count'] += 1
                        existing_client['overdue_balance'] += installment.amount
                    else:
                        # Crear nuevo cliente
                        client_arrears = {
                            'client_name': loan.client.first_name + ' ' + loan.client.last_name,
                            'arrears_count': 1,
                            'overdue_balance': installment.amount,
                            'total_loan_amount': loan.amount + (loan.amount * loan.interest / 100),
                            'loan_id': loan.id,
                            '_sort_time': payment_today.payment_date
                        }
                        clients_in_arrears.append(client_arrears)

    # Ordenar lista de mora por fecha de procesamiento
    clients_in_arrears.sort(key=lambda x: x['_sort_time'])

    # Obtener todos los pagos realizados hoy
    payments_today = Payment.query.join(LoanInstallment).join(Loan).join(Employee).filter(Employee.id == employee_id,
                                                                                          func.date(
                                                                                              Payment.payment_date) == today).order_by(Payment.payment_date.asc()).all()

    # Recopilar detalles de los pagos realizados hoy
    payment_details = []
    payment_summary = {}  # Dictionary to store payment summary for each client, date, and loan

    for payment in payments_today:
        client_name = payment.installment.loan.client.first_name + \
            ' ' + payment.installment.loan.client.last_name
        payment_date = payment.payment_date.date()
        loan_id = payment.installment.loan.id

        # Calculate expected installment amount dynamically
        # loan = payment.installment.loan
        # expected_installment_amount = int((loan.amount + (loan.amount * loan.interest / 100)) / loan.dues) if loan.dues > 0 else 0
        expected_installment_amount = payment.installment.fixed_amount

        # Check if payment summary already exists for the client, date, and loan
        if (client_name, payment_date, loan_id) in payment_summary:
            summary = payment_summary[(client_name, payment_date, loan_id)]
            # Update the existing payment summary with the payment amount
            summary['payment_amount'] += payment.amount
            
            if payment.installment.id not in summary['_processed_installments']:
                 summary['expected_amount'] += expected_installment_amount
                 summary['_processed_installments'].add(payment.installment.id)
            else:
                 # Check if this is a different payment transaction for the same installment
                 # If we are processing multiple payments for the same installment in the loop,
                 # we should NOT add expected_amount again.
                 # The current logic handles "multiple installments" correctly by checking ID.
                 # However, if 'payments_today' contains multiple entries for the same installment 
                 # (e.g. partial payments), the 'else' block ensures we don't add expected_amount again.
                 pass

        else:
            # Create a new payment summary for the client, date, and loan
            remaining_balance = sum(inst.amount for inst in payment.installment.loan.installments if inst.status in (
                InstallmentStatus.PENDIENTE, InstallmentStatus.MORA, InstallmentStatus.ABONADA))
            total_credit = payment.installment.loan.amount  # Total credit from the loan model
            if payment.amount > 0:  # Only include payments greater than 0
                payment_summary[(client_name, payment_date, loan_id)] = {
                    'loan_id': payment.installment.loan.id,  # Add loan_id to the payment details
                    # Add installment_id to the payment details
                    'installment_id': payment.installment.id,
                    'client_name': client_name,
                    'payment_amount': payment.amount,
                    'expected_amount': expected_installment_amount,
                    'remaining_balance': remaining_balance,
                    'total_credit': total_credit,  # Add total credit to the payment details
                    'payment_date': payment_date.strftime('%d/%m/%y'),
                    '_processed_installments': {payment.installment.id}
                }

    # Convert payment summary dictionary to a list of payment details
    payment_details = list(payment_summary.values())



    loan_id = payment_details[0].get('loan_id') if payment_details else None
    installment_id = payment_details[0].get(
        'installment_id') if payment_details else None
    
    # Obtener el valor de closing_total del modelo EmployeeRecord
    employee_record = EmployeeRecord.query.filter_by(employee_id=employee_id).order_by(EmployeeRecord.creation_date.desc()).first()
    closing_total = employee_record.closing_total if employee_record else 0


    # *** Cálculo de totales (INGRESOS y EGRESOS) ***
    # Calcular el total de pagos e ingresos
    # sum(payment['payment_amount'] for payment in payment_details) + \
    # sum(income['amount'] for income in income_details) + 
    total_ingresos = Decimal(closing_total)
        
    total_movimientos = sum(payment['payment_amount'] for payment in payment_details) + \
                        sum(income['amount'] for income in income_details)

    # Calcular el total de egresos (retiros, gastos, préstamos, renovaciones)
    total_egresos = sum(withdrawal['amount'] for withdrawal in withdrawal_details) + \
        sum(expense['amount'] for expense in expense_details) + \
        sum(loan['loan_amount'] for loan in loan_details) + \
        sum(renewal['loan_amount'] for renewal in renewal_loan_details) \
        
    
    total_final = total_movimientos + total_ingresos - total_egresos

    # Calcular contadores de créditos únicos
    # Contador de créditos que han pagado (área de Pago)
    paid_loans_count = len(set(payment['loan_id'] for payment in payment_details))
    
    # Contador de créditos que no han pagado (área de No Pago)
    unpaid_loans_count = len(set(client['loan_id'] for client in clients_in_arrears))

    
    # Renderizar la plantilla HTML con los datos recopilados
    return render_template('box-detail.html',
                           salesman=employee.salesman,
                           loans_details=loan_details,
                           renewal_loan_details=renewal_loan_details,
                           expense_details=expense_details,
                           income_details=income_details,
                           withdrawal_details=withdrawal_details,
                           clients_in_arrears=clients_in_arrears,
                           total_ingresos=total_ingresos,  # <-- Total ingresos agregado
                           total_final = total_final,
                           total_movimientos=total_movimientos,
                           total_egresos=total_egresos,
                           payment_details=payment_details,
                           paid_loans_count=paid_loans_count,
                           unpaid_loans_count=unpaid_loans_count,
                           user_role=user_role,
                           loan_id=loan_id,
                           installment_id=installment_id,
                           user_id=user_id)




@routes.route('/add-employee-record/<int:employee_id>', methods=['POST'])
def add_employee_record(employee_id):
    fecha_actual = datetime.now().date()

    employee = Employee.query.get(employee_id)
    if employee is not None:
        # Alternar estado: 0 (cerrada) -> 1 (abierta), 1 (activa) -> 0 (cerrada)
        current_status = getattr(employee, 'status', None)
        if current_status == 0:
            employee.status = 1
        elif current_status == 1:
            employee.status = 0

    # Guardar los cambios en la base de datos
    if employee is not None:
        db.session.add(employee)
        db.session.commit()

    # Redirigir a la página de origen (box o box-detail-admin)
    redirect_url = request.form.get('redirect_url', url_for('routes.box'))
    return redirect(redirect_url)


@routes.route('/all-open-boxes', methods=['POST'])
def all_open_boxes():
    user_id = session.get('user_id')

    if user_id is None:
        return jsonify({'message': 'Usuario no encontrado en la sesión'}), 401

    # Verificar si el usuario es un coordinador
    user = User.query.get(user_id)
    if user is None or user.role != Role.COORDINADOR:
        return jsonify({'message': 'El usuario no es un coordinador válido'}), 403

    # Obtener la información de la caja del coordinador
    coordinator = Employee.query.filter_by(user_id=user_id).first()

    # Obtener el ID del manager del coordinador
    manager_id = db.session.query(Manager.id).filter_by(
        employee_id=coordinator.id).scalar()

    if not manager_id:
        return jsonify({'message': 'No se encontró ningún coordinador asociado a este empleado'}), 404

    salesmen = Salesman.query.filter_by(manager_id=manager_id).all()

    # Cambiar el estado de los empleados de los vendedores a True
    for salesman in salesmen:
        salesman.employee.status = True

    db.session.commit()

    # Redirigir a la página de origen (box o box-detail-admin)
    redirect_url = request.form.get('redirect_url', url_for('routes.box'))
    return redirect(redirect_url)


# Cierra las cajas desde la vista del vendedor

@routes.route('/add-daily-collected/<int:employee_id>', methods=['POST'])
def add_daily_collected(employee_id):
    fecha_actual = datetime.now().date()

    if request.method == 'POST':
        # Buscar el último registro de caja del día anterior
        last_record = EmployeeRecord.query.filter_by(employee_id=employee_id) \
            .filter(func.date(EmployeeRecord.creation_date) <= fecha_actual) \
            .order_by(EmployeeRecord.creation_date.desc()).first()

        employee = Employee.query.get(employee_id)
        employee_status = employee.status

        # Transacciones de tipo ingreso y aprobadas
        transaction_income = Transaction.query.filter_by(employee_id=employee_id, transaction_types=TransactionType.INGRESO,
                                                         approval_status=ApprovalStatus.APROBADA).all()

        transaction_income_today = Transaction.query.filter_by(employee_id=employee_id, transaction_types=TransactionType.INGRESO,
                                                               approval_status=ApprovalStatus.APROBADA).filter(func.date(Transaction.creation_date) == fecha_actual).all()

        transaction_income_total_today = sum(
            transaction.amount for transaction in transaction_income_today)

        transaction_income_total = sum(
            transaction.amount for transaction in transaction_income)

        # Usar el cierre de caja del último registro como el estado inicial, si existe
        if last_record:
            initial_state = last_record.closing_total + \
                float(transaction_income_total_today)
        else:
            initial_state = transaction_income_total

        # Calcular la cantidad de préstamos por cobrar
        loans_to_collect = Loan.query.filter_by(
            employee_id=employee_id, status=True).count()

        # Subconsulta para obtener los IDs de las cuotas de préstamo del empleado
        subquery = db.session.query(LoanInstallment.id) \
            .join(Loan) \
            .filter(Loan.employee_id == employee_id) \
            .subquery()

        # Subconsulta para obtener los IDs de las cuotas de préstamo PAGADA del empleado
        paid_installments_query = db.session.query(LoanInstallment.id) \
            .join(Loan) \
            .filter(Loan.employee_id == employee_id,
                    LoanInstallment.status == InstallmentStatus.PAGADA) \
            .subquery()

        # Calcular la cantidad de cuotas PAGADA y su total
        paid_installments = db.session.query(func.sum(Payment.amount)) \
            .join(paid_installments_query, Payment.installment_id == paid_installments_query.c.id) \
            .filter(func.date(Payment.payment_date) == fecha_actual) \
            .scalar() or 0

        # Obtén la fecha de mañana
        tomorrow = datetime.now().date() + timedelta(days=1)

        total_pending_installments_amount = 0

        for client in employee.clients:
            for loan in client.loans:
                # Encuentra todas las cuotas con fecha de vencimiento igual a mañana y estado pendiente o pagada
                installments_tomorrow = LoanInstallment.query.filter(
                    LoanInstallment.loan_id == loan.id,
                    LoanInstallment.due_date == tomorrow,
                    LoanInstallment.status.in_(
                        [InstallmentStatus.PENDIENTE, InstallmentStatus.PAGADA])
                ).all()

                for installment in installments_tomorrow:
                    total_pending_installments_amount += installment.fixed_amount

        # Subconsulta para obtener los IDs de las cuotas de préstamo ABONADAS del empleado
        partial_installments_query = db.session.query(LoanInstallment.id) \
            .join(Loan) \
            .filter(Loan.employee_id == employee_id,
                    LoanInstallment.status == InstallmentStatus.ABONADA) \
            .subquery()

        # Calcular la cantidad de cuotas ABONADAS y su total
        partial_installments = db.session.query(func.sum(Payment.amount)) \
            .join(partial_installments_query,
                  Payment.installment_id == partial_installments_query.c.id) \
            .filter(func.date(Payment.payment_date) == fecha_actual) \
            .scalar() or 0

        # Verificar si todos los préstamos tienen un pago igual al de hoy
        all_loans_paid = Loan.query.filter_by(employee_id=employee_id).all()
        all_loans_paid_today = False
        for loan in all_loans_paid:
            loan_installments = LoanInstallment.query.filter_by(
                loan_id=loan.id).all()
            for installment in loan_installments:
                payments = Payment.query.filter_by(
                    installment_id=installment.id).all()
                if any(payment.payment_date.date() == fecha_actual for payment in payments):
                    all_loans_paid_today = True
                    break
                if all_loans_paid_today:
                    break

        

        # Subconsulta para obtener los IDs de las cuotas de préstamo en mora del empleado
        overdue_installments_query = db.session.query(LoanInstallment.id) \
            .join(Loan) \
            .filter(Loan.employee_id == employee_id,
                    LoanInstallment.status == InstallmentStatus.MORA) \
            .subquery()

        # Calcular la cantidad de cuotas vencidas y su total
        overdue_installments_total = db.session.query(func.sum(LoanInstallment.amount)) \
            .join(overdue_installments_query,
                  LoanInstallment.id == overdue_installments_query.c.id) \
            .join(Payment, Payment.installment_id == LoanInstallment.id) \
            .filter(func.date(Payment.payment_date) == fecha_actual) \
            .scalar() or 0


        # Calcular el total recaudado en la fecha actual
        total_collected = db.session.query(
            db.func.sum(Payment.amount)
        ).join(LoanInstallment, LoanInstallment.id == Payment.installment_id).join(
            Loan, Loan.id == LoanInstallment.loan_id
        ).filter(
            and_(Loan.employee_id == employee_id, func.date(
                Payment.payment_date) == fecha_actual)
        ).scalar() or 0

# Calcula el total de préstamos de los nuevos clientes
        new_clients_loan_amount = Loan.query.join(Client).filter(
            Client.employee_id == employee_id,
            Loan.creation_date >= datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0),
            Loan.is_renewal == False,  # Excluir renovaciones
            Loan.status == True  # Solo préstamos activos
        ).with_entities(func.sum(Loan.amount)).scalar() or 0

        # Calcula el monto total de las renovaciones de préstamos para este vendedor
        total_renewal_loans_amount = Loan.query.filter(
            Loan.client.has(employee_id=employee_id),
            Loan.is_renewal == True,
            Loan.status == True,
            Loan.approved == True,
            Loan.creation_date >= datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0)
            # Loan.creation_date < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        ).with_entities(func.sum(Loan.amount)).scalar() or 0

        # Calcula Valor de los gastos diarios
        daily_expenses_amount = Transaction.query.filter(
            Transaction.employee_id == employee_id,
            Transaction.transaction_types == TransactionType.GASTO,
            # Filtrar por fecha actual
            func.date(Transaction.creation_date) == datetime.now().date()
        ).with_entities(func.sum(Transaction.amount)).scalar() or 0

        # Calcula los retiros diarios basados en transacciones de RETIRO
        daily_withdrawals = Transaction.query.filter(
            Transaction.employee_id == employee_id,
            Transaction.transaction_types == TransactionType.RETIRO,
            # Filtrar por fecha actual
            func.date(Transaction.creation_date) == datetime.now().date()
        ).with_entities(func.sum(Transaction.amount)).scalar() or 0

        # Calcula las colecciones diarias basadas en transacciones de INGRESO
        daily_incomings = Transaction.query.filter(
            Transaction.employee_id == employee_id,
            Transaction.transaction_types == TransactionType.INGRESO,
            # Filtrar por fecha actual
            func.date(Transaction.creation_date) == datetime.now().date()
        ).with_entities(func.sum(Transaction.amount)).scalar() or 0

        # Crear una instancia de EmployeeRecord
        message = "Caja Activada"
        success = False

        if employee_status == 1 and all_loans_paid_today == True:
            employee_record = EmployeeRecord(
                employee_id=employee_id,
                initial_state=initial_state,
                loans_to_collect=loans_to_collect,
                paid_installments=paid_installments,
                partial_installments=partial_installments,
                overdue_installments=overdue_installments_total,
                incomings=daily_incomings,
                expenses=daily_expenses_amount,
                sales=new_clients_loan_amount,
                renewals=total_renewal_loans_amount,
                due_to_collect_tomorrow=total_pending_installments_amount,
                withdrawals=daily_withdrawals,
                total_collected=total_collected,
                closing_total=int(initial_state) + int(paid_installments)
                + int(partial_installments)
                - int(new_clients_loan_amount)
                - int(total_renewal_loans_amount)
                #   + int(daily_incomings)
                - int(daily_withdrawals)
                - int(daily_expenses_amount),  # Calcular el cierre de caja
                creation_date=datetime.now()
            )

            employee.status = 0
            db.session.add(employee)
            # Agregar la instancia a la sesión de la base de datos y guardar los cambios
            db.session.add(employee_record)
            db.session.commit()


        else:
            if employee_status == 1 and all_loans_paid_today == False:
                message = "desactivada"
                success = False
                employee.status = 0
            else:
                employee.status = 1

            # Guardar los cambios en la base de datos
            db.session.add(employee)
            db.session.commit()

    return redirect(url_for('routes.logout'))



@routes.route('/closed-boxes')
def closed_boxes():
    # Código de la función que quieres ejecutar
    return "Tarea ejecutada con éxito"


