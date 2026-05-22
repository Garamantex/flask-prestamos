# app/routes/clients.py
# Gestión de clientes y préstamos

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

@routes.route('/create-client/<int:user_id>', methods=['GET', 'POST'])
def create_client(user_id):
    try:
        employee = Employee.query.filter_by(user_id=user_id).first()
        role = session.get('role')

        if not employee or not (role == Role.COORDINADOR.value or role == Role.VENDEDOR.value):
            return redirect(url_for('routes.menu_salesman'))

        if request.method == 'POST':
            # Recopilar datos del formulario POST
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            alias = request.form.get('alias')
            document = request.form.get('document')
            cellphone = request.form.get('cellphone')
            address = request.form.get('address')
            neighborhood = request.form.get('neighborhood')
            amount = request.form.get('amount')
            dues = request.form.get('dues')
            interest = request.form.get('interest')
            payment = request.form.get('amountPerPay')

            # Validar que los campos obligatorios no estén vacíos
            if not first_name or not last_name or not document or not cellphone:
                raise Exception(
                    "Error: Los campos obligatorios deben estar completos.")

            # Verificar si el DNI ya existe
            existing_client = Client.query.filter_by(document=document).first()
            if existing_client:
                flash('El DNI ingresado ya está registrado. Por favor, use un DNI diferente.', 'error')
                return render_template('create-client.html', user_id=user_id)

            # Crear una instancia del cliente con los datos proporcionados
            client = Client(
                first_name=first_name,
                last_name=last_name,
                alias=alias,
                document=document,
                cellphone=cellphone,
                address=address,
                neighborhood=neighborhood,
                employee_id=employee.id
            )

            # Guardar el cliente en la base de datos
            db.session.add(client)
            db.session.commit()

            # Obtener el ID del cliente recién creado
            client_id = client.id

            # Obtener maximum_sale del empleado
            maximum_sale = employee.maximum_sale
            approved = float(amount) <= maximum_sale

            # Descuento del valor del préstamo al box_value del vendedor
            employee.box_value -= Decimal(amount)
            db.session.commit()

            # Crear una instancia del préstamo con los datos proporcionados
            loan = Loan(
                amount=amount,
                dues=dues,
                interest=interest,
                payment=payment,
                status=True,
                approved=approved,
                up_to_date=False,
                client_id=client_id,
                employee_id=employee.id
            )

            # Guardar el préstamo en la base de datos
            db.session.add(loan)
            db.session.commit()

            current_date = datetime.now()
            filename = ""
            # Usar el employee_id obtenido para crear la transacción
            if not approved:
                transaction = Transaction(
                    transaction_types="INGRESO",
                    concept_id=14,
                    description="Solicitud Prestamo NO APROBADO",
                    amount=float(amount),
                    attachment=filename,  # Usar el nombre único del archivo
                    approval_status="PENDIENTE",
                    employee_id=employee.id,
                    loan_id=loan.id,
                    creation_date=current_date
                )

                db.session.add(transaction)
                db.session.commit()

            flash('Préstamo creado exitosamente', 'success')
            return redirect(url_for('routes.credit_detail', id=loan.id))

        return render_template('create-client.html', user_id=user_id)
    except Exception as e:
        # Manejo de excepciones: mostrar un mensaje de error y registrar la excepción
        error_message = str(e)
        return render_template('error.html', error_message=error_message), 500


@routes.route('/edit-client/<int:client_id>', methods=['GET', 'POST'])
def edit_client(client_id):
    try:
        # Verificar que el usuario tenga permisos y sea coordinador
        if 'user_id' in session and session['role'] == Role.VENDEDOR.value:
            client = Client.query.get(client_id)

            if not client:
                raise Exception("Error: Cliente no encontrado.")

            if request.method == 'POST':
                # Recopilar datos del formulario POST
                first_name = request.form.get('first_name')
                last_name = request.form.get('last_name')
                alias = request.form.get('alias')
                document = request.form.get('document')
                cellphone = request.form.get('cellphone')
                address = request.form.get('address')
                neighborhood = request.form.get('neighborhood')

                # Validar que los campos obligatorios no estén vacíos
                if not first_name or not last_name or not document or not cellphone:
                    raise Exception(
                        "Error: Los campos obligatorios deben estar completos.")

                # Actualizar los datos del cliente
                client.first_name = first_name
                client.last_name = last_name
                client.alias = alias
                client.document = document
                client.cellphone = cellphone
                client.address = address
                client.neighborhood = neighborhood

                # Guardar los cambios en la base de datos
                db.session.commit()

                return redirect(url_for('routes.client_list'))

            return render_template('edit-client.html', client=client)
        else:
            return redirect(url_for('routes.menu_salesman'))
    except Exception as e:
        # Manejo de excepciones: mostrar un mensaje de error y registrar la excepción
        error_message = str(e)
        return render_template('error.html', error_message=error_message), 500


@routes.route('/client-list/<int:user_id>', methods=['GET', 'POST'])
def client_list(user_id):
    user_id = user_id
    user = User.query.get(user_id)
    role = user.role.value
    if user and (user.role.value == Role.COORDINADOR.value or user.role.value == Role.VENDEDOR.value):
        employee = Employee.query.filter_by(user_id=user_id).first()

        if employee is None:
            return "Error: No se encontró el empleado correspondiente al usuario."

        # Obtener la lista de clientes asociados al empleado actual que tienen préstamos en estado diferente de Falso
        if session['role'] == Role.COORDINADOR.value:
            clients_query = Client.query.filter_by(
                employee_id=employee.id).join(Loan).filter(Loan.status != False)
        else:  # Si es vendedor, obtener solo los clientes asociados al vendedor con préstamos en estado diferente de Falso
            clients_query = Client.query.join(Loan).filter(
                Loan.employee_id == employee.id, Loan.status != False)

        # Manejar la búsqueda
        search_term = request.form.get('search')
        if search_term:
            clients_query = clients_query.filter(
                (Client.first_name.ilike(f'%{search_term}%')) |
                (Client.last_name.ilike(f'%{search_term}%')) |
                (Client.alias.ilike(f'%{search_term}%')) |
                (Client.document.ilike(f'%{search_term}%'))
            )

        clients = clients_query.all()

        return render_template('client-list.html', client_list=clients, user_id=user_id)
    else:
        return redirect(url_for('routes.menu_salesman', user_id=user_id))


@routes.route('/renewal', methods=['GET', 'POST'])
def renewal():
    if 'user_id' in session and (session['role'] == Role.COORDINADOR.value or session['role'] == Role.VENDEDOR.value):
        user_id = session['user_id']
        employee = Employee.query.filter_by(user_id=user_id).first()

        if employee is None:
            return "Error: No se encontró el empleado correspondiente al usuario."

        if request.method == 'POST':
            # Obtener el número de documento del cliente seleccionado en el formulario
            document_number = request.form.get('document_number')

            if not document_number:
                return "Error: No se seleccionó un cliente."

            # Buscar el cliente por su número de documento
            selected_client = Client.query.filter_by(
                document=document_number).first()

            if selected_client is None:
                return "Error: No se encontró el cliente."

            # Verificar si el cliente tiene préstamos activos
            active_loans = Loan.query.filter_by(
                client_id=selected_client.id, status=True).count()

            if active_loans > 0:
                return "Error: El cliente ya tiene préstamos activos y no puede realizar una renovación."

            # Obtener los valores máximos permitidos para el empleado
            maximum_sale = employee.maximum_sale
            maximum_installments = employee.maximum_installments
            minimum_interest = employee.minimum_interest

            # Obtener los datos del formulario
            amount = float(request.form.get('amount'))
            dues = float(request.form.get('dues'))
            interest = float(request.form.get('interest'))
            payment = float(request.form.get('amount'))

            # Verificar que los valores ingresados no superen los máximos permitidos
            if amount > maximum_sale or dues > maximum_installments or interest < minimum_interest:
                return "Error: Los valores ingresados superan los máximos permitidos."

            # Crear la instancia de renovación de préstamo
            renewal_loan = Loan(
                amount=amount,
                dues=dues,
                interest=interest,
                payment=payment,
                status=True,
                up_to_date=False,
                is_renewal=True,
                client_id=selected_client.id,
                employee_id=employee.id
            )

            # Descontar el valor del loan del box_value del modelo employee
            employee.box_value -= Decimal(renewal_loan.amount)

            # Guardar la renovación de préstamo en la base de datos
            db.session.add(renewal_loan)
            db.session.commit()

            return redirect(url_for('routes.credit_detail', id=renewal_loan.id))

        # Crear una lista de tuplas con los nombres y apellidos de los clientes para mostrar en el formulario
        if session['role'] == Role.COORDINADOR.value:
            # Para el coordinador, mostrar todos los clientes sin préstamos activos que pertenecen a su equipo
            clients = Client.query.filter(
                Client.employee_id == employee.id,
                ~Client.loans.any(Loan.status == True)
            ).all()
        else:
            # Para el vendedor, mostrar solo sus clientes sin préstamos activos
            clients = Client.query.filter(
                Client.employee_id == employee.id,
                ~Client.loans.any(Loan.status == True)
            ).all()

        client_data = [
            (client.document, f"{client.first_name} {client.last_name}") for client in clients]

        return render_template('renewal.html', clients=client_data, user_id=user_id)
    else:
        return redirect(url_for('routes.menu_salesman', user_id=session['user_id']))


@routes.route('/credit-detail/<int:id>')
def credit_detail(id):
    try:
        loan = Loan.query.get(id)
        if not loan:
            flash('Préstamo no encontrado', 'error')
            return redirect(url_for('routes.menu_salesman', user_id=session.get('user_id')))
        
        client = Client.query.get(loan.client_id)
        if not client:
            flash('Cliente no encontrado', 'error')
            return redirect(url_for('routes.menu_salesman', user_id=session.get('user_id')))
        
        installments = LoanInstallment.query.filter_by(loan_id=loan.id).all()
        payments = Payment.query.join(LoanInstallment).filter(
            LoanInstallment.loan_id == loan.id).all()

        # Verificar si ya se generaron las cuotas del préstamo
        if not installments and loan.approved == 1:
            generate_loan_installments(loan)
            installments = LoanInstallment.query.filter_by(loan_id=loan.id).all()

        loans = Loan.query.all()  # Obtener todos los créditos
        loan_detail = get_loan_details(id)

        # Agrupar pagos por fecha y hora, y calcular el total pagado en cada fecha/hora
        payments_by_datetime = {}
        for payment in payments:
            # Solo incluir pagos mayores a 0
            if float(payment.amount) > 0:
                payment_datetime = payment.payment_date
                if payment_datetime not in payments_by_datetime:
                    payments_by_datetime[payment_datetime] = {
                        'datetime': payment_datetime,
                        'date': payment_datetime.date(),
                        'time': payment_datetime.time(),
                        'total_amount': 0
                    }
                payments_by_datetime[payment_datetime]['total_amount'] += float(payment.amount)

        # Ordenar por fecha y hora (más reciente primero)
        payments_by_datetime = dict(sorted(payments_by_datetime.items(), reverse=True))

        # Verificar si el préstamo tiene pagos registrados para mostrar/ocultar el botón de eliminar
        has_payments = db.session.query(Payment.id).join(
            LoanInstallment, Payment.installment_id == LoanInstallment.id
        ).filter(
            LoanInstallment.loan_id == loan.id
        ).first() is not None

        return render_template('credit-detail.html', loans=loans, loan=loan, client=client, installments=installments,
                               loan_detail=loan_detail, payments=payments, payments_by_datetime=payments_by_datetime, 
                               user_id=session['user_id'], has_payments=has_payments)
    except Exception as e:
        # Manejo de excepciones: mostrar un mensaje de error y registrar la excepción
        flash(f'Error al cargar el detalle del préstamo: {str(e)}', 'error')
        return redirect(url_for('routes.menu_salesman', user_id=session.get('user_id')))


@routes.route('/modify-installments/<int:loan_id>', methods=['POST'])
def modify_installments(loan_id):
    loan = Loan.query.get(loan_id)
    installments = LoanInstallment.query.filter_by(loan_id=loan.id).all()

    for installment in installments:
        installment_id = installment.id
        new_status = request.form.get(f'estado_cuota_{installment_id}')

        # Verificar si el estado seleccionado es válido
        if new_status in [status.value for status in InstallmentStatus]:
            # Actualizar el estado de la cuota
            installment.status = InstallmentStatus(new_status)

            # Actualizar la fecha de pago a la fecha actual
            if installment.status == InstallmentStatus.PAGADA:
                installment.payment_date = dt.now()  # Corrección

    # Guardar los cambios en la base de datos
    db.session.commit()

    # Verificar si hay cuotas en estado "MORA"
    mora_installments = LoanInstallment.query.filter_by(
        loan_id=loan.id, status=InstallmentStatus.MORA).count()
    if mora_installments > 0:
        # El cliente está en mora, cambiar el estado a True
        client = Client.query.get(loan.client_id)
        client.debtor = True
    else:
        # No hay cuotas en estado "MORA", cambiar el estado a False
        client = Client.query.get(loan.client_id)
        client.debtor = False
    db.session.commit()

    # Verificar si el cliente ya no tiene más cuotas pendientes del préstamo
    pending_installments = LoanInstallment.query.filter_by(
        loan_id=loan.id, status=InstallmentStatus.PENDIENTE).count()
    if pending_installments == 0:
        loan.status = False
        db.session.commit()

    return redirect(url_for('routes.credit_detail', id=loan_id))



@routes.route('/api/check-dni/<dni>', methods=['GET'])
def check_dni(dni):
    """Verificar si un DNI ya existe en la base de datos"""
    try:
        # Buscar si existe un cliente con ese DNI
        existing_client = Client.query.filter_by(document=dni).first()
        
        if existing_client:
            return jsonify({
                'exists': True,
                'message': 'Este DNI ya está registrado'
            }), 200
        else:
            return jsonify({
                'exists': False,
                'message': 'DNI disponible'
            }), 200
    except Exception as e:
        return jsonify({
            'error': 'Error al verificar el DNI',
            'message': str(e)
        }), 500



@routes.route('/cancel_loan/<int:loan_id>', methods=['PUT'])
def cancel_loan(loan_id):
    # Buscar el préstamo
    loan = Loan.query.get(loan_id)
    
    if not loan:
        return jsonify({'error': 'Préstamo no encontrado'}), 404

    # Obtener todas las cuotas del préstamo
    installments = LoanInstallment.query.filter_by(loan_id=loan_id).all()

    # Obtener el cliente asociado al préstamo
    client = Client.query.get(loan.client_id)
    client_name = f"{client.first_name} {client.last_name}"

    # Obtener el empleado asociado al préstamo
    employee = Employee.query.get(loan.employee_id)
    
    # Verificar si hay pagos registrados para este préstamo
    has_payments = db.session.query(Payment.id).join(
        LoanInstallment, Payment.installment_id == LoanInstallment.id
    ).filter(
        LoanInstallment.loan_id == loan_id
    ).first() is not None
    
    # Reintegrar el monto del préstamo al box_value solo si NO hay pagos registrados
    # NO se crea un registro de Payment para que NO aparezca en el recaudo del día
    # Solo se actualiza el valor de la caja que se vio afectado por la creación del préstamo
    if not has_payments:
        employee.box_value += Decimal(str(loan.amount))

    # Actualizar cada cuota a 0
    for installment in installments:
        installment.amount = 0

    # Desactivar el préstamo
    loan.status = False
    loan.modification_date = datetime.now()

    # Guardar cambios en la base de datos
    db.session.commit()

    return jsonify({'message': f'Préstamo {client_name} cancelado correctamente'}), 200





@routes.route('/loan-management', methods=['GET', 'POST'])
def loan_management():
    """Vista principal para gestión de préstamos por coordinadores"""
    try:
        # Validar acceso del coordinador
        user_id, user = validate_coordinator_access()
        
        # Obtener datos del coordinador
        coordinator, coordinator_cash, coordinator_name, manager_id, salesmen = get_coordinator_data(user_id)
        
        # Obtener employee_ids de todos los vendedores subordinados (incluyendo subcoordinadores)
        all_salesmen_ids = []
        for salesman_tuple in salesmen:
            salesman_obj = salesman_tuple[0]
            all_salesmen_ids.append(salesman_obj.employee_id)
        
        # Obtener todos los préstamos de los vendedores subordinados
        loans_query = db.session.query(Loan, Client, Employee, User)\
            .join(Client, Loan.client_id == Client.id)\
            .join(Employee, Loan.employee_id == Employee.id)\
            .join(User, Employee.user_id == User.id)\
            .filter(Loan.employee_id.in_(all_salesmen_ids))
        
        # Búsqueda y filtros
        search_term = request.args.get('search', '').strip()
        filter_salesman = request.args.get('salesman', type=int)
        filter_status = request.args.get('status', '')
        
        if search_term:
            loans_query = loans_query.filter(
                db.or_(
                    Client.first_name.ilike(f'%{search_term}%'),
                    Client.last_name.ilike(f'%{search_term}%'),
                    Client.document.ilike(f'%{search_term}%')
                )
            )
        
        if filter_salesman:
            loans_query = loans_query.filter(Loan.employee_id == filter_salesman)
        
        if filter_status == 'active':
            loans_query = loans_query.filter(Loan.status == True)
        elif filter_status == 'inactive':
            loans_query = loans_query.filter(Loan.status == False)
        
        loans = loans_query.order_by(Loan.creation_date.desc()).all()
        
        # Preparar datos para la plantilla
        loans_data = []
        for loan, client, employee, user in loans:
            # Calcular saldo pendiente
            total_paid = db.session.query(func.sum(Payment.amount))\
                .join(LoanInstallment, Payment.installment_id == LoanInstallment.id)\
                .filter(LoanInstallment.loan_id == loan.id)\
                .scalar() or Decimal('0')
            
            total_amount = loan.amount + (loan.amount * loan.interest / 100)
            pending_balance = total_amount - total_paid
            
            loans_data.append({
                'loan': loan,
                'client': client,
                'employee': employee,
                'user': user,
                'pending_balance': float(pending_balance),
                'total_paid': float(total_paid)
            })
        
        # Preparar lista de vendedores para el filtro
        salesmen_list = [
            {
                'employee_id': salesman_tuple[0].employee_id,
                'name': f"{salesman_tuple[2].first_name} {salesman_tuple[2].last_name}"
            }
            for salesman_tuple in salesmen
        ]
        
        return render_template('loan-management.html',
                             loans_data=loans_data,
                             salesmen_list=salesmen_list,
                             coordinator_name=coordinator_name,
                             user_id=user_id,
                             search_term=search_term,
                             filter_salesman=filter_salesman,
                             filter_status=filter_status)
    
    except ValueError as e:
        return jsonify({'message': str(e)}), 401 if 'Usuario no encontrado' in str(e) else 403
    except Exception as e:
        return jsonify({'message': 'Error interno del servidor', 'error': str(e)}), 500


@routes.route('/edit-loan/<int:loan_id>', methods=['GET', 'POST'])
def edit_loan(loan_id):
    """Endpoint para editar préstamos existentes"""
    try:
        # Validar acceso del coordinador
        user_id, user = validate_coordinator_access()
        
        # Obtener datos del coordinador
        coordinator, coordinator_cash, coordinator_name, manager_id, salesmen = get_coordinator_data(user_id)
        
        # Obtener employee_ids de todos los vendedores subordinados
        all_salesmen_ids = []
        for salesman_tuple in salesmen:
            salesman_obj = salesman_tuple[0]
            all_salesmen_ids.append(salesman_obj.employee_id)
        
        # Obtener el préstamo
        loan = Loan.query.get(loan_id)
        if not loan:
            flash('Préstamo no encontrado', 'error')
            return redirect(url_for('routes.loan_management'))
        
        # Validar que el préstamo pertenezca a un vendedor del coordinador
        if loan.employee_id not in all_salesmen_ids:
            flash('No tiene permisos para editar este préstamo', 'error')
            return redirect(url_for('routes.loan_management'))
        
        # Obtener cliente y empleado
        client = Client.query.get(loan.client_id)
        employee = Employee.query.get(loan.employee_id)
        
        if request.method == 'POST':
            # Obtener datos del formulario
            new_amount = Decimal(request.form.get('amount'))
            new_dues = int(request.form.get('dues'))
            new_interest = Decimal(request.form.get('interest'))
            
            # Calcular diferencia en el monto para actualizar box_value
            amount_difference = new_amount - loan.amount
            
            # Actualizar box_value del vendedor
            if amount_difference != 0:
                employee.box_value -= amount_difference
                db.session.add(employee)
            
            # Actualizar parámetros del préstamo
            loan.amount = new_amount
            loan.dues = new_dues
            loan.interest = new_interest
            loan.modification_date = datetime.now()
            
            # Recalcular cuotas
            recalculate_loan_installments(loan, new_amount, new_dues, new_interest)
            
            # Actualizar cuotas individuales si se proporcionaron
            installments = LoanInstallment.query.filter_by(loan_id=loan.id)\
                .order_by(LoanInstallment.installment_number.asc()).all()
            
            for installment in installments:
                installment_key = f'installment_{installment.id}'
                new_amount_inst = request.form.get(f'{installment_key}_amount')
                new_due_date = request.form.get(f'{installment_key}_due_date')
                
                if new_amount_inst:
                    new_amount_value = Decimal(new_amount_inst)
                    old_amount = installment.amount
                    
                    # Obtener el total pagado actual antes de la modificación
                    total_paid_before = db.session.query(func.sum(Payment.amount)).filter(
                        Payment.installment_id == installment.id
                    ).scalar() or Decimal('0')
                    
                    # Calcular el nuevo total que debería estar pagado basado en el nuevo monto pendiente
                    new_total_paid_expected = installment.fixed_amount - new_amount_value
                    
                    # Calcular la diferencia entre lo que debería estar pagado y lo que está pagado
                    payment_difference = new_total_paid_expected - total_paid_before
                    
                    if payment_difference > 0:
                        # Se necesita agregar un pago (el monto pendiente se redujo)
                        # Crear un nuevo Payment con la diferencia
                        payment = Payment(
                            amount=payment_difference,
                            payment_date=loan.modification_date,
                            installment_id=installment.id
                        )
                        db.session.add(payment)
                    elif payment_difference < 0:
                        # El monto pendiente aumentó (ajuste manual hacia atrás)
                        # Esto es raro pero podría pasar, no creamos un Payment negativo
                        # Solo actualizamos el monto
                        pass
                    
                    # Actualizar el monto pendiente de la cuota
                    installment.amount = new_amount_value
                    
                    # Recalcular estado basado en el nuevo monto y pagos
                    # Usar flush para asegurar que el Payment se guarde antes de consultar
                    db.session.flush()
                    total_paid_after = db.session.query(func.sum(Payment.amount)).filter(
                        Payment.installment_id == installment.id
                    ).scalar() or Decimal('0')
                    
                    if installment.amount <= 0:
                        installment.status = InstallmentStatus.PAGADA
                        installment.amount = Decimal('0')
                        if not installment.payment_date:
                            installment.payment_date = loan.modification_date.date()
                    elif total_paid_after > 0 and total_paid_after < installment.fixed_amount:
                        installment.status = InstallmentStatus.ABONADA
                    else:
                        installment.status = InstallmentStatus.PENDIENTE
                
                if new_due_date:
                    installment.due_date = datetime.strptime(new_due_date, '%Y-%m-%d').date()
            
            # Actualizar el estado del préstamo después de los cambios
            remaining_outstanding = sum(
                inst.amount for inst in installments
                if inst.status in [InstallmentStatus.PENDIENTE, InstallmentStatus.ABONADA, InstallmentStatus.MORA]
                and inst.amount > 0
            )
            
            if remaining_outstanding == 0:
                loan.status = False
                loan.up_to_date = True
            else:
                loan.status = True
                loan.up_to_date = False
            
            db.session.commit()
            flash('Préstamo actualizado correctamente', 'success')
            return redirect(url_for('routes.loan_management'))
        
        # GET: Mostrar formulario de edición
        installments = LoanInstallment.query.filter_by(loan_id=loan.id)\
            .order_by(LoanInstallment.installment_number.asc()).all()
        
        # Calcular información adicional
        total_paid = db.session.query(func.sum(Payment.amount))\
            .join(LoanInstallment, Payment.installment_id == LoanInstallment.id)\
            .filter(LoanInstallment.loan_id == loan.id)\
            .scalar() or Decimal('0')
        
        total_amount = loan.amount + (loan.amount * loan.interest / 100)
        pending_balance = total_amount - total_paid
        
        return render_template('edit-loan.html',
                             loan=loan,
                             client=client,
                             employee=employee,
                             installments=installments,
                             total_paid=float(total_paid),
                             pending_balance=float(pending_balance),
                             coordinator_name=coordinator_name,
                             user_id=user_id)
    
    except ValueError as e:
        return jsonify({'message': str(e)}), 401 if 'Usuario no encontrado' in str(e) else 403
    except Exception as e:
        flash(f'Error al editar préstamo: {str(e)}', 'error')
        return redirect(url_for('routes.loan_management'))


@routes.route('/create-custom-loan', methods=['GET', 'POST'])
def create_custom_loan():
    """Endpoint para crear préstamos personalizados con fecha de inicio anterior"""
    try:
        # Validar acceso del coordinador
        user_id, user = validate_coordinator_access()
        
        # Obtener datos del coordinador
        coordinator, coordinator_cash, coordinator_name, manager_id, salesmen = get_coordinator_data(user_id)
        
        if request.method == 'POST':
            # Obtener datos del formulario
            employee_id = int(request.form.get('employee_id'))
            amount = Decimal(request.form.get('amount'))
            dues = int(request.form.get('dues'))
            interest = Decimal(request.form.get('interest'))
            payment = Decimal(request.form.get('payment', amount))
            start_date_str = request.form.get('start_date')
            advance_amount = Decimal(request.form.get('advance_amount', 0))
            
            # Validar que el empleado sea un vendedor subordinado
            all_salesmen_ids = []
            for salesman_tuple in salesmen:
                salesman_obj = salesman_tuple[0]
                all_salesmen_ids.append(salesman_obj.employee_id)
            
            if employee_id not in all_salesmen_ids:
                flash('El empleado seleccionado no es un vendedor subordinado', 'error')
                return redirect(url_for('routes.create_custom_loan'))
            
            # Verificar si se está creando un cliente nuevo o usando uno existente
            create_new_client = request.form.get('create_new_client') == 'true'
            
            if create_new_client:
                # Crear nuevo cliente
                first_name = request.form.get('client_first_name')
                last_name = request.form.get('client_last_name')
                alias = request.form.get('client_alias', '')
                document = request.form.get('client_document')
                cellphone = request.form.get('client_cellphone')
                address = request.form.get('client_address', '')
                neighborhood = request.form.get('client_neighborhood', '')
                
                # Validar campos obligatorios
                if not first_name or not last_name or not document or not cellphone:
                    flash('Los campos obligatorios del cliente deben estar completos', 'error')
                    return redirect(url_for('routes.create_custom_loan'))
                
                # Verificar si el DNI ya existe
                existing_client = Client.query.filter_by(document=document).first()
                if existing_client:
                    flash('El DNI ingresado ya está registrado. Por favor, use un DNI diferente.', 'error')
                    return redirect(url_for('routes.create_custom_loan'))
                
                # Crear el cliente
                client = Client(
                    first_name=first_name,
                    last_name=last_name,
                    alias=alias,
                    document=document,
                    cellphone=cellphone,
                    address=address,
                    neighborhood=neighborhood,
                    employee_id=employee_id
                )
                
                db.session.add(client)
                db.session.commit()
                client_id = client.id
            else:
                # Usar cliente existente
                client_id = int(request.form.get('client_id'))
                client = Client.query.get(client_id)
                if not client:
                    flash('Cliente no encontrado', 'error')
                    return redirect(url_for('routes.create_custom_loan'))
            
            employee = Employee.query.get(employee_id)
            if not employee:
                flash('Empleado no encontrado', 'error')
                return redirect(url_for('routes.create_custom_loan'))
            
            # Parsear fecha de inicio
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            current_date = datetime.now().date()
            
            # Validar que la fecha de inicio no sea futura
            if start_date > current_date:
                flash('La fecha de inicio no puede ser futura', 'error')
                return redirect(url_for('routes.create_custom_loan'))
            
            # Crear el préstamo
            loan = Loan(
                amount=amount,
                dues=dues,
                interest=interest,
                payment=payment,
                status=True,
                approved=True,
                up_to_date=False,
                client_id=client_id,
                employee_id=employee_id,
                creation_date=datetime.combine(start_date, datetime.min.time())
            )
            
            db.session.add(loan)
            db.session.commit()
            
            # Generar cuotas
            generate_loan_installments(loan)
            
            # Si hay monto abonado, distribuirlo entre las cuotas
            if advance_amount > 0:
                distribute_advance_payment(loan, start_date, advance_amount, current_date)
            
            # Actualizar box_value del vendedor (descontar el monto del préstamo)
            employee.box_value -= amount
            db.session.add(employee)
            db.session.commit()
            
            flash('Préstamo personalizado creado exitosamente', 'success')
            return redirect(url_for('routes.loan_management'))
        
        # GET: Mostrar formulario de creación
        # Obtener lista de vendedores subordinados
        salesmen_list = []
        for salesman_tuple in salesmen:
            salesman_obj = salesman_tuple[0]
            employee_obj = salesman_tuple[1]
            user_obj = salesman_tuple[2]
            salesmen_list.append({
                'employee_id': salesman_obj.employee_id,
                'name': f"{user_obj.first_name} {user_obj.last_name}",
                'employee': employee_obj
            })
        
        # Obtener todos los clientes de los vendedores subordinados
        all_salesmen_ids = [s['employee_id'] for s in salesmen_list]
        clients = Client.query.filter(Client.employee_id.in_(all_salesmen_ids)).all()
        
        current_date = datetime.now().date()
        
        return render_template('create-custom-loan.html',
                             salesmen_list=salesmen_list,
                             clients=clients,
                             coordinator_name=coordinator_name,
                             user_id=user_id,
                             current_date=current_date)
    
    except ValueError as e:
        return jsonify({'message': str(e)}), 401 if 'Usuario no encontrado' in str(e) else 403
    except Exception as e:
        flash(f'Error al crear préstamo personalizado: {str(e)}', 'error')
        return redirect(url_for('routes.create_custom_loan'))


