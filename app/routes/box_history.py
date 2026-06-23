# app/routes/box_history.py
# Historial de caja y registros de cierre

# Importaciones estándar
from datetime import datetime, date, timedelta
from decimal import Decimal
import os
import uuid
import holidays
import io

# Importaciones de SQLAlchemy
from sqlalchemy import func, case, join, tuple_
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

@routes.route('/history-box', methods=['POST', 'GET'])
def history_box():
    try:
        # Validar acceso del coordinador
        user_id, user = validate_coordinator_access()
        
        # Obtener datos del coordinador y sus vendedores
        coordinator, coordinator_cash_base, coordinator_name, manager_id, salesmen = get_coordinator_data(user_id)
        
        # Obtener filter_date
        if request.method == 'POST':
            filter_date = request.form.get('filter_date')
            if isinstance(filter_date, str) and filter_date:
                from datetime import datetime as dt
                try:
                    filter_date = dt.strptime(filter_date, '%Y-%m-%d').date()
                except ValueError:
                    filter_date = datetime.now().date()
            elif not filter_date:
                filter_date = datetime.now().date()
            else:
                filter_date = datetime.now().date()
        else:
            filter_date = datetime.now().date()
        
        # Para testing, usar fecha actual si la fecha es futura
        if filter_date > datetime.now().date():
            filter_date = datetime.now().date()
        
        # Calcular coordinator_cash para la fecha filtrada (lógica específica de history_box)
        if filter_date != None:
            coordinator_cash = db.session.query(
                func.sum(EmployeeRecord.closing_total)
            ).filter(
                EmployeeRecord.employee_id == coordinator.id,
                func.date(EmployeeRecord.creation_date) == filter_date
            ).scalar() or 0
        else:
            coordinator_cash = coordinator.box_value

        # Calcular totales de transacciones del coordinador para la fecha filtrada (excluyendo subcoordinadores)
        salesman_incomes, salesman_withdrawals, coordinator_incomes, coordinator_withdrawals = calculate_daily_transaction_totals_history(manager_id, filter_date, coordinator.id)

        # Obtener los gastos del coordinador para la fecha filtrada
        expenses = Transaction.query.filter(
            Transaction.employee_id == coordinator.id,
            Transaction.transaction_types == 'GASTO',
            func.date(Transaction.creation_date) == filter_date
        ).all()

        # Obtener el valor total de los gastos
        total_expenses = sum(expense.amount for expense in expenses)

        manager_expense_details = [
            {'description': trans.description, 'amount': trans.amount, 'approval_status': trans.approval_status.name,
                'attachment': trans.attachment, 'date': trans.creation_date.strftime('%d/%m/%Y')} for trans in expenses]

        # Calcular valor final de la caja del coordinador según las reglas de negocio
        final_box_value = float(coordinator_cash) \
                         - float(salesman_incomes) \
                         + float(salesman_withdrawals) \
                         - float(total_expenses) \
                         + float(coordinator_incomes) \
                         - float(coordinator_withdrawals)

        # Construir la respuesta como variables separadas
        coordinator_box = {
            'maximum_cash': coordinator_cash,
            'total_outbound_amount': float(salesman_incomes + coordinator_withdrawals),  # Para compatibilidad con template
            'total_inbound_amount': float(salesman_withdrawals + coordinator_incomes),  # Para compatibilidad con template
            'total_expenses': float(total_expenses),
            'final_box_value': final_box_value,
            'expense_details': manager_expense_details
        }

        # OPTIMIZACIÓN: Obtener todos los datos de vendedores en consultas optimizadas
        salesmen_data = get_all_salesmen_data_optimized_history(salesmen, filter_date)
        
        # OPTIMIZACIÓN: Obtener datos adicionales en una sola consulta para todos los vendedores
        employee_ids = [salesman[0].employee_id for salesman in salesmen]
        additional_data = get_all_salesmen_additional_data_optimized_history(employee_ids, filter_date)
        
        # Asegurar que additional_data tenga datos por defecto para todos los empleados
        for emp_id in employee_ids:
            if emp_id not in additional_data:
                additional_data[emp_id] = {
                    'total_customers': 0,
                    'customers_in_arrears': 0,
                    'total_pending_installments_amount': 0,
                    'all_loans_paid_today': False,
                    'expense_details': [],
                    'income_details': [],
                    'withdrawal_details': []
                }
        
        # Procesar cada vendedor con datos pre-cargados
        salesmen_stats = []
        for salesman, employee, user in salesmen:
            employee_id = salesman.employee_id
            
            # Obtener datos optimizados
            data = salesmen_data.get(employee_id, {})
            additional = additional_data.get(employee_id, {})
            
            # Combinar datos
            data.update(additional)
            
            # Verificar si existe registro del día filtrado para usar closing_total directamente
            filter_date_record = None
            if filter_date != datetime.now().date():
                filter_date_record = db.session.query(EmployeeRecord).filter(
                    EmployeeRecord.employee_id == employee_id,
                    func.date(EmployeeRecord.creation_date) == filter_date
                ).order_by(EmployeeRecord.id.desc()).first()
            
            # Si existe registro del día filtrado, usar el closing_total guardado en DB
            if filter_date_record:
                box_value = float(filter_date_record.closing_total)
            else:
                # Calcular solo si no existe registro del día
                box_value = calculate_box_value(
                    data.get('initial_box_value', 0), 
                    data.get('total_collections_today', 0), 
                    data.get('daily_withdrawals', 0), 
                    data.get('daily_expenses_amount', 0),
                    data.get('daily_collection', 0), 
                    data.get('new_clients_loan_amount', 0),
                    data.get('total_renewal_loans_amount', 0), 
                    data.get('existing_record_today', False)
                )
            
            # Crear datos del vendedor con la estructura esperada
            salesman_data = {
                'salesman_name': data.get('salesman_name', ''),
                'employee_id': employee_id,
                'employee_status': data.get('employee_status', False),
                'role_employee': data.get('role_employee', ''),
                'total_collections_today': data.get('total_collections_today', 0),
                'new_clients': data.get('new_clients', 0),
                'daily_expenses': data.get('daily_expenses_count', 0),
                'daily_expenses_amount': data.get('daily_expenses_amount', 0),
                'daily_withdrawals': data.get('daily_withdrawals', 0),
                'daily_collections_made': data.get('daily_collection', 0),
                'total_number_of_customers': data.get('total_customers', 0),
                'customers_in_arrears_for_the_day': data.get('customers_in_arrears', 0),
                'total_renewal_loans': data.get('total_renewal_loans', 0),
                'total_new_clients_loan_amount': data.get('new_clients_loan_amount', 0),
                'total_renewal_loans_amount': data.get('total_renewal_loans_amount', 0),
                'daily_withdrawals_count': data.get('daily_withdrawals_count', 0),
                'daily_collection_count': data.get('daily_collection_count', 0),
                'total_pending_installments_amount': data.get('total_pending_installments_amount', 0),
                'all_loans_paid_today': data.get('all_loans_paid_today', False),
                'total_clients_collected': data.get('daily_collections_count', 0),
                'box_value': box_value,
                'initial_box_value': data.get('initial_box_value', 0),
                'expense_details': data.get('expense_details', []),
                'income_details': data.get('income_details', []),
                'withdrawal_details': data.get('withdrawal_details', [])
            }
            
            salesmen_stats.append(salesman_data)

        # Procesar búsqueda
        search_term = request.args.get('salesman_name', '')
        if search_term:
            salesmen_stats = [salesman for salesman in salesmen_stats if
                            search_term.lower() in salesman['salesman_name'].lower()]

        # Renderizar la plantilla con las variables
        return render_template('history-box.html', 
                            coordinator_box=coordinator_box, 
                            salesmen_stats=salesmen_stats,
                            search_term=search_term, 
                            filter_date=filter_date, 
                            manager_id=manager_id, 
                            coordinator_name=coordinator_name, 
                            user_id=user_id, 
                            expense_details=manager_expense_details, 
                            total_expenses=total_expenses)
                            
    except ValueError as e:
        return jsonify({'message': str(e)}), 401 if 'Usuario no encontrado' in str(e) else 403
    except Exception as e:
        return jsonify({'message': 'Error interno del servidor', 'error': str(e)}), 500







@routes.route('/add-manager-record')
def add_manager_record():
    try:
        users_manager = User.query.filter_by(role=Role.COORDINADOR).all()
        users_salesman = User.query.filter_by(role=Role.VENDEDOR).all()
        
        # Ajuste para tareas cron en la madrugada: 
        # Si se ejecuta antes de las 8 AM, se toma como el cierre del día anterior.
        now_time = datetime.now()
        if now_time.hour < 8:
            current_date = (now_time - timedelta(days=1)).date()
        else:
            current_date = now_time.date()


        # OPTIMIZACIÓN: Pre-cargar todos los employee_ids que son managers en un set
        all_manager_employee_ids = {
            m.employee_id for m in db.session.query(Manager.employee_id).all()
        }

        # OPTIMIZACIÓN: Recopilar employee_ids que serán procesados por coordinadores
        # para evitar procesamiento duplicado
        employees_under_coordinators = set()
        for user in users_manager:
            employee = Employee.query.filter_by(user_id=user.id).first()
            if not employee:
                continue
            manager = Manager.query.filter_by(employee_id=employee.id).first()
            if manager:
                # Agregar todos los vendedores puros bajo este coordinador
                salesmen = Salesman.query.filter_by(manager_id=manager.id).all()
                for s in salesmen:
                    if s.employee_id not in all_manager_employee_ids:
                        employees_under_coordinators.add(s.employee_id)

        # PRIMERO: Procesar SOLO vendedores que NO son coordinadores Y NO están bajo un coordinador
        for user in users_salesman:
            employee = Employee.query.filter_by(user_id=user.id).first()
            if not employee:
                continue
            
            # Saltar si es manager o si ya será procesado por un coordinador
            if employee.id in all_manager_employee_ids:
                continue
            if employee.id in employees_under_coordinators:
                continue
            
            # Es un vendedor huérfano (sin coordinador) - procesarlo
            process_salesman_record(employee.id, current_date)

        # SEGUNDO: Procesar coordinadores usando función recursiva (bottom-up)
        # Esto internamente procesará a sus vendedores subordinados
        for user in users_manager:
            manager_array = Employee.query.filter_by(user_id=user.id).first()
            if not manager_array:
                continue
            
            manager = Manager.query.filter_by(employee_id=manager_array.id).first()
            if manager:
                process_coordinator_hierarchy(manager.id, current_date)
        
        # OPTIMIZACIÓN: Un solo commit para todas las operaciones
        db.session.commit()
        
        return render_template('add-manager-record.html')
    except Exception as e:
        db.session.rollback()
        # Log del error (puedes usar logging aquí)
        return render_template('add-manager-record.html')


@routes.route('/add-manager-record/<target_date>')
def add_manager_record_for_date(target_date):
    """Generar registros de cierre de caja para una fecha específica
    ---
    tags:
      - Caja
    parameters:
      - name: target_date
        in: path
        type: string
        required: true
        description: Fecha en formato YYYY-MM-DD (ej. 2026-05-20)
    responses:
      200:
        description: Registros generados o diagnóstico de datos
        schema:
          type: object
          properties:
            message:
              type: string
            diagnostics:
              type: object
              properties:
                fecha_solicitada:
                  type: string
                datos_encontrados:
                  type: object
                  properties:
                    pagos_en_fecha:
                      type: integer
                    transacciones_aprobadas_en_fecha:
                      type: integer
                    prestamos_creados_en_fecha:
                      type: integer
            resultado:
              type: object
              properties:
                vendedores_procesados:
                  type: integer
                coordinadores_procesados:
                  type: integer
                registros_creados:
                  type: integer
                registros_con_valores:
                  type: integer
      400:
        description: Formato de fecha inválido o fecha futura
      500:
        description: Error interno del servidor
    """
    try:
        # Validar formato de fecha
        try:
            current_date = datetime.strptime(target_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD (ej: 2026-05-20)'}), 400

        # Validar que la fecha no sea futura
        if current_date > datetime.now().date():
            return jsonify({'error': 'No se pueden generar registros para fechas futuras'}), 400

        # --- DIAGNÓSTICO: Verificar que existen datos para la fecha solicitada ---
        total_payments = db.session.query(func.count(Payment.id)).filter(
            func.date(Payment.payment_date) == current_date
        ).scalar() or 0

        total_transactions = db.session.query(func.count(Transaction.id)).filter(
            func.date(Transaction.creation_date) == current_date,
            Transaction.approval_status == ApprovalStatus.APROBADA
        ).scalar() or 0

        total_loans_created = db.session.query(func.count(Loan.id)).filter(
            func.date(Loan.creation_date) == current_date
        ).scalar() or 0

        diagnostics = {
            'fecha_solicitada': target_date,
            'datos_encontrados': {
                'pagos_en_fecha': total_payments,
                'transacciones_aprobadas_en_fecha': total_transactions,
                'prestamos_creados_en_fecha': total_loans_created
            }
        }

        if total_payments == 0 and total_transactions == 0 and total_loans_created == 0:
            return jsonify({
                'warning': f'No se encontraron datos (pagos, transacciones, préstamos) para la fecha {target_date}. '
                           'Verifique que las fechas en la base de datos correspondan a esta fecha.',
                'diagnostics': diagnostics
            }), 200

        # --- PROCESAR REGISTROS ---
        users_manager = User.query.filter_by(role=Role.COORDINADOR).all()
        users_salesman = User.query.filter_by(role=Role.VENDEDOR).all()

        # Pre-cargar todos los employee_ids que son managers
        all_manager_employee_ids = {
            m.employee_id for m in db.session.query(Manager.employee_id).all()
        }

        # PRIMERO: Procesar TODOS los vendedores puros (mismo flujo que la ruta original)
        processed_salesmen = 0
        for user in users_salesman:
            employee = Employee.query.filter_by(user_id=user.id).first()
            if not employee:
                continue
            if employee.id in all_manager_employee_ids:
                continue
            process_salesman_record(employee.id, current_date)
            processed_salesmen += 1

        # SEGUNDO: Procesar coordinadores (bottom-up, incluye sus vendedores)
        processed_coordinators = 0
        for user in users_manager:
            manager_array = Employee.query.filter_by(user_id=user.id).first()
            if not manager_array:
                continue
            manager = Manager.query.filter_by(employee_id=manager_array.id).first()
            if manager:
                process_coordinator_hierarchy(manager.id, current_date)
                processed_coordinators += 1
        
        db.session.commit()

        # Verificar los registros creados
        records_created = EmployeeRecord.query.filter(
            func.date(EmployeeRecord.creation_date) == current_date
        ).count()

        records_with_values = EmployeeRecord.query.filter(
            func.date(EmployeeRecord.creation_date) == current_date,
            (EmployeeRecord.total_collected > 0) | (EmployeeRecord.paid_installments > 0) |
            (EmployeeRecord.incomings > 0) | (EmployeeRecord.expenses > 0)
        ).count()
        
        return jsonify({
            'message': f'Registros generados para {target_date}',
            'diagnostics': diagnostics,
            'resultado': {
                'vendedores_procesados': processed_salesmen,
                'coordinadores_procesados': processed_coordinators,
                'registros_creados': records_created,
                'registros_con_valores': records_with_values
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error al generar registros: {str(e)}'}), 500



@routes.route('/history-box-detail/<int:employee_id>', methods=['GET', 'POST'])
def history_box_detail(employee_id):
    filter_date = request.args.get('filter_date')  # Obtener el parámetro de la URL

    if not filter_date:
        return jsonify({'error': 'Se requiere filter_date'}), 400

    # Convertir la fecha en un objeto datetime.date si es necesario
    try:
        filter_date = datetime.strptime(filter_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400

    
    # Obtener el rol y el user_id del empleado
    employee = Employee.query.get(employee_id)
    if not employee:
        return jsonify({'error': 'Empleado no encontrado'}), 404

    role = employee.user.role.name
    user_id = employee.user_id

    
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
        
        if loan_date == filter_date and loan.is_renewal == 0 and loan.status:  # Verificar si el préstamo se realizó en la fecha filtrada y está activo
            loan_detail = {
                'client_name': loan.client.first_name + ' ' + loan.client.last_name,
                'loan_amount': loan.amount,
                'loan_dues': loan.dues,
                'loan_interest': loan.interest,
                # Agregar la fecha del préstamo
                'loan_date': loan_date.strftime('%d/%m/%Y')
            }
            loan_details.append(loan_detail)

        # Si el préstamo es una renovación activa y se realizó en la fecha filtrada, recopilar detalles adicionales
        if loan.is_renewal and loan.status:
            # Obtener solo la fecha de la renovación
            renewal_date = loan.creation_date.date()
            if renewal_date == filter_date:  # Verificar si la renovación se realizó en la fecha filtrada
                renewal_loan_detail = {
                    'client_name': loan.client.first_name + ' ' + loan.client.last_name,
                    'loan_amount': loan.amount,
                    'loan_dues': loan.dues,
                    'loan_interest': loan.interest,
                    # Agregar la fecha de la renovación
                    'renewal_date': renewal_date.strftime('%d/%m/%Y')
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
    expenses = [trans for trans in transactions if
                trans.transaction_types == TransactionType.GASTO and trans.approval_status == ApprovalStatus.APROBADA and trans.creation_date.date() == filter_date]
    incomes = [trans for trans in transactions if
               trans.transaction_types == TransactionType.INGRESO and trans.approval_status == ApprovalStatus.APROBADA and trans.creation_date.date() == filter_date]
    withdrawals = [trans for trans in transactions if
                   trans.transaction_types == TransactionType.RETIRO and trans.approval_status == ApprovalStatus.APROBADA and trans.creation_date.date() == filter_date]

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

    # Calcular clientes con cuotas en mora y cuya fecha de vencimiento sea la de la fecha filtrada
    clients_in_arrears = []
    for loan in loans:
        for installment in loan.installments:
            payment = Payment.query.filter_by(
                installment_id=installment.id).first()
            if installment.is_in_arrears() and payment and payment.payment_date.date() == filter_date:
                client_arrears = {
                    'client_name': loan.client.first_name + ' ' + loan.client.last_name,
                    'arrears_count': sum(1 for inst in loan.installments if inst.is_in_arrears()),
                    'overdue_balance': sum(inst.amount for inst in loan.installments if inst.is_in_arrears()),
                    'total_loan_amount': loan.amount,
                    'loan_id': loan.id
                }
                clients_in_arrears.append(client_arrears)

    # Obtener todos los pagos realizados en la fecha filtrada
    payments_today = Payment.query.join(LoanInstallment).join(Loan).join(Employee).filter(Employee.id == employee_id,
                                                                                          func.date(
                                                                                              Payment.payment_date) == filter_date).all()

    # Recopilar detalles de los pagos realizados en la fecha filtrada
    payment_details = []
    payment_summary = {}  # Dictionary to store payment summary for each client and date

    for payment in payments_today:
        client_name = payment.installment.loan.client.first_name + \
            ' ' + payment.installment.loan.client.last_name
        payment_date = payment.payment_date.date()

        # Check if payment summary already exists for the client and date
        if (client_name, payment_date) in payment_summary:
            # Update the existing payment summary with the payment amount
            payment_summary[(client_name, payment_date)
                            ]['payment_amount'] += payment.amount
        else:
            # Create a new payment summary for the client and date
            remaining_balance = sum(inst.amount for inst in payment.installment.loan.installments if inst.status in (
                InstallmentStatus.PENDIENTE, InstallmentStatus.MORA, InstallmentStatus.ABONADA))
            total_credit = payment.installment.loan.amount  # Total credit from the loan model
            if payment.amount > 0:  # Only include payments greater than 0
                payment_summary[(client_name, payment_date)] = {
                    'loan_id': payment.installment.loan.id,  # Add loan_id to the payment details
                    # Add installment_id to the payment details
                    'installment_id': payment.installment.id,
                    'client_name': client_name,
                    'payment_amount': payment.amount,
                    'remaining_balance': remaining_balance,
                    'total_credit': total_credit,  # Add total credit to the payment details
                    'payment_date': payment_date.strftime('%d/%m/%Y'),
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

    

    # Renderizar la plantilla HTML con los datos recopilados
    return render_template('history-box-detail.html',
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
                           user_role=role,
                           user_id=user_id,
                           employee_id=employee_id,
                           loan_id=loan_id,
                           installment_id=installment_id,
                           filter_date=filter_date)




@routes.route('/history-box-detail-admin/<int:employee_id>', methods=['GET', 'POST'])
def history_box_detail_admin(employee_id):
    try:
        # Obtener el parámetro de fecha de la URL
        filter_date = request.args.get('filter_date')
        
        if not filter_date:
            return jsonify({'error': 'Se requiere filter_date'}), 400

        # Convertir la fecha en un objeto datetime.date
        try:
            filter_date = datetime.strptime(filter_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400

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

        # Obtener la información de la caja del sub-administrador para la fecha filtrada
        sub_admin_cash = db.session.query(
            func.sum(EmployeeRecord.closing_total)
        ).filter(
            EmployeeRecord.employee_id == sub_admin_employee.id,
            func.date(EmployeeRecord.creation_date) == filter_date
        ).scalar() or 0
        
        sub_admin_name = f"{sub_admin_user.first_name} {sub_admin_user.last_name}"

        # Obtener el ID del manager del sub-administrador
        manager_id = db.session.query(Manager.id).filter_by(
            employee_id=sub_admin_employee.id).scalar()

        if not manager_id:
            return jsonify({'message': 'No se encontró ningún manager asociado a este empleado'}), 404

        salesmen = Salesman.query.filter_by(manager_id=manager_id).all()

        # Calcular totales de transacciones del sub-administrador para la fecha filtrada (excluyendo subcoordinadores)
        salesman_incomes, salesman_withdrawals, coordinator_incomes, coordinator_withdrawals = calculate_daily_transaction_totals_history(manager_id, filter_date, sub_admin_employee.id)

        # Inicializa la lista para almacenar las estadísticas de los vendedores
        salesmen_stats = []

        # Ciclo a través de cada vendedor asociado al sub-administrador
        for salesman in salesmen:
            # Inicializar variables para recopilar estadísticas para cada vendedor
            total_collections_today = 0  # Recaudo Diario
            daily_expenses_count = 0  # Gastos Diarios
            daily_expenses_amount = 0  # Valor Gastos Diarios
            daily_withdrawals = 0  # Retiros Diarios
            daily_collection = 0  # Ingresos Diarios
            customers_in_arrears = 0  # Clientes en MORA o NO PAGO
            total_renewal_loans = 0  # Cantidad de Renovaciones
            total_renewal_loans_amount = 0  # Valor Total Renovaciones
            total_customers = 0  # Clientes Totales (Activos)
            new_clients = 0  # Clientes Nuevos
            new_clients_loan_amount = 0  # Valor Prestamos Nuevos
            daily_withdrawals_count = 0  # Cantidad Retiros Diarios
            daily_collection_count = 0  # Cantidad Ingresos Diarios
            total_pending_installments_amount = 0  # Monto total de cuotas pendientes
            box_value = 0  # Valor de la caja del vendedor
            initial_box_value = 0
            # Monto total de cuotas pendientes de préstamos por cerrar
            total_pending_installments_loan_close_amount = 0

            # Obtener el valor de la caja del vendedor
            employee = Employee.query.get(salesman.employee_id)
            employee_id = employee.id

            employee_userid = User.query.get(employee.user_id)
            role_employee = employee_userid.role.value

            # Obtener el valor inicial de la caja del vendedor para la fecha filtrada
            employee_records = EmployeeRecord.query.filter(
                EmployeeRecord.employee_id == salesman.employee_id,
                func.date(EmployeeRecord.creation_date) == filter_date
            ).order_by(EmployeeRecord.id.desc()).first()

            # Verificar si ya existe un registro en EmployeeRecord con la fecha filtrada
            existing_record_today = employee_records
            
            if employee_records:
                # Si existe registro del día, usar initial_state (valor inicial guardado)
                initial_box_value = float(employee_records.initial_state)
            else:
                # Si no hay registro del día, buscar último registro anterior
                last_record = EmployeeRecord.query.filter(
                    EmployeeRecord.employee_id == salesman.employee_id,
                    func.date(EmployeeRecord.creation_date) < filter_date
                ).order_by(EmployeeRecord.creation_date.desc()).first()
                
                if last_record:
                    initial_box_value = float(last_record.closing_total)
                else:
                    initial_box_value = float(employee.box_value)

            all_loans_paid = Loan.query.filter_by(employee_id=salesman.employee_id)
            all_loans_paid_today = False
            for loan in all_loans_paid:
                loan_installments = LoanInstallment.query.filter_by(loan_id=loan.id).all()
                for installment in loan_installments:
                    payments = Payment.query.filter_by(installment_id=installment.id).all()
                    if any(payment.payment_date.date() == filter_date for payment in payments):
                        all_loans_paid_today = True
                        break
                    if all_loans_paid_today:
                        break

            # Si existe registro del día filtrado, usar valores guardados en EmployeeRecord
            if employee_records:
                # Usar valores guardados en DB
                total_collections_today = float(employee_records.total_collected or 0)
                daily_expenses_amount = float(employee_records.expenses or 0)
                daily_withdrawals = float(employee_records.withdrawals or 0)
                daily_collection = float(employee_records.incomings or 0)
                new_clients_loan_amount = float(employee_records.sales or 0)
                total_renewal_loans_amount = float(employee_records.renewals or 0)
                total_pending_installments_amount = float(employee_records.due_to_charge or 0)
                box_value = float(employee_records.closing_total)
                
                # Para conteos, aún calcular desde transacciones para mantener la información
                daily_expenses_count = Transaction.query.filter(
                    Transaction.employee_id == salesman.employee_id,
                    Transaction.transaction_types == TransactionType.GASTO,
                    Transaction.approval_status == ApprovalStatus.APROBADA,
                    func.date(Transaction.creation_date) == filter_date
                ).count() or 0
                
                daily_withdrawals_count = Transaction.query.filter(
                    Transaction.employee_id == salesman.employee_id,
                    Transaction.transaction_types == TransactionType.RETIRO,
                    Transaction.approval_status == ApprovalStatus.APROBADA,
                    func.date(Transaction.creation_date) == filter_date
                ).count() or 0
                
                daily_collection_count = Transaction.query.filter(
                    Transaction.employee_id == salesman.employee_id,
                    Transaction.transaction_types == TransactionType.INGRESO,
                    Transaction.approval_status == ApprovalStatus.APROBADA,
                    func.date(Transaction.creation_date) == filter_date
                ).count() or 0
                
                # Calcular cantidad de nuevos clientes
                new_clients = Client.query.filter(
                    Client.employee_id == salesman.employee_id,
                    func.date(Client.creation_date) == filter_date
                ).count()
                
                # Calcular cantidad de renovaciones
                total_renewal_loans = Loan.query.filter(
                    Loan.client.has(employee_id=salesman.employee_id),
                    Loan.is_renewal == True,
                    Loan.status == True,
                    Loan.approved == True,
                    func.date(Loan.creation_date) == filter_date
                ).count()
            else:
                # Si no existe registro, calcular desde transacciones y otras tablas
                total_collections_today = db.session.query(
                    func.sum(Payment.amount)
                ).join(
                    LoanInstallment, Payment.installment_id == LoanInstallment.id
                ).join(
                    Loan, LoanInstallment.loan_id == Loan.id
                ).filter(
                    Loan.client.has(employee_id=salesman.employee_id),
                    func.date(Payment.payment_date) == filter_date
                ).scalar() or 0

                for client in employee.clients:
                    for loan in client.loans:
                        # Excluir préstamos creados en la fecha filtrada
                        if loan.creation_date.date() == filter_date:
                            continue
                        
                        if loan.status:
                            # Encuentra la última cuota pendiente a la fecha filtrada
                            pending_installment = LoanInstallment.query.filter(
                                LoanInstallment.loan_id == loan.id
                            ).order_by(LoanInstallment.due_date.asc()).first()
                            if pending_installment:
                                total_pending_installments_amount += pending_installment.fixed_amount
                        elif loan.status == False and loan.up_to_date and loan.modification_date.date() == filter_date:
                            pending_installment_paid = LoanInstallment.query.filter(
                                LoanInstallment.loan_id == loan.id
                            ).order_by(LoanInstallment.due_date.asc()).first()
                            total_pending_installments_loan_close_amount += pending_installment_paid.fixed_amount

                # Calcula la cantidad de nuevos clientes registrados en la fecha filtrada
                new_clients = Client.query.filter(
                    Client.employee_id == salesman.employee_id,
                    func.date(Client.creation_date) == filter_date
                ).count()

                # Calcula el total de préstamos de los nuevos clientes
                new_clients_loan_amount = Loan.query.join(Client).filter(
                    Client.employee_id == salesman.employee_id,
                    func.date(Loan.creation_date) == filter_date,
                    Loan.is_renewal == False,  # Excluir renovaciones
                    Loan.status == True  # Solo préstamos activos
                ).with_entities(func.sum(Loan.amount)).scalar() or 0

                # Calcula el total de renovaciones para la fecha filtrada para este vendedor
                total_renewal_loans = Loan.query.filter(
                    Loan.client.has(employee_id=salesman.employee_id),
                    Loan.is_renewal == True,
                    Loan.status == True,
                    Loan.approved == True,
                    func.date(Loan.creation_date) == filter_date
                ).count()

                # Calcula el monto total de las renovaciones de préstamos para este vendedor
                total_renewal_loans_amount = Loan.query.filter(
                    Loan.client.has(employee_id=salesman.employee_id),
                    Loan.is_renewal == True,
                    Loan.status == True,
                    Loan.approved == True,
                    func.date(Loan.creation_date) == filter_date
                ).with_entities(func.sum(Loan.amount)).scalar() or 0

                # Calcula Valor de los gastos diarios
                daily_expenses_amount = Transaction.query.filter(
                    Transaction.employee_id == salesman.employee_id,
                    Transaction.transaction_types == TransactionType.GASTO,
                    Transaction.approval_status == ApprovalStatus.APROBADA,
                    func.date(Transaction.creation_date) == filter_date
                ).with_entities(func.sum(Transaction.amount)).scalar() or 0

                # Calcula el número de transacciones de gastos diarios
                daily_expenses_count = Transaction.query.filter(
                    Transaction.employee_id == salesman.employee_id,
                    Transaction.transaction_types == TransactionType.GASTO,
                    Transaction.approval_status == ApprovalStatus.APROBADA,
                    func.date(Transaction.creation_date) == filter_date
                ).count() or 0

                # Calcula los retiros diarios basados en transacciones de RETIRO
                daily_withdrawals = Transaction.query.filter(
                    Transaction.employee_id == salesman.employee_id,
                    Transaction.transaction_types == TransactionType.RETIRO,
                    Transaction.approval_status == ApprovalStatus.APROBADA,
                    func.date(Transaction.creation_date) == filter_date
                ).with_entities(func.sum(Transaction.amount)).scalar() or 0

                daily_withdrawals_count = Transaction.query.filter(
                    Transaction.employee_id == salesman.employee_id,
                    Transaction.transaction_types == TransactionType.RETIRO,
                    Transaction.approval_status == ApprovalStatus.APROBADA,
                    func.date(Transaction.creation_date) == filter_date
                ).count() or 0

                # Calcula las colecciones diarias basadas en transacciones de INGRESO
                daily_collection = Transaction.query.filter(
                    Transaction.employee_id == salesman.employee_id,
                    Transaction.transaction_types == TransactionType.INGRESO,
                    Transaction.approval_status == ApprovalStatus.APROBADA,
                    func.date(Transaction.creation_date) == filter_date
                ).with_entities(func.sum(Transaction.amount)).scalar() or 0

                daily_collection_count = Transaction.query.filter(
                    Transaction.employee_id == salesman.employee_id,
                    Transaction.transaction_types == TransactionType.INGRESO,
                    Transaction.approval_status == ApprovalStatus.APROBADA,
                    func.date(Transaction.creation_date) == filter_date
                ).count() or 0

            # Obtener detalles de gastos, ingresos y retiros asociados a ese vendedor y ordenar por fecha de creación descendente
            transactions = Transaction.query.filter_by(
                employee_id=employee_id).order_by(Transaction.creation_date.desc()).all()

            # Filtrar transacciones por tipo y fecha filtrada
            expenses = [trans for trans in transactions if
                        trans.transaction_types == TransactionType.GASTO and trans.approval_status == ApprovalStatus.APROBADA and trans.creation_date.date() == filter_date]
            incomes = [trans for trans in transactions if
                       trans.transaction_types == TransactionType.INGRESO and trans.approval_status == ApprovalStatus.APROBADA and trans.creation_date.date() == filter_date]
            withdrawals = [trans for trans in transactions if
                           trans.transaction_types == TransactionType.RETIRO and trans.approval_status == ApprovalStatus.APROBADA and trans.creation_date.date() == filter_date]

            # Recopilar detalles con formato de fecha y clases de Bootstrap
            expense_details = [
                {'description': trans.description, 'amount': trans.amount, 'approval_status': trans.approval_status.name,
                 'attachment': trans.attachment, 'date': trans.creation_date.strftime('%d/%m/%Y')} for trans in expenses]
            income_details = [
                {'description': trans.description, 'amount': trans.amount, 'approval_status': trans.approval_status.name,
                 'attachment': trans.attachment, 'date': trans.creation_date.strftime('%d/%m/%Y'), 'employee_id': employee_id, 'username': Employee.query.get(employee_id).user.username} for trans in incomes]
            withdrawal_details = [
                {'description': trans.description, 'amount': trans.amount, 'approval_status': trans.approval_status.name,
                 'attachment': trans.attachment, 'date': trans.creation_date.strftime('%d/%m/%Y'), 'employee_id': employee_id, 'username': Employee.query.get(employee_id).user.username} for trans in withdrawals]

            # Número total de clientes del vendedor
            total_customers = sum(
                1 for client in salesman.employee.clients
                for loan in client.loans
                if loan.status
            )

            # Clientes morosos para la fecha filtrada
            customers_in_arrears = sum(
                1 for client in salesman.employee.clients
                for loan in client.loans
                if loan.status and any(
                    installment.status == InstallmentStatus.MORA
                    for installment in loan.installments
                )
            )

            # Crear subconsulta para obtener los IDs de los clientes
            client_subquery = db.session.query(Client.id).filter(
                Client.employee_id == employee_id).subquery()

            # Crear subconsulta para obtener los IDs de los préstamos
            loan_subquery = db.session.query(Loan.id).filter(
                Loan.client_id.in_(client_subquery.select())).subquery()

            # Crear subconsulta para contar los préstamos únicos
            subquery = db.session.query(
                Loan.id
            ).join(
                LoanInstallment, LoanInstallment.loan_id == Loan.id
            ).join(
                Payment, Payment.installment_id == LoanInstallment.id
            ).filter(
                Loan.id.in_(loan_subquery.select()),
                func.date(Payment.payment_date) == filter_date,
                LoanInstallment.status.in_(['PAGADA', 'ABONADA'])
            ).group_by(
                Loan.id
            ).subquery()

            # Contar el número de préstamos únicos
            total_clients_collected = db.session.query(
                func.count()
            ).select_from(
                subquery
            ).scalar() or 0

            # Obtener el estado del modelo Employee
            employee_status = salesman.employee.status

            status_box = ""

            if employee_status == False and all_loans_paid_today == True:
                status_box = "Cerrada"
            elif employee_status == False and all_loans_paid_today == False:
                status_box = "Desactivada"
            elif employee_status == True and all_loans_paid_today == False:
                status_box = "Activa"
            else:
                status_box = "Activa"

            # box_value ya se asignó arriba si existe registro, solo calcular si no existe
            if not employee_records:
                # Si no existe registro, calcular box_value
                box_value = initial_box_value + float(total_collections_today) - float(daily_withdrawals) - float(
                    daily_expenses_amount) + float(daily_collection) - float(new_clients_loan_amount) - float(total_renewal_loans_amount)

            salesman_data = {
                'salesman_name': f'{salesman.employee.user.first_name} {salesman.employee.user.last_name}',
                'employee_id': salesman.employee_id,
                'employee_status': employee_status,
                'total_collections_today': total_collections_today,
                'new_clients': new_clients,
                'daily_expenses': daily_expenses_count,
                'daily_expenses_amount': daily_expenses_amount,
                'daily_withdrawals': daily_withdrawals,
                'daily_collections_made': daily_collection,
                'total_number_of_customers': total_customers,
                'customers_in_arrears_for_the_day': customers_in_arrears,
                'total_renewal_loans': total_renewal_loans,
                'total_new_clients_loan_amount': new_clients_loan_amount,
                'total_renewal_loans_amount': total_renewal_loans_amount,
                'daily_withdrawals_count': daily_withdrawals_count,
                'daily_collection_count': daily_collection_count,
                'total_pending_installments_amount': total_pending_installments_amount,
                'all_loans_paid_today': all_loans_paid_today,
                'total_clients_collected': total_clients_collected,
                'status_box': status_box,
                'box_value': box_value,
                'initial_box_value': initial_box_value,
                'expense_details': expense_details,
                'income_details': income_details,
                'withdrawal_details': withdrawal_details,
                'role_employee': role_employee,
                'total_pending_installments_loan_close_amount': total_pending_installments_loan_close_amount
            }

            salesmen_stats.append(salesman_data)

        # Obtener el término de búsqueda
        search_term = request.args.get('salesman_name')
        all_boxes_closed = all(
            salesman_data['status_box'] == 'Cerrada' for salesman_data in salesmen_stats)

        # Inicializar search_term como cadena vacía si es None
        search_term = search_term if search_term else ""

        # Realizar la búsqueda en la lista de salesmen_stats si hay un término de búsqueda
        if search_term:
            salesmen_stats = [salesman for salesman in salesmen_stats if
                              search_term.lower() in salesman['salesman_name'].lower()]

        # Obtener los gastos del sub-administrador para la fecha filtrada
        expenses = Transaction.query.filter(
            Transaction.employee_id == sub_admin_employee.id,
            Transaction.transaction_types == 'GASTO',
            func.date(Transaction.creation_date) == filter_date
        ).all()

        # Obtener el valor total de los gastos
        total_expenses = sum(expense.amount for expense in expenses)

        expense_details = [
            {'description': trans.description, 'amount': trans.amount, 'approval_status': trans.approval_status.name,
             'attachment': trans.attachment, 'date': trans.creation_date.strftime('%d/%m/%Y')} for trans in expenses]

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
        return render_template('history-box.html', coordinator_box=sub_admin_box, salesmen_stats=salesmen_stats,
                               search_term=search_term, all_boxes_closed=all_boxes_closed,
                               coordinator_name=sub_admin_name, user_id=user_id, expense_details=expense_details, 
                               total_expenses=total_expenses, filter_date=filter_date, manager_id=manager_id)
    except Exception as e:
        return jsonify({'message': 'Error interno del servidor', 'error': str(e)}), 500


