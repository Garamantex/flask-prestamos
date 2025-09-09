# Importaciones del módulo estándar de Python
from sqlalchemy import join
from flask import request, render_template, session, redirect, url_for
from datetime import datetime, date, timedelta
from decimal import Decimal
from datetime import timedelta, datetime as dt, date as dt_date
import os
import uuid
import holidays
from flask import send_file
import pandas as pd
import holidays
import io
from operator import and_
import holidays
from sqlalchemy import func
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, session, redirect, url_for, abort, request, jsonify

# Importaciones de tu aplicación (módulos locales)
from app.models import db, InstallmentStatus, Concept, Transaction, Role, Manager, Payment, Salesman, TransactionType, \
    ApprovalStatus, EmployeeRecord

# Importaciones de modelos y otros componentes específicos de tu aplicación
from .models import User, Client, Loan, Employee, LoanInstallment

# Crea una instancia de Blueprint
routes = Blueprint('routes', __name__)

# ruta para el logout de la aplicación web


@routes.route('/logout')
def logout():
    # Limpiar la sesión
    session.clear()
    return redirect(url_for('routes.home'))


# ruta para el home de la aplicación web
@routes.route('/', methods=['GET', 'POST'])
def home():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'ADMINISTRADOR' or role == 'COORDINADOR':
            return redirect(url_for('routes.menu_manager', user_id=session['user_id']))
        elif role == 'VENDEDOR':
            return redirect(url_for('routes.menu_salesman', user_id=session['user_id']))
        else:
            abort(403)  # Acceso no autorizado

    if request.method == 'POST':
        # Obtener los datos del formulario
        username = request.form.get('username')
        password = request.form.get('password')

        # Verificar las credenciales del usuario en la base de datos
        user = User.query.filter_by(
            username=username, password=password).first()

        if user:
            employee = '' if user.role.name == 'ADMINISTRADOR' else Employee.query.filter_by(
                user_id=user.id).first()
            status = 1 if user.role.name == 'ADMINISTRADOR' else employee.status
            if status == 1:
                # Guardar el usuario en la sesión
                session['user_id'] = user.id
                session['first_name'] = user.first_name
                session['last_name'] = user.last_name
                session['username'] = user.username
                # Guardar solo el nombre del rol
                session['role'] = user.role.name

                # Redireccionar según el rol del usuario
                if user.role.name == 'ADMINISTRADOR' or user.role.name == 'COORDINADOR':
                    return redirect(url_for('routes.menu_manager', user_id=user.id))
                elif user.role.name == 'VENDEDOR':
                    return redirect(url_for('routes.menu_salesman', user_id=user.id))
                else:
                    abort(403)  # Acceso no autorizado
            error_message = 'Caja Desactivada.'
            return render_template('index.html', error_message=error_message)
        error_message = 'Credenciales inválidas. Inténtalo nuevamente.'
        return render_template('index.html', error_message=error_message)

    return render_template('index.html')


# ruta para el menú del administrador
@routes.route('/menu-manager/<int:user_id>')
def menu_manager(user_id):
    # Verificar si el usuario está logueado es administrador o coordinador
    if 'user_id' not in session:
        return redirect(url_for('routes.home'))

    # Obtener la información del vendedor y créditos en mora
    manager_name = f"{session.get('first_name')} {session.get('last_name')}"

    # Verificar si el usuario es administrador o coordinador
    if session.get('role') != 'ADMINISTRADOR' and session.get('role') != 'COORDINADOR':
        abort(403)  # Acceso no autorizado

    # Mostrar el menú del administrador
    return render_template('menu-manager.html', manager_name=manager_name)


# ruta para el menú del vendedor


@routes.route('/menu-salesman/<int:user_id>')
def menu_salesman(user_id):
    # Verificar si el usuario está logueado
    if 'user_id' not in session:
        return redirect(url_for('routes.home'))

    # Obtener el employee_id a partir del user_id
    employee_id = Employee.query.filter_by(user_id=user_id).first().id

    # Obtener la información del vendedor y créditos en mora
    salesman_name = f"{session.get('first_name')} {session.get('last_name')}"

    # Obtener clientes morosos
    delinquent_clients = Client.query.filter_by(
        employee_id=employee_id,
        debtor=True
    ).count()

    # Obtener la cantidad total de créditos asociados al employee_id
    total_credits = Loan.query.filter_by(
        employee_id=employee_id,
        status=1
    ).distinct(Loan.client_id).count()

    # Recaudo realizado en el día (Ingresos del día)
    today_revenue = db.session.query(
        db.func.sum(Payment.amount)
    ).join(
        LoanInstallment, Payment.installment_id == LoanInstallment.id
    ).join(
        Loan, LoanInstallment.loan_id == Loan.id
    ).filter(
        Payment.payment_date == datetime.now(),
        Loan.employee_id == employee_id
    ).scalar() or 0

    # Si no hay recaudo, establecerlo como 0
    today_revenue = today_revenue or 0

    # Calcular el valor total en mora
    total_arrears_value = db.session.query(
        db.func.sum(LoanInstallment.amount)
    ).join(
        Loan
    ).filter(
        # Añadimos la condición de unión entre las tablas
        LoanInstallment.loan_id == Loan.id,
        Loan.employee_id == employee_id,
        LoanInstallment.status == InstallmentStatus.MORA
    ).scalar()

    # Si no hay valor en mora, establecerlo como 0
    total_arrears_value = total_arrears_value or 0

    # Mostrar el menú del vendedor y la información obtenida
    return render_template('menu-salesman.html', salesman_name=salesman_name,
                           delinquent_clients=delinquent_clients,
                           total_credits=total_credits,
                           today_revenue=today_revenue,
                           total_arrears_value=total_arrears_value,
                           employee_id=employee_id,
                           user_id=user_id)


@routes.route('/create-user', methods=['GET', 'POST'])
def create_user():
    user_id = session['user_id']
    if 'user_id' in session and (session['role'] == 'ADMINISTRADOR' or session['role'] == 'COORDINADOR'):
        # Verificar si el usuario es administrador o coordinador

        # Redirecciona a la página de lista de usuarios o a donde corresponda
        if request.method == 'POST':
            # Obtener los datos enviados en el formulario
            name = request.form['name']
            password = request.form['password']
            role = request.form['role']
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            cellphone = request.form['cellphone']
            box_value = 0
            maximum_cash = request.form['maximum_cash']
            maximum_sale = request.form['maximum_sale']
            maximum_expense = request.form['maximum_expense']
            maximum_installments = request.form['maximum_installments']
            minimum_interest = request.form['minimum_interest']
            percentage_interest = request.form['percentage_interest']
            fix_value = request.form['fix_value']

            # Crea un nuevo objeto User con los datos proporcionados
            user = User(
                username=name,
                password=password,
                role=role,
                first_name=first_name,
                last_name=last_name,
                cellphone=cellphone
            )

            # Guarda el nuevo usuario en la base de datos
            db.session.add(user)
            db.session.commit()

            # Crea un nuevo objeto Employee asociado al usuario
            employee = Employee(
                user_id=user.id,
                maximum_cash=maximum_cash,
                maximum_sale=maximum_sale,
                maximum_expense=maximum_expense,
                maximum_installments=maximum_installments,
                minimum_interest=minimum_interest,
                box_value=box_value,
                percentage_interest=percentage_interest,
                fix_value=fix_value
            )

            # Guarda el nuevo empleado en la base de datos
            db.session.add(employee)
            db.session.commit()

            # Verificar si se seleccionó el rol "Coordinador"
            if role == 'COORDINADOR':
                # Obtén el ID del empleado recién creado
                employee_id = employee.id

                # Crea un nuevo objeto Manager asociado al empleado
                manager = Manager(
                    employee_id=employee_id
                )

                # Guarda el nuevo coordinador en la base de datos
                db.session.add(manager)
                db.session.commit()

            if session['role'] == 'ADMINISTRADOR':
                # Verificar si se seleccionó el rol "Vendedor"
                if role == 'VENDEDOR':
                    # Obtén el ID del empleado recién creado (el empleado asociado al usuario que acaba de registrarse)
                    employee_id_recien_creado = employee.id

                    # Obtén el ID del empleado de la sesión (el empleado que está logeado)
                    user_id_empleado_sesion = session['user_id']
                    employee_id_empleado_sesion = Employee.query.filter_by(
                        user_id=user_id_empleado_sesion).first().id

                    # Busca el ID del gerente (manager) a partir del  ID del empleado de la sesión
                    manager = Manager.query.filter_by(
                        employee_id=employee_id_empleado_sesion).first()

                    if manager:
                        # Si se encuentra el gerente, obtén su ID
                        manager_id = manager.id

                        # Crea un nuevo objeto Salesman asociado al empleado recién creado y al gerente
                        salesman = Salesman(
                            employee_id=employee_id_recien_creado,
                            manager_id=manager_id
                        )

                        # Guarda el nuevo vendedor en la base de datos
                        db.session.add(salesman)
                        db.session.commit()

            else:

                # Verificar si se seleccionó el rol "Vendedor"
                if role in {'VENDEDOR', 'COORDINADOR'}:
                    # Obtén el ID del empleado recién creado (el empleado asociado al usuario que acaba de registrarse)
                    employee_id_recien_creado = employee.id

                    # Obtén el ID del empleado de la sesión (el empleado que está logeado)
                    user_id_empleado_sesion = session['user_id']
                    employee_id_empleado_sesion = Employee.query.filter_by(
                        user_id=user_id_empleado_sesion).first().id

                    # Busca el ID del gerente (manager) a partir del  ID del empleado de la sesión
                    manager = Manager.query.filter_by(
                        employee_id=employee_id_empleado_sesion).first()

                    if manager:
                        # Si se encuentra el gerente, obtén su ID
                        manager_id = manager.id

                        # Crea un nuevo objeto Salesman asociado al empleado recién creado y al gerente
                        salesman = Salesman(
                            employee_id=employee_id_recien_creado,
                            manager_id=manager_id
                        )

                        # Guarda el nuevo vendedor en la base de datos
                        db.session.add(salesman)
                        db.session.commit()

            # Redirecciona a la página de lista de usuarios o a donde corresponda
            return redirect(url_for('routes.user_list'))

        return render_template('create-user.html', user_id=user_id)
    else:
        abort(403)  # Acceso no autorizado


@routes.route('/user-list')
def user_list():
    user_id = session['user_id']
    role = session.get('role')
    
    # Si es administrador, mostrar todos los usuarios
    if role == 'ADMINISTRADOR':
        users = User.query.all()
        employees = Employee.query.all()
    else:
        # Si es coordinador, filtrar solo los vendedores asociados a él
        employee = Employee.query.filter_by(user_id=user_id).first()
        if employee:
            manager = Manager.query.filter_by(employee_id=employee.id).first()
            if manager:
                # Obtener todos los vendedores asociados a este coordinador
                salesmen = Salesman.query.filter_by(manager_id=manager.id).all()
                # Obtener los IDs de empleados de los vendedores
                salesman_employee_ids = [salesman.employee_id for salesman in salesmen]
                # Obtener los IDs de usuarios de esos empleados
                salesman_user_ids = [emp.user_id for emp in Employee.query.filter(Employee.id.in_(salesman_employee_ids)).all()]
                # Filtrar usuarios y empleados
                users = User.query.filter(User.id.in_(salesman_user_ids)).all()
                employees = Employee.query.filter(Employee.id.in_(salesman_employee_ids)).all()
            else:
                users = []
                employees = []
        else:
            users = []
            employees = []

    return render_template('user-list.html', users=users, employees=employees, user_id=user_id)


@routes.route('/get_maximum_values_create_salesman', methods=['GET'])
def get_maximum_values_create_salesman():
    # Buscar el empleado id a partir del user_id de la sesión
    user_id = session['user_id']
    employee_id = Employee.query.filter_by(user_id=user_id).first()

    if employee_id:
        employee_id = employee_id.id
        # Buscar el manager id a partir del employee_id
        manager = Manager.query.filter_by(employee_id=employee_id).first()

        if manager:
            manager_id = manager.id
            # Obtener la suma de maximum_cash de los vendedores asociados al coordinador
            total_cash_query = db.session.query(db.func.sum(Employee.maximum_cash)).join(Salesman). \
                filter(Salesman.manager_id == manager_id)
            total_cash = total_cash_query.scalar()

            if total_cash is None:
                total_cash = 0

            # Obtener el valor máximo de maximum_cash para el coordinador
            maximum_cash_coordinator = manager.employee.maximum_cash

            # Obtener el valor máximo de venta para el coordinador
            maximum_sale_coordinator = manager.employee.maximum_sale

            # Obtener el valor máximo de gastos
            maximum_expense_coordinator = manager.employee.maximum_expense

            # Obtener la cantidad máxima de cuotas
            maximum_installments_coordinator = manager.employee.maximum_installments

            # Calcular el valor máximo que se puede parametrizar a un nuevo vendedor
            maximum_cash_salesman = maximum_cash_coordinator - total_cash

            if maximum_cash_salesman <= 0:
                return {
                    'message': 'No se pueden crear mas vendedores.'
                }

            # Obtener el mínimo de interés
            minimum_interest = manager.employee.minimum_interest

            return {
                'maximum_cash_coordinator': str(maximum_cash_coordinator),
                'total_cash_salesman': str(total_cash),
                'maximum_cash_salesman': str(maximum_cash_salesman),
                'maximum_sale_coordinator': str(maximum_sale_coordinator),
                'maximum_expense_coordinator': str(maximum_expense_coordinator),
                'maximum_installments_coordinator': str(maximum_installments_coordinator),
                'minimum_interest_coordinator': str(minimum_interest),
            }
        else:
            abort(404)  # Coordinador no encontrado
    else:
        abort(404)  # Empleado no encontrado


@routes.route('/maximum-values-loan', methods=['GET'])
def get_maximum_values_loan():
    # Verificamos si 'user_id' está presente en la sesión
    if 'user_id' not in session:
        return "Error: El usuario no ha iniciado sesión."

    # Obtenemos el ID del empleado desde la sesión
    user_id = session['user_id']
    employee = Employee.query.filter_by(user_id=user_id).first()

    if employee is None:
        return "Error: No se encontraron los valores máximos para el préstamo."

    # Obtenemos los valores máximos establecidos para el préstamo
    maximum_sale = employee.maximum_sale
    maximum_installments = employee.maximum_installments
    minimum_interest = employee.minimum_interest

    # Devolvemos los valores como una respuesta JSON
    return jsonify({
        'maximum_sale': str(maximum_sale),
        'maximum_installments': str(maximum_installments),
        'minimum_interest': str(minimum_interest)
    })


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
    loan = Loan.query.get(id)
    client = Client.query.get(loan.client_id)
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

    return render_template('credit-detail.html', loans=loans, loan=loan, client=client, installments=installments,
                           loan_detail=loan_detail, payments=payments, payments_by_datetime=payments_by_datetime, user_id=session['user_id'])


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


@routes.route('/confirm_payment', methods=['POST'])
def confirm_payment():
    loan_id = request.form.get('loan_id')
    custom_payment = float(request.form.get('customPayment'))

    # Validar que el pago sea mayor a 0
    if custom_payment <= 0:
        return jsonify({"error": "El monto del pago debe ser mayor a 0."}), 400

    # Obtener los datos del préstamo y el cliente
    loan = Loan.query.get(loan_id)
    if not loan:
        return jsonify({"error": "Préstamo no encontrado."}), 404
        
    employee = Employee.query.get(loan.employee_id)
    employee.box_value += Decimal(custom_payment)

    client = loan.client

    # Calcular la suma de los montos pendientes de las cuotas
    total_amount_due = sum(installment.amount for installment in loan.installments
                           if installment.status in [InstallmentStatus.PENDIENTE, InstallmentStatus.MORA,
                                                     InstallmentStatus.ABONADA])

    # Validar que haya montos pendientes para pagar
    if total_amount_due <= 0:
        return jsonify({"error": "No hay montos pendientes para pagar."}), 400

    if custom_payment >= total_amount_due:
        # Marcar todas las cuotas como "PAGADA" y actualizar la fecha de pago
        for installment in loan.installments:
            if installment.status in [InstallmentStatus.PENDIENTE, InstallmentStatus.MORA, InstallmentStatus.ABONADA]:
                # Verificar que la cuota tenga monto pendiente
                if installment.amount <= 0:
                    continue
                    
                installment.status = InstallmentStatus.PAGADA
                installment.payment_date = datetime.now()
                # Crear el pago asociado a esta cuota
                payment = Payment(amount=installment.amount, payment_date=datetime.now(),
                                installment_id=installment.id)
                # Establecer el valor de la cuota en 0 (ya está pagada)
                installment.amount = 0
                db.session.add(payment)
        
        # Actualizar el estado del préstamo y el campo up_to_date
        loan.status = False  # 0 indica que el préstamo está pagado en su totalidad
        loan.up_to_date = True
        loan.modification_date = datetime.now()
        db.session.commit()
        return jsonify({"message": "Todas las cuotas han sido pagadas correctamente."}), 200
    else:
        # Lógica para manejar el pago parcial
        remaining_payment = Decimal(custom_payment)
        
        # Obtener las cuotas pendientes ordenadas por fecha de vencimiento (cronológicamente)
        pending_installments = sorted(
            [installment for installment in loan.installments 
             if installment.status in [InstallmentStatus.PENDIENTE, InstallmentStatus.MORA, InstallmentStatus.ABONADA] 
             and installment.amount > 0],
            key=lambda x: x.due_date if x.due_date else datetime.max
        )
        
        for installment in pending_installments:
            if remaining_payment <= 0:
                break
                
            # El monto pendiente de esta cuota
            installment_amount_due = installment.amount
            
            if remaining_payment >= installment_amount_due:
                # El pago cubre completamente esta cuota
                installment.status = InstallmentStatus.PAGADA
                installment.payment_date = datetime.now()
                installment.amount = 0
                
                # Crear el pago por el monto completo de la cuota
                payment = Payment(amount=installment_amount_due, payment_date=datetime.now(), 
                                installment_id=installment.id)
                db.session.add(payment)
                
                remaining_payment -= installment_amount_due
            else:
                # El pago solo cubre parcialmente esta cuota
                installment.status = InstallmentStatus.ABONADA
                installment.amount -= remaining_payment
                
                # Crear el pago por el monto parcial
                payment = Payment(amount=remaining_payment, payment_date=datetime.now(), 
                                installment_id=installment.id)
                db.session.add(payment)
                
                remaining_payment = 0
        
        # Actualizar el campo modification_date del préstamo después de procesar el pago parcial
        loan.modification_date = datetime.now()
        if client.first_modification_date != datetime.now().date():
            client.first_modification_date = datetime.now()
        client.debtor = False
        db.session.commit()

        return jsonify({"message": "El pago se ha registrado correctamente."}), 200
    
    return jsonify({"error": "El pago no pudo ser procesado."}), 400


@routes.route('/mark_overdue', methods=['POST'])
def mark_overdue():
    if request.method == 'POST':
        # Obtener el ID del préstamo de la solicitud POST
        loan_id = request.form['loan_id']

        # Buscar la primera cuota pendiente del préstamo específico
        # Si no hay cuotas pendientes, buscar la primera cuota en MORA
        pending_installment = LoanInstallment.query.filter(
            LoanInstallment.loan_id == loan_id,
            LoanInstallment.status == InstallmentStatus.PENDIENTE
        ).order_by(LoanInstallment.due_date.asc()).first()

        if pending_installment:
            # Actualizar el estado de la cuota pendiente a "MORA"
            pending_installment.status = InstallmentStatus.MORA
            pending_installment.updated_at = datetime.now()

            # Obtener el cliente asociado a este préstamo
            client = Client.query.join(Loan).filter(Loan.id == loan_id).first()
            if client:
                # Actualizar el campo debtor del cliente a True
                client.debtor = True
                db.session.add(client)

            # Crear un nuevo pago asociado a la cuota en MORA (monto 0)
            payment = Payment(
                amount=0, 
                payment_date=datetime.now(), 
                installment_id=pending_installment.id
            )
            db.session.add(payment)

            # Guardar los cambios en la base de datos
            if not client.first_modification_date:
                client.first_modification_date = datetime.now()
            db.session.commit()

            return 'La cuota pendiente ha sido marcada como MORA y el cliente ha sido marcado como deudor exitosamente'
        else:
            # Si no hay cuotas pendientes, verificar si ya hay cuotas en MORA
            overdue_installments = LoanInstallment.query.filter(
                LoanInstallment.loan_id == loan_id,
                LoanInstallment.status == InstallmentStatus.MORA
            ).all()
            
            if overdue_installments:
                # Obtener el cliente asociado a este préstamo
                client = Client.query.join(Loan).filter(Loan.id == loan_id).first()
                if client:
                    # Actualizar el campo debtor del cliente a True
                    client.debtor = True
                    db.session.add(client)

                # Crear un nuevo pago asociado a la primera cuota en MORA (monto 0)
                first_overdue_installment = overdue_installments[0]
                payment = Payment(
                    amount=0, 
                    payment_date=datetime.now(), 
                    installment_id=first_overdue_installment.id
                )
                db.session.add(payment)

                # Guardar los cambios en la base de datos
                if not client.first_modification_date:
                    client.first_modification_date = datetime.now()
                db.session.commit()
            else:
                return 'No se encontraron cuotas pendientes para marcar como MORA'
    else:
        return 'Método no permitido'


@routes.route('/payment_list/<int:user_id>', methods=['GET'])
def payments_list(user_id):
    # Obtiene el ID de usuario desde la ruta
    user_id = user_id

    # Busca al empleado asociado al usuario
    employee = Employee.query.filter_by(user_id=user_id).first()
    employee_id = employee.id
    employee_status = employee.status
    current_date = datetime.now().date()

    if not employee:
        return jsonify({"error": "No se encontró el empleado asociado al usuario."}), 404

    all_loans_paid = Loan.query.filter_by(employee_id=employee.id).all()

    all_loans_paid_count = 0

    all_loans_paid_today = False

    # Inicializa un set para almacenar los IDs de clientes que tienen pagos hoy
    clients_with_payments_today = set()

    # Obtiene todos los préstamos del empleado
    all_loans_paid = Loan.query.filter_by(employee_id=employee.id).all()

    # Recorre cada préstamo y sus cuotas para verificar pagos del día de hoy
    for loan in all_loans_paid:
        loan_installments = LoanInstallment.query.filter_by(
            loan_id=loan.id).all()
        for installment in loan_installments:
            payments = Payment.query.filter_by(
                installment_id=installment.id).all()
            for payment in payments:
                if payment.payment_date.date() == current_date:
                    # Agrega el ID del cliente al set si hay un pago hoy
                    clients_with_payments_today.add(loan.client_id)
                    break

    # La cantidad de clientes con pagos hoy es el tamaño del set
    all_loans_paid_count = len(clients_with_payments_today)

    # Contar préstamos activos (status=True) más los inactivos modificados hoy
    active_loans_count = db.session.query(Loan).filter(
        Loan.employee_id == employee.id,
        (Loan.status == True) | 
        ((Loan.status == False) & (func.date(Loan.modification_date) == datetime.now().date()))
    ).count()

    if active_loans_count == all_loans_paid_count:
        all_loans_paid_today = True


    # Calcula el total de cobros para el día con estado "PAGADA"
    total_collections_today = db.session.query(
        func.sum(Payment.amount)
    ).join(
        LoanInstallment, Payment.installment_id == LoanInstallment.id
    ).join(
        Loan, LoanInstallment.loan_id == Loan.id
    ).filter(
        Loan.client.has(employee_id=employee_id),
        func.date(Payment.payment_date) == datetime.now().date()
    ).scalar() or 0


    status_box = ""

    if employee_status == True and all_loans_paid_today == True:
        status_box = "Cerrada"
    elif employee_status == False and all_loans_paid_today == True:
        status_box = "Activa"
    elif employee_status == False and all_loans_paid_today == False:
        status_box = "Desactivada"
    elif employee_status == True and all_loans_paid_today == False:
        status_box = "Activa"
    else:
        status_box = "Activa"


    # Inicializa la lista para almacenar la información de los clientes
    clients_information = []
    clients_information_paid = []

    # Obtiene los clientes del empleado con préstamos activos o en mora
    for client in employee.clients:

        for loan in client.loans:
            total_installment_value_paid = 0  # Inicializar variable

            if loan.status:
                # Calcula el número de cuotas pagadas
                paid_installments = LoanInstallment.query.filter_by(loan_id=loan.id,
                                                                    status=InstallmentStatus.PAGADA).count()

                # Calcula el total pagado en el préstamo
                total_paid_amount = db.session.query(func.sum(Payment.amount)).join(
                    LoanInstallment, Payment.installment_id == LoanInstallment.id
                ).filter(
                    LoanInstallment.loan_id == loan.id
                ).scalar() or 0

                # Obtiene el valor de la cuota fija (asumiendo que todas las cuotas tienen el mismo valor)
                installment_value = db.session.query(LoanInstallment.fixed_amount).filter_by(
                    loan_id=loan.id
                ).first()

                # Calcula el número de cuota incluyendo decimales
                if installment_value and installment_value[0] > 0:
                    cuota_number_with_decimal = float(total_paid_amount) / float(installment_value[0])
                else:
                    cuota_number_with_decimal = paid_installments


                # Calcula el número de cuotas vencidas
                overdue_installments = LoanInstallment.query.filter_by(loan_id=loan.id,
                                                                       status=InstallmentStatus.MORA).count()
                total_overdue_amount = db.session.query(func.sum(LoanInstallment.amount)).filter_by(loan_id=loan.id,
                                                                                                    status=InstallmentStatus.MORA).scalar() or 0

                # Calcula el monto total pendiente
                total_outstanding_amount = db.session.query(func.sum(LoanInstallment.amount)).filter(
                    LoanInstallment.loan_id == loan.id,
                    LoanInstallment.status.in_(
                        [InstallmentStatus.PENDIENTE, InstallmentStatus.ABONADA, InstallmentStatus.MORA])
                ).scalar() or 0

                total_amount_paid = db.session.query(func.sum(LoanInstallment.fixed_amount)).filter(
                    LoanInstallment.loan_id == loan.id,
                    LoanInstallment.status.in_(
                        [InstallmentStatus.ABONADA, InstallmentStatus.PAGADA])
                ).scalar() or 0

                total_overdue_amount = db.session.query(func.sum(LoanInstallment.amount)).filter_by(loan_id=loan.id,
                                                                                                    status=InstallmentStatus.MORA).scalar() or 0

                # Encuentra la última cuota pendiente a la fecha actual incluyendo la fecha de creación de la cuota
                last_pending_installment = LoanInstallment.query.filter(
                    LoanInstallment.loan_id == loan.id,
                    LoanInstallment.status.in_(
                        [InstallmentStatus.PENDIENTE, InstallmentStatus.MORA])
                ).order_by(LoanInstallment.due_date.asc()).first()



                # Obtener la primera cuota de cada cliente y su valor
                # Excluir préstamos creados el mismo día
                if loan.creation_date.date() != datetime.now().date():
                    first_installment = LoanInstallment.query.filter(
                        LoanInstallment.loan_id == loan.id,
                        LoanInstallment.status.in_([InstallmentStatus.PENDIENTE, InstallmentStatus.ABONADA, InstallmentStatus.MORA])
                    ).order_by(LoanInstallment.due_date.asc()).first()
                else:
                    first_installment = None

                # Encuentra la fecha de modificación más reciente del préstamo
                last_loan_modification_date = Loan.query.filter_by(client_id=client.id).order_by(
                    Loan.modification_date.desc()).first()

                # Obtiene la fecha del último pago
                # last_payment_date = LoanInstallment.query.filter_by(loan_id=loan.id, status=InstallmentStatus.PAGADA).order_by(LoanInstallment.payment_date.desc()).first()

                # Encuentra la fecha del último pago
                last_payment_date = Payment.query \
                    .join(LoanInstallment) \
                    .filter(LoanInstallment.loan_id == loan.id) \
                    .filter(LoanInstallment.status.in_(
                        [InstallmentStatus.PAGADA, InstallmentStatus.ABONADA, InstallmentStatus.MORA])) \
                    .order_by(Payment.payment_date.desc()) \
                    .first()

                # Encuentra la cuota anterior a la fecha actual
                # previous_installment = LoanInstallment.query.filter_by(loan_id=loan.id, status=InstallmentStatus.PAGADA).order_by(LoanInstallment.payment_date.desc()).first()

                # Encuentra la cuota anterior a la fecha actual
                previous_installment = LoanInstallment.query \
                    .filter(LoanInstallment.loan_id == loan.id) \
                    .filter(LoanInstallment.status.in_(
                        [InstallmentStatus.PAGADA, InstallmentStatus.ABONADA, InstallmentStatus.MORA])) \
                    .order_by(LoanInstallment.due_date.desc()) \
                    .first()

                # Agrega el estado de la cuota anterior al diccionario client_info
                previous_installment_status = previous_installment.status.value if previous_installment else None

                # Obtener el valor pagado de la cuota anterior si existe
                previous_installment_paid_amount = 0
                if previous_installment:
                    previous_installment_paid_amount = sum(
                        payment.amount for payment in previous_installment.payments)

                approved = 'Aprobado' if loan.approved else 'Pendiente de Aprobación'

                # Agrega la información del cliente y su crédito a la lista de información de clientes
                client_info = {
                    'First Name': client.first_name,
                    'Last Name': client.last_name,
                    'Alias Client': client.alias,
                    'Paid Installments': paid_installments,
                    'Overdue Installments': overdue_installments,
                    'Total Outstanding Amount': total_outstanding_amount,
                    'Total Amount Paid': total_amount_paid,
                    'Total Overdue Amount': total_overdue_amount,
                    'Last Payment Date': last_payment_date.payment_date.isoformat() if last_payment_date else 0,
                    'Last Payment Date front': last_payment_date.payment_date.strftime(
                        '%Y-%m-%d') if last_payment_date else '0',
                    'Loan ID': loan.id,
                    'Approved': approved,
                    'Installment Value': last_pending_installment.amount if last_pending_installment else 0,
                    'Total Installments': loan.dues,
                    'Sales Date': loan.creation_date.isoformat(),
                    'Next Installment Date': last_pending_installment.due_date.isoformat() if last_pending_installment else 0,
                    'Next Installment Date front': last_pending_installment.due_date.strftime(
                        '%Y-%m-%d') if last_pending_installment else '0',
                    'Cuota Number': round(cuota_number_with_decimal, 2),
                    # Agrega el número de la cuota actual
                    'Due Date': last_pending_installment.due_date.isoformat() if last_pending_installment else 0,
                    # Agrega la fecha de vencimiento de la cuota
                    'Installment Status': last_pending_installment.status.value if last_pending_installment else None,
                    # Agrega el estado de la cuota
                    'Previous Installment Status': previous_installment_status,
                    'Last Loan Modification Date': last_loan_modification_date.modification_date.isoformat() if last_loan_modification_date else None,
                    'Previous Installment Paid Amount': previous_installment_paid_amount,
                    'Current Date': current_date,
                    'First Installment Value': first_installment.fixed_amount if first_installment and first_installment is not None else 0,
                    'First Modification Date': client.first_modification_date.isoformat() if client.first_modification_date else None,
                }

                clients_information.append(client_info)


            elif loan.status == False and loan.up_to_date and loan.modification_date.date() == datetime.now().date():

                # Obtener la primera cuota de cada cliente y su valor
                first_installment_paid = LoanInstallment.query.filter(
                    LoanInstallment.loan_id == loan.id
                ).order_by(LoanInstallment.due_date.asc()).first()


                # Verificar que first_installment_paid no sea None antes de acceder a sus pagos
                if first_installment_paid is not None:
                    total_installment_value_paid = sum(
                        payment.amount for payment in first_installment_paid.payments)


                    # Agrega la información del cliente y su crédito a la lista de información de clientes
                    client_information_paid = {
                        'Total Installment Value Paid': total_installment_value_paid,
                    }

                    clients_information_paid.append(client_information_paid)
                else:
                    # Si no hay cuotas, agregar un valor por defecto
                    client_information_paid = {
                        'Total Installment Value Paid': 0,
                    }
                    clients_information_paid.append(client_information_paid)

    # Obtén el término de búsqueda del formulario
    search_term = request.args.get('search', '')

    # Filtra los clientes según el término de búsqueda
    filtered_clients_information = [client_info for client_info in clients_information if
                                    search_term.lower() in f"{client_info['First Name']} {client_info['Last Name']}".lower()]

    # Ordena la lista filtrada por fecha de modificación ascendente
    filtered_clients_information.sort(
        key=lambda x: x['First Modification Date'] or datetime.max
    )

    # Calcular la suma total de los valores de pagos a plazos
    total_installment_value = sum(
        client['First Installment Value'] for client in clients_information)

    paid_total_installment_value = sum(
        client_info_paid['Total Installment Value Paid'] for client_info_paid in clients_information_paid
    )


    porcentaje_cobro = int(total_collections_today / total_installment_value *
                           100) if total_installment_value != 0 else 0


    # Renderiza la información filtrada como una respuesta JSON y también renderiza una plantilla
    return render_template('payments-route.html', clients=filtered_clients_information, status_box=status_box, employee_id=employee_id, user_id=user_id, active_loans_count=active_loans_count, all_loans_paid_count=all_loans_paid_count, total_installment_value=total_installment_value + paid_total_installment_value, total_collections_today=total_collections_today, porcentaje_cobro=porcentaje_cobro)


def is_workday(date):
    # Verificar si la fecha es domingo
    if date.weekday() == 6:  # 6 para domingo
        return False

    return True


def generate_loan_installments(loan):
    amount = loan.amount
    fixed_amount = loan.amount
    dues = loan.dues
    interest = loan.interest
    payment = loan.payment
    creation_date = loan.creation_date.date()
    client_id = loan.client_id
    employee_id = loan.employee_id

    installment_amount = int((amount + (amount * interest / 100)) / dues)

    # Establecer la fecha de vencimiento de la primera cuota
    if creation_date.weekday() == 5:  # 5 representa el sábado
        due_date = creation_date + timedelta(days=1)  # Avanzar al lunes
    else:
        due_date = creation_date + timedelta(days=1)

    installments = []
    for installment_number in range(1, int(dues) + 1):
        # Asegurarse de que la fecha de vencimiento sea un día laborable
        # while not is_workday(due_date):
        #     due_date += timedelta(days=1)

        installment = LoanInstallment(
            installment_number=installment_number,
            due_date=due_date,
            fixed_amount=installment_amount,
            amount=installment_amount,
            status='PENDIENTE',
            loan_id=loan.id
        )
        installments.append(installment)

        # Avanzar al siguiente día laborable para la próxima cuota
        due_date += timedelta(days=1)

    # Guardar las cuotas en la base de datos
    db.session.bulk_save_objects(installments)
    db.session.commit()


def get_loan_details(loan_id):
    # Obtener el préstamo y el cliente asociado
    loan = Loan.query.get(loan_id)
    client = Client.query.get(loan.client_id)

    # Obtener todas las cuotas del préstamo
    installments = LoanInstallment.query.filter_by(loan_id=loan.id).all()

    loan_id = loan.id

    # Calcular los datos requeridos
    total_cuotas = len(installments)
    cuotas_pagadas = sum(
        1 for installment in installments if installment.status == InstallmentStatus.PAGADA)
    cuotas_vencidas = sum(
        1 for installment in installments if installment.status == InstallmentStatus.MORA)
    valor_total = loan.amount + (loan.amount * loan.interest / 100)

    # SE DEBE MODIFICAR EL CALCULO DE LA SUMA DEL SALDO PENDIENTE
    # Calcular la suma de todos los pagos realizados para este préstamo
    total_pagos_realizados = db.session.query(func.sum(Payment.amount)).join(
        LoanInstallment, Payment.installment_id == LoanInstallment.id
    ).filter(
        LoanInstallment.loan_id == loan_id
    ).scalar() or 0
    
    saldo_pendiente = valor_total - total_pagos_realizados

        

    # Formatear los valores sin decimales
    valor_total = int(valor_total)
    saldo_pendiente = int(saldo_pendiente)

    # Retornar los detalles del préstamo
    detalles_prestamo = {
        'loan_id': loan_id,
        'cuotas_totales': total_cuotas,
        'cuotas_pagadas': cuotas_pagadas,
        'cuotas_vencidas': cuotas_vencidas,
        'valor_total': valor_total,
        'saldo_pendiente': saldo_pendiente
    }
    return detalles_prestamo


@routes.route('/concept', methods=['GET', 'POST'])
def create_concept():
    if 'user_id' in session and session['role'] == 'ADMINISTRADOR':
        if request.method == 'POST':
            name = request.form.get('concept')
            transaction_types = request.form.getlist('transaction_types')
            transaction_types_str = ','.join(transaction_types)

            concept = Concept(
                transaction_types=transaction_types_str, name=name)
            db.session.add(concept)
            db.session.commit()
            return 'Concepto creado', 200
        return render_template('create-concept.html', concept=Concept)


@routes.route('/concept/<int:concept_id>', methods=['PUT'])
def update_concept(concept_id):
    concept = Concept.query.get(concept_id)

    if not concept:
        return jsonify({'message': 'Concepto no encontrado'}), 404

    data = request.get_json()
    name = data.get('name')
    transaction_types = data.get('transaction_types')

    concept.name = name
    concept.transaction_types = transaction_types
    db.session.commit()

    return jsonify(concept.to_json())


@routes.route('/get-concepts', methods=['GET'])
def get_concepts():
    transaction_type = request.args.get('transaction_type')

    # Consultar los conceptos relacionados con el tipo de transacción
    concepts = Concept.query.filter_by(
        transaction_types=transaction_type).all()

    # Convertir los conceptos a formato JSON
    concepts_json = [concept.to_json() for concept in concepts]

    return jsonify(concepts_json)


@routes.route('/box', methods=['GET'])
def box():
    try:
        # Obtener el user_id de la sesión
        user_id = session.get('user_id')


        if user_id is None:
            return jsonify({'message': 'Usuario no encontrado en la sesión'}), 401

        # Verificar si el usuario es un coordinador
        user = User.query.get(user_id)
        if user is None or user.role != Role.COORDINADOR:
            return jsonify({'message': 'El usuario no es un coordinador válido'}), 403

        # Obtener la información de la caja del coordinador
        coordinator = Employee.query.filter_by(user_id=user_id).first()
        coordinator_cash = coordinator.box_value

        coordinator_name = f"{user.first_name} {user.last_name}"

        # Obtener el ID del manager del coordinador
        manager_id = db.session.query(Manager.id).filter_by(
            employee_id=coordinator.id).scalar()

        if not manager_id:
            return jsonify({'message': 'No se encontró ningún coordinador asociado a este empleado'}), 404

        salesmen = Salesman.query.filter_by(manager_id=manager_id).all()

        # Funciones para sumar el valor de todas las transacciones en estado: APROBADO y Tipo: INGRESO/RETIRO
        current_date = datetime.now().date()

        # Calcular la fecha de inicio y fin del día actual
        start_of_day = datetime.combine(current_date, datetime.min.time())
        end_of_day = datetime.combine(current_date, datetime.max.time())

        # Filtrar las transacciones para el día actual del manager en sesión
        total_outbound_amount = db.session.query(
            func.sum(Transaction.amount).label('total_amount')
        ).join(Salesman, Transaction.employee_id == Salesman.employee_id).filter(
            Transaction.transaction_types == 'INGRESO',
            Transaction.approval_status == 'APROBADA',
            Salesman.manager_id == manager_id,  # Filtrar solo por el manager en sesión
            Transaction.creation_date.between(
                start_of_day, end_of_day)  # Filtrar por fecha actual
        ).scalar() or 0

        # Filtrar las transacciones para el día actual del manager en sesión
        total_inbound_amount = db.session.query(
            func.sum(Transaction.amount).label('total_amount')
        ).join(Salesman, Transaction.employee_id == Salesman.employee_id).filter(
            Transaction.transaction_types == 'RETIRO',
            Transaction.approval_status == 'APROBADA',
            Salesman.manager_id == manager_id,  # Filtrar solo por el manager en sesión
            # Filtrar por fecha actual
            func.date(Transaction.creation_date) == current_date
        ).scalar() or 0


        # Inicializa la lista para almacenar las estadísticas de los vendedores
        salesmen_stats = []

        # Ciclo a través de cada vendedor asociado al coordinador
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


            # Obtener el valor inicial de la caja del vendedor
            employee_records = EmployeeRecord.query.filter_by(
                employee_id=salesman.employee_id).order_by(EmployeeRecord.id.desc()).first()
            if employee_records:
                initial_box_value = employee_records.closing_total

            # Verificar si ya existe un registro en EmployeeRecord con la fecha actual
            existing_record_today = EmployeeRecord.query.filter(
                EmployeeRecord.employee_id == salesman.employee_id,
                func.date(EmployeeRecord.creation_date) == datetime.now().date()
            ).first()

            all_loans_paid = Loan.query.filter_by(
                employee_id=salesman.employee_id)
            all_loans_paid_today = False
            for loan in all_loans_paid:
                loan_installments = LoanInstallment.query.filter_by(
                    loan_id=loan.id).all()
                for installment in loan_installments:
                    payments = Payment.query.filter_by(
                        installment_id=installment.id).all()
                    if any(payment.payment_date.date() == current_date for payment in payments):
                        all_loans_paid_today = True
                        break
                    if all_loans_paid_today:
                        break

            # Calcula el total de cobros para el día con estado "PAGADA"
            total_collections_today = db.session.query(
                func.sum(Payment.amount)
            ).join(
                LoanInstallment, Payment.installment_id == LoanInstallment.id
            ).join(
                Loan, LoanInstallment.loan_id == Loan.id
            ).filter(
                Loan.client.has(employee_id=salesman.employee_id),
                func.date(Payment.payment_date) == datetime.now().date()
            ).scalar() or 0

            for client in employee.clients:
                for loan in client.loans:
                    # Excluir préstamos creados hoy mismo
                    if loan.creation_date.date() == datetime.now().date():
                        continue
                    
                    if loan.status:
                        # Encuentra la última cuota pendiente a la fecha actual incluyendo la fecha de creación de la cuota
                        pending_installment = LoanInstallment.query.filter(
                            LoanInstallment.loan_id == loan.id
                        ).order_by(LoanInstallment.due_date.asc()).first()
                        if pending_installment:
                            total_pending_installments_amount += pending_installment.fixed_amount
                    elif loan.status == False and loan.up_to_date and loan.modification_date.date() == datetime.now().date():
                        pending_installment_paid = LoanInstallment.query.filter(
                            LoanInstallment.loan_id == loan.id
                        ).order_by(LoanInstallment.due_date.asc()).first()
                        total_pending_installments_loan_close_amount += pending_installment_paid.fixed_amount

            # Calcula la cantidad de nuevos clientes registrados en el día
            new_clients = Client.query.filter(
                Client.employee_id == salesman.employee_id,
                Client.creation_date >= datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0),
                # Client.creation_date <= datetime.now()
            ).count()

            # Calcula el total de préstamos de los nuevos clientes
            new_clients_loan_amount = Loan.query.join(Client).filter(
                Client.employee_id == salesman.employee_id,
                Loan.creation_date >= datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0),
                # Loan.creation_date <= datetime.now(),
                Loan.is_renewal == False  # Excluir renovaciones
            ).with_entities(func.sum(Loan.amount)).scalar() or 0

            # Calcula el total de renovaciones para el día actual para este vendedor
            total_renewal_loans = Loan.query.filter(
                Loan.client.has(employee_id=salesman.employee_id),
                Loan.is_renewal == True,
                Loan.status == True,
                Loan.approved == True,
                Loan.creation_date >= datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0)
                # Loan.creation_date < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            ).count()

            # Calcula el monto total de las renovaciones de préstamos para este vendedor
            total_renewal_loans_amount = Loan.query.filter(
                Loan.client.has(employee_id=salesman.employee_id),
                Loan.is_renewal == True,
                Loan.status == True,
                Loan.approved == True,
                Loan.creation_date >= datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0)
                # Loan.creation_date < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            ).with_entities(func.sum(Loan.amount)).scalar() or 0

            # Calcula Valor de los gastos diarios
            daily_expenses_amount = Transaction.query.filter(
                Transaction.employee_id == salesman.employee_id,
                Transaction.transaction_types == TransactionType.GASTO,
                Transaction.approval_status == ApprovalStatus.APROBADA,
                # Filtrar por fecha actual
                func.date(Transaction.creation_date) == datetime.now().date()
            ).with_entities(func.sum(Transaction.amount)).scalar() or 0

            # Calcula el número de transacciones de gastos diarios
            daily_expenses_count = Transaction.query.filter(
                Transaction.employee_id == salesman.employee_id,
                Transaction.transaction_types == TransactionType.GASTO,
                Transaction.approval_status == ApprovalStatus.APROBADA,
                # Filtrar por fecha actual
                func.date(Transaction.creation_date) == datetime.now().date()
            ).count() or 0

            # Calcula los retiros diarios basados en transacciones de RETIRO
            daily_withdrawals = Transaction.query.filter(
                Transaction.employee_id == salesman.employee_id,
                Transaction.transaction_types == TransactionType.RETIRO,
                Transaction.approval_status == ApprovalStatus.APROBADA,
                # Filtrar por fecha actual
                func.date(Transaction.creation_date) == datetime.now().date()
            ).with_entities(func.sum(Transaction.amount)).scalar() or 0

            daily_withdrawals_count = Transaction.query.filter(
                Transaction.employee_id == salesman.employee_id,
                Transaction.transaction_types == TransactionType.RETIRO,
                Transaction.approval_status == ApprovalStatus.APROBADA,
                # Filtrar por fecha actual
                func.date(Transaction.creation_date) == datetime.now().date()
            ).count() or 0

            # Calcula las colecciones diarias basadas en transacciones de INGRESO
            daily_collection = Transaction.query.filter(
                Transaction.employee_id == salesman.employee_id,
                Transaction.transaction_types == TransactionType.INGRESO,
                Transaction.approval_status == ApprovalStatus.APROBADA,
                # Filtrar por fecha actual
                func.date(Transaction.creation_date) == datetime.now().date()
            ).with_entities(func.sum(Transaction.amount)).scalar() or 0

            daily_collection_count = Transaction.query.filter(
                Transaction.employee_id == salesman.employee_id,
                Transaction.transaction_types == TransactionType.INGRESO,
                Transaction.approval_status == ApprovalStatus.APROBADA,
                # Filtrar por fecha actual
                func.date(Transaction.creation_date) == datetime.now().date()
            ).count() or 0

            # Obtener detalles de gastos, ingresos y retiros asociados a ese vendedor y ordenar por fecha de creación descendente
            transactions = Transaction.query.filter_by(
                employee_id=employee_id).order_by(Transaction.creation_date.desc()).all()

            # Filtrar transacciones por tipo y fecha
            today = datetime.today().date()
            expenses = [trans for trans in transactions if
                        trans.transaction_types == TransactionType.GASTO and trans.creation_date.date() == today]
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

            # Clientes morosos para el día
            customers_in_arrears = sum(
                1 for client in salesman.employee.clients
                for loan in client.loans
                if loan.status and any(
                    installment.status == InstallmentStatus.MORA
                    for installment in loan.installments
                )
            )

            # Calcula la cantidad de clientes recaudados en el día
            total_clients_collected_close = sum(
                1 for client in salesman.employee.clients
                for loan in client.loans
                if loan.status == False and any(
                    installment.status == InstallmentStatus.PAGADA and installment.payment_date == datetime.now().date()
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
                func.date(Payment.payment_date) == datetime.now().date(),
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

            # Convertir los valores de estadísticas a números antes de agregarlos a salesmen_stats
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

            # Si ya existe un registro del día, no sumar total_collections_today
            if existing_record_today:
                box_value = initial_box_value - float(daily_withdrawals) - float(
                    daily_expenses_amount) + float(daily_collection) - float(new_clients_loan_amount) - float(total_renewal_loans_amount)
            else:
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

        # Obtener los gastos del coordinador
        expenses = Transaction.query.filter(
            Transaction.employee_id == coordinator.id,
            Transaction.transaction_types == 'GASTO',
            func.date(Transaction.creation_date) == current_date
        ).all()

        # Obtener el valor total de los gastos
        total_expenses = sum(expense.amount for expense in expenses)

        expense_details = [
            {'description': trans.description, 'amount': trans.amount, 'approval_status': trans.approval_status.name,
             'attachment': trans.attachment, 'date': trans.creation_date.strftime('%d/%m/%Y')} for trans in expenses]

        coordinator_box = {
        'maximum_cash': float(coordinator_cash),
        'total_outbound_amount': float(total_outbound_amount),
        'total_inbound_amount': float(total_inbound_amount),
        'final_box_value': float(coordinator_cash) +
                        float(total_inbound_amount) -
                        float(total_outbound_amount) -
                        float(total_expenses),
        }


        # Renderizar la plantilla con las variables
        return render_template('box.html', coordinator_box=coordinator_box, salesmen_stats=salesmen_stats,
                               search_term=search_term, all_boxes_closed=all_boxes_closed,
                               coordinator_name=coordinator_name, user_id=user_id, expense_details=expense_details, total_expenses=total_expenses)
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

        # Obtener la información de la caja del sub-administrador
        sub_admin_cash = sub_admin_employee.box_value
        sub_admin_name = f"{sub_admin_user.first_name} {sub_admin_user.last_name}"

        # Obtener el ID del manager del sub-administrador
        manager_id = db.session.query(Manager.id).filter_by(
            employee_id=sub_admin_employee.id).scalar()

        if not manager_id:
            return jsonify({'message': 'No se encontró ningún manager asociado a este empleado'}), 404

        salesmen = Salesman.query.filter_by(manager_id=manager_id).all()

        # Funciones para sumar el valor de todas las transacciones en estado: APROBADO y Tipo: INGRESO/RETIRO
        current_date = datetime.now().date()

        # Calcular la fecha de inicio y fin del día actual
        start_of_day = datetime.combine(current_date, datetime.min.time())
        end_of_day = datetime.combine(current_date, datetime.max.time())

        # Filtrar las transacciones para el día actual del manager específico
        total_outbound_amount = db.session.query(
            func.sum(Transaction.amount).label('total_amount')
        ).join(Salesman, Transaction.employee_id == Salesman.employee_id).filter(
            Transaction.transaction_types == 'INGRESO',
            Transaction.approval_status == 'APROBADA',
            Salesman.manager_id == manager_id,  # Filtrar solo por el manager específico
            Transaction.creation_date.between(
                start_of_day, end_of_day)  # Filtrar por fecha actual
        ).scalar() or 0

        # Filtrar las transacciones para el día actual del manager específico
        total_inbound_amount = db.session.query(
            func.sum(Transaction.amount).label('total_amount')
        ).join(Salesman, Transaction.employee_id == Salesman.employee_id).filter(
            Transaction.transaction_types == 'RETIRO',
            Transaction.approval_status == 'APROBADA',
            Salesman.manager_id == manager_id,  # Filtrar solo por el manager específico
            # Filtrar por fecha actual
            func.date(Transaction.creation_date) == current_date
        ).scalar() or 0

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

            # Obtener el valor inicial de la caja del vendedor
            employee_records = EmployeeRecord.query.filter_by(
                employee_id=salesman.employee_id).order_by(EmployeeRecord.id.desc()).first()
            if employee_records:
                initial_box_value = employee_records.closing_total

            all_loans_paid = Loan.query.filter_by(
                employee_id=salesman.employee_id)
            all_loans_paid_today = False
            for loan in all_loans_paid:
                loan_installments = LoanInstallment.query.filter_by(
                    loan_id=loan.id).all()
                for installment in loan_installments:
                    payments = Payment.query.filter_by(
                        installment_id=installment.id).all()
                    if any(payment.payment_date.date() == current_date for payment in payments):
                        all_loans_paid_today = True
                        break
                    if all_loans_paid_today:
                        break

            # Calcula el total de cobros para el día con estado "PAGADA"
            total_collections_today = db.session.query(
                func.sum(Payment.amount)
            ).join(
                LoanInstallment, Payment.installment_id == LoanInstallment.id
            ).join(
                Loan, LoanInstallment.loan_id == Loan.id
            ).filter(
                Loan.client.has(employee_id=salesman.employee_id),
                func.date(Payment.payment_date) == datetime.now().date()
            ).scalar() or 0

            for client in employee.clients:
                for loan in client.loans:
                    # Excluir préstamos creados hoy mismo
                    if loan.creation_date.date() == datetime.now().date():
                        continue
                    
                    if loan.status:
                        # Encuentra la última cuota pendiente a la fecha actual incluyendo la fecha de creación de la cuota
                        pending_installment = LoanInstallment.query.filter(
                            LoanInstallment.loan_id == loan.id
                        ).order_by(LoanInstallment.due_date.asc()).first()
                        if pending_installment:
                            total_pending_installments_amount += pending_installment.fixed_amount
                    elif loan.status == False and loan.up_to_date and loan.modification_date.date() == datetime.now().date():
                        pending_installment_paid = LoanInstallment.query.filter(
                            LoanInstallment.loan_id == loan.id
                        ).order_by(LoanInstallment.due_date.asc()).first()
                        total_pending_installments_loan_close_amount += pending_installment_paid.fixed_amount

            # Calcula la cantidad de nuevos clientes registrados en el día
            new_clients = Client.query.filter(
                Client.employee_id == salesman.employee_id,
                Client.creation_date >= datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0),
            ).count()

            # Calcula el total de préstamos de los nuevos clientes
            new_clients_loan_amount = Loan.query.join(Client).filter(
                Client.employee_id == salesman.employee_id,
                Loan.creation_date >= datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0),
                Loan.is_renewal == False  # Excluir renovaciones
            ).with_entities(func.sum(Loan.amount)).scalar() or 0

            # Calcula el total de renovaciones para el día actual para este vendedor
            total_renewal_loans = Loan.query.filter(
                Loan.client.has(employee_id=salesman.employee_id),
                Loan.is_renewal == True,
                Loan.status == True,
                Loan.approved == True,
                Loan.creation_date >= datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0)
            ).count()

            # Calcula el monto total de las renovaciones activas de préstamos para este vendedor
            total_renewal_loans_amount = Loan.query.filter(
                Loan.client.has(employee_id=salesman.employee_id),
                Loan.is_renewal == True,
                Loan.status == True,
                Loan.approved == True,
                Loan.creation_date >= datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0)
            ).with_entities(func.sum(Loan.amount)).scalar() or 0



            # Calcula Valor de los gastos diarios
            daily_expenses_amount = Transaction.query.filter(
                Transaction.employee_id == salesman.employee_id,
                Transaction.transaction_types == TransactionType.GASTO,
                Transaction.approval_status == ApprovalStatus.APROBADA,
                # Filtrar por fecha actual
                func.date(Transaction.creation_date) == datetime.now().date()
            ).with_entities(func.sum(Transaction.amount)).scalar() or 0

            # Calcula el número de transacciones de gastos diarios
            daily_expenses_count = Transaction.query.filter(
                Transaction.employee_id == salesman.employee_id,
                Transaction.transaction_types == TransactionType.GASTO,
                Transaction.approval_status == ApprovalStatus.APROBADA,
                # Filtrar por fecha actual
                func.date(Transaction.creation_date) == datetime.now().date()
            ).count() or 0

            # Calcula los retiros diarios basados en transacciones de RETIRO
            daily_withdrawals = Transaction.query.filter(
                Transaction.employee_id == salesman.employee_id,
                Transaction.transaction_types == TransactionType.RETIRO,
                Transaction.approval_status == ApprovalStatus.APROBADA,
                # Filtrar por fecha actual
                func.date(Transaction.creation_date) == datetime.now().date()
            ).with_entities(func.sum(Transaction.amount)).scalar() or 0

            daily_withdrawals_count = Transaction.query.filter(
                Transaction.employee_id == salesman.employee_id,
                Transaction.transaction_types == TransactionType.RETIRO,
                Transaction.approval_status == ApprovalStatus.APROBADA,
                # Filtrar por fecha actual
                func.date(Transaction.creation_date) == datetime.now().date()
            ).count() or 0

            # Calcula las colecciones diarias basadas en transacciones de INGRESO
            daily_collection = Transaction.query.filter(
                Transaction.employee_id == salesman.employee_id,
                Transaction.transaction_types == TransactionType.INGRESO,
                Transaction.approval_status == ApprovalStatus.APROBADA,
                # Filtrar por fecha actual
                func.date(Transaction.creation_date) == datetime.now().date()
            ).with_entities(func.sum(Transaction.amount)).scalar() or 0

            daily_collection_count = Transaction.query.filter(
                Transaction.employee_id == salesman.employee_id,
                Transaction.transaction_types == TransactionType.INGRESO,
                Transaction.approval_status == ApprovalStatus.APROBADA,
                # Filtrar por fecha actual
                func.date(Transaction.creation_date) == datetime.now().date()
            ).count() or 0

            # Obtener detalles de gastos, ingresos y retiros asociados a ese vendedor y ordenar por fecha de creación descendente
            transactions = Transaction.query.filter_by(
                employee_id=employee_id).order_by(Transaction.creation_date.desc()).all()

            # Filtrar transacciones por tipo y fecha
            today = datetime.today().date()
            expenses = [trans for trans in transactions if
                        trans.transaction_types == TransactionType.GASTO and trans.creation_date.date() == today]
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

            # Clientes morosos para el día
            customers_in_arrears = sum(
                1 for client in salesman.employee.clients
                for loan in client.loans
                if loan.status and any(
                    installment.status == InstallmentStatus.MORA
                    for installment in loan.installments
                )
            )

            # Calcula la cantidad de clientes recaudados en el día
            total_clients_collected_close = sum(
                1 for client in salesman.employee.clients
                for loan in client.loans
                if loan.status == False and any(
                    installment.status == InstallmentStatus.PAGADA and installment.payment_date == datetime.now().date()
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
                func.date(Payment.payment_date) == datetime.now().date(),
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

        # Obtener los gastos del sub-administrador
        expenses = Transaction.query.filter(
            Transaction.employee_id == sub_admin_employee.id,
            Transaction.transaction_types == 'GASTO',
            func.date(Transaction.creation_date) == current_date
        ).all()

        # Obtener el valor total de los gastos
        total_expenses = sum(expense.amount for expense in expenses)

        expense_details = [
            {'description': trans.description, 'amount': trans.amount, 'approval_status': trans.approval_status.name,
             'attachment': trans.attachment, 'date': trans.creation_date.strftime('%d/%m/%Y')} for trans in expenses]

        sub_admin_box = {
            'maximum_cash': float(sub_admin_cash),
            'total_outbound_amount': float(total_outbound_amount),
            'total_inbound_amount': float(total_inbound_amount),
            'final_box_value': float(sub_admin_cash) +
                            float(total_inbound_amount) -
                            float(total_outbound_amount) -
                            float(total_expenses),
        }

        # Renderizar la plantilla con las variables
        return render_template('box.html', coordinator_box=sub_admin_box, salesmen_stats=salesmen_stats,
                               search_term=search_term, all_boxes_closed=all_boxes_closed,
                               coordinator_name=sub_admin_name, user_id=user_id, expense_details=expense_details, 
                               total_expenses=total_expenses, manager_id=manager_id)
    except Exception as e:
        return jsonify({'message': 'Error interno del servidor', 'error': str(e)}), 500


@routes.route('/debtor', methods=['GET'])
def debtor():
    try:
        # Obtener el user_id de la sesión
        user_id = session.get('user_id')

        if user_id is None:
            return jsonify({'message': 'Usuario no encontrado en la sesión'}), 401

        empleado = Employee.query.filter_by(user_id=user_id).first()

        if not empleado:
            return jsonify({'message': 'Empleado no encontrado'}), 404

        mora_debtors_details = []

        # Obtener todos los clientes asociados a este empleado que tienen préstamos en estado "MORA"
        clientes_en_mora = Client.query.filter(
            Client.employee_id == empleado.id,  # Filtrar por el ID del empleado
            Client.debtor == True,
        ).all()

        for cliente in clientes_en_mora:
            # Obtener el préstamo del cliente
            prestamo = Loan.query.filter_by(client_id=cliente.id).first()

            if prestamo is None:
                continue  # Si el cliente no tiene préstamo, continuar con el siguiente cliente

            # Obtener todas las cuotas del préstamo del cliente
            cuotas = LoanInstallment.query.filter_by(loan_id=prestamo.id).all()

            # Calcular los datos requeridos
            cuotas_pagadas = sum(
                1 for cuota in cuotas if cuota.status == InstallmentStatus.PAGADA)
            cuotas_vencidas = sum(
                1 for cuota in cuotas if cuota.status == InstallmentStatus.MORA)
            valor_total = prestamo.amount + \
                (prestamo.amount * prestamo.interest / 100)
            saldo_pendiente = valor_total - sum(
                cuota.amount for cuota in cuotas if cuota.status == InstallmentStatus.PAGADA)

            # Formatear los valores sin decimales
            valor_total = int(valor_total)
            saldo_pendiente = int(saldo_pendiente)

            # Crear un diccionario con los detalles del cliente en MORA
            mora_debtor_details = {
                'nombre_empleado': f'{empleado.user.first_name} {empleado.user.last_name}',
                'nombre_cliente': f'{cliente.first_name} {cliente.last_name}',
                'cuotas_pagadas': cuotas_pagadas,
                'cuotas_vencidas': cuotas_vencidas,
                'valor_total': valor_total,
                'saldo_pendiente': saldo_pendiente,
                'id_prestamo': prestamo.id
            }

            # Agregar los detalles del cliente en MORA a la lista
            mora_debtors_details.append(mora_debtor_details)

            # Obtener el término de búsqueda del formulario
        search_term = request.args.get('search')

        # Filtrar los clientes según el término de búsqueda
        if search_term:
            clientes_en_mora = Client.query.filter(
                Client.employee_id == empleado.id,
                Client.debtor == True,
                (Client.first_name + ' ' +
                 Client.last_name).ilike(f'%{search_term}%')
            ).all()
        else:
            clientes_en_mora = Client.query.filter(
                Client.employee_id == empleado.id,
                Client.debtor == True,
            ).all()

        return render_template('debtor.html', mora_debtors_details=mora_debtors_details, search_term=search_term)

    except Exception as e:
        return jsonify({'message': 'Error interno del servidor', 'error': str(e)}), 500


@routes.route('/get-debtors', methods=['GET'])
def get_debtors():
    # Obtener el ID del usuario desde la sesión
    user_id = session.get('user_id')

    # Buscar al empleado asociado al usuario
    employee = Employee.query.filter_by(user_id=user_id).first()

    if not employee:
        return jsonify({"error": "No se encontró el empleado asociado al usuario."}), 404

    # Inicializar la lista para almacenar la información de los vendedores y sus clientes
    debtors_info = []

    # Si el usuario es un COORDINADOR, puede ver a todos los vendedores y sus clientes
    if employee.user.role == Role.COORDINADOR:
        # Obtener todos los vendedores
        salesmen = Salesman.query.all()

        for salesman in salesmen:
            # Obtener la información del empleado (vendedor)
            salesman_info = {
                "employee_name": salesman.employee.user.first_name + " " + salesman.employee.user.last_name,
                "total_overdue_installments": 0,  # Inicializar el total de cuotas en mora en 0
                "clients": []
            }

            # Obtener los clientes del vendedor
            clients = Client.query.filter_by(
                employee_id=salesman.employee.id).all()

            for client in clients:
                # Calcular la información para cada cliente
                client_info = {
                    "client_name": client.first_name + " " + client.last_name,
                    "paid_installments": 0,  # Inicializar el número de cuotas pagadas en 0
                    "overdue_installments": 0,  # Inicializar el número de cuotas en mora en 0
                    "remaining_debt": 0,  # Inicializar el monto pendiente en 0
                    "total_overdue_amount": 0,  # Inicializar el monto total en mora en 0
                    # Inicializar la fecha de la última cuota pagada como None
                    "last_paid_installment_date": None
                }

                # Obtener todas las cuotas del cliente
                installments = LoanInstallment.query.filter_by(
                    client_id=client.id).all()

                for installment in installments:
                    if installment.status == InstallmentStatus.PAGADA:
                        client_info["paid_installments"] += 1
                        client_info["last_paid_installment_date"] = installment.payment_date
                    elif installment.status == InstallmentStatus.MORA:
                        client_info["overdue_installments"] += 1
                        client_info["total_overdue_amount"] += float(
                            installment.amount)
                    if installment.status != InstallmentStatus.PAGADA:
                        client_info["remaining_debt"] += float(
                            installment.amount)

                # Agregar la información del cliente a la lista de clientes del vendedor
                salesman_info["clients"].append(client_info)

                # Actualizar el total de cuotas en mora del vendedor
                salesman_info["total_overdue_installments"] += client_info["overdue_installments"]

            # Agregar la información del vendedor a la lista principal
            debtors_info.append(salesman_info)

    # Si el usuario es un VENDEDOR, solo puede ver sus propios clientes morosos
    elif employee.user.role == Role.VENDEDOR:
        # Obtener al vendedor
        salesman = Salesman.query.filter_by(employee_id=employee.id).first()

        if not salesman:
            return jsonify({"error": "No se encontró el vendedor asociado al empleado."}), 404

        # Obtener la información del empleado (vendedor)
        salesman_info = {
            "employee_name": salesman.employee.user.first_name + " " + salesman.employee.user.last_name,
            "total_overdue_installments": 0,  # Inicializar el total de cuotas en mora en 0
            "clients": []
        }

        # Obtener los clientes del vendedor
        clients = Client.query.filter_by(
            employee_id=salesman.employee.id).all()

        for client in clients:
            # Calcular la información para cada cliente
            client_info = {
                "client_name": client.first_name + " " + client.last_name,
                "paid_installments": 0,  # Inicializar el número de cuotas pagadas en 0
                "overdue_installments": 0,  # Inicializar el número de cuotas en mora en 0
                "remaining_debt": 0,  # Inicializar el monto pendiente en 0
                "total_overdue_amount": 0,  # Inicializar el monto total en mora en 0
                # Inicializar la fecha de la última cuota pagada como None
                "last_paid_installment_date": None
            }

            # Obtener todas las cuotas del cliente
            installments = LoanInstallment.query.filter_by(
                client_id=client.id).all()

            for installment in installments:
                if installment.status == InstallmentStatus.PAGADA:
                    client_info["paid_installments"] += 1
                    client_info["last_paid_installment_date"] = installment.payment_date
                elif installment.status == InstallmentStatus.MORA:
                    client_info["overdue_installments"] += 1
                    client_info["total_overdue_amount"] += float(
                        installment.amount)
                if installment.status != InstallmentStatus.PAGADA:
                    client_info["remaining_debt"] += float(installment.amount)

            # Agregar la información del cliente a la lista de clientes del vendedor
            salesman_info["clients"].append(client_info)

            # Actualizar el total de cuotas en mora del vendedor
            salesman_info["total_overdue_installments"] += client_info["overdue_installments"]

        # Agregar la información del vendedor a la lista principal
        debtors_info.append(salesman_info)
    return jsonify(debtors_info)


@routes.route('/approval-expenses')
def approval_expenses():
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

        # Verificar si el usuario es un coordinador
        if empleado.manager is None:
            return jsonify({'message': 'El usuario no es un coordinador'}), 403

        # Inicializar una lista para almacenar las transacciones pendientes de aprobación
        detalles_transacciones = []

        # Obtener los vendedores asociados a este coordinador
        vendedores_a_cargo = Salesman.query.filter_by(manager_id=empleado.manager.id).all()

        # Iterar sobre los vendedores y obtener las transacciones pendientes de cada uno
        for vendedor in vendedores_a_cargo:
            # Realizar una unión entre las tablas Transaction y Employee para obtener el nombre del vendedor
            query = db.session.query(Transaction, Employee).join(Employee).filter(
                Transaction.employee_id == vendedor.employee_id,
                Transaction.approval_status == ApprovalStatus.PENDIENTE
            )

            for transaccion, empleado_vendedor in query:
                # Obtener el concepto de la transacción
                concepto = Concept.query.get(transaccion.concept_id)
                # Usar imagen por defecto si no hay adjunto
                adjunto = transaccion.attachment if transaccion.attachment else 'black.png'

                # Crear un diccionario con los detalles de la transacción pendiente, incluyendo el nombre del vendedor
                detalle_transaccion = {
                    'id': transaccion.id,
                    'tipo': transaccion.transaction_types.name,
                    'concepto': concepto.name,
                    'descripcion': transaccion.description,
                    'monto': transaccion.amount,
                    'attachment': adjunto,
                    'vendedor': empleado_vendedor.user.first_name + ' ' + empleado_vendedor.user.last_name
                }

                # Agregar los detalles a la lista
                detalles_transacciones.append(detalle_transaccion)

        # Confirmar la sesión de la base de datos después de la actualización
        db.session.commit()

        return render_template('approval-expenses.html', detalles_transacciones=detalles_transacciones, user_id=user_id, user_role=user_role)

    except Exception as e:
        return jsonify({'message': 'Error interno del servidor', 'error': str(e)}), 500


upload_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'images')
if not os.path.exists(upload_folder):
    os.makedirs(upload_folder)


@routes.route('/transaction', methods=['GET', 'POST'])
def transactions():
    if 'user_id' in session and (session['role'] == 'COORDINADOR' or session['role'] == 'VENDEDOR'):
        user_id = session['user_id']
        user_role = session['role']

        # Obtener el empleado asociado al user_id
        employee = Employee.query.filter_by(user_id=user_id).first()

        # Obtener el employee_id a partir del user_id
        employee_id = Employee.query.filter_by(user_id=user_id).first().id

        transaction_type = ''  # Definir transaction_type por defecto
        concepts = []  # Definir concepts por defecto

        if request.method == 'POST':
            # Manejar la creación de la transacción
            transaction_type = request.form.get('transaction_type')

            if transaction_type != 'GASTO':
                approval_status = "APROBADA"
            else:
                approval_status = request.form.get('status')

            concept_id = request.form.get('concept_id')
            description = request.form.get('description')
            amount = request.form.get('quantity')
            # Obtener el archivo de imagen
            attachment = request.files.get('photo')

            filename = None  # Inicializar filename
            if attachment and attachment.filename:  # Verificar que se haya subido un archivo válido
                try:
                    # Importar app para acceder a la configuración
                    from flask import current_app
                    upload_folder = current_app.config['UPLOAD_FOLDER']
                    
                    # Crear nombre único para el archivo
                    filename = str(uuid.uuid4()) + '_' + secure_filename(attachment.filename)
                    
                    # Asegurar que la carpeta existe
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    # Guardar el archivo
                    file_path = os.path.join(upload_folder, filename)
                    attachment.save(file_path)
                    
                    
                except Exception as e:
                
                    filename = None
            else:
                # Si no se subió archivo, usar imagen fallback
                from flask import current_app
                upload_folder = current_app.config['UPLOAD_FOLDER']
                fallback_path = os.path.join('app', 'static', 'images', 'black_bg.png')
                fallback_filename = 'black_bg.png'
                fallback_dest = os.path.join(upload_folder, fallback_filename)
                os.makedirs(upload_folder, exist_ok=True)
                if not os.path.exists(fallback_dest):
                    import shutil
                    shutil.copyfile(fallback_path, fallback_dest)
                filename = fallback_filename

            current_date = datetime.now()

            # Usar el employee_id obtenido para crear la transacción
            transaction = Transaction(
                transaction_types=transaction_type,
                concept_id=concept_id,
                description=description,
                amount=amount,
                attachment=filename,  # Usar el nombre único del archivo
                approval_status=approval_status,
                employee_id=employee.id,
                loan_id=None,
                creation_date=current_date
            )

            db.session.add(transaction)
            db.session.commit()

            if user_role == 'VENDEDOR':
                return redirect(url_for('routes.menu_salesman', user_id=user_id))
            elif user_role == 'COORDINADOR':
                return redirect(url_for('routes.menu_manager', user_id=user_id))

        else:
            # Obtener todos los conceptos disponibles
            concepts = Concept.query.all()

            return render_template('transactions.html', concepts=concepts, user_role=user_role, user_id=user_id)
    else:
        return "Acceso no autorizado."



@routes.route('/modify-transaction/<int:transaction_id>', methods=['POST'])
def modify_transaction(transaction_id):

    try:
        with db.session.no_autoflush:
            # Obtener la transacción
            transaction = Transaction.query.get(transaction_id)

            if not transaction:
                return jsonify({'message': 'Transacción no encontrada'}), 404

            new_status = request.form.get('new_status')

            if new_status not in [ApprovalStatus.APROBADA.value, ApprovalStatus.RECHAZADA.value]:
                return jsonify({'message': 'Estado no válido'}), 400

            transaction.approval_status = ApprovalStatus(new_status)

            if transaction.loan_id:
                prestamo = Loan.query.get(transaction.loan_id)
                if prestamo:
                    if transaction.approval_status == ApprovalStatus.APROBADA:
                        prestamo.approved = True
                        generate_loan_installments(prestamo)
                    elif transaction.approval_status == ApprovalStatus.RECHAZADA:
                        prestamo.status = 0
                        cliente = Client.query.filter_by(
                            id=prestamo.client_id).first()
                        if cliente:
                            cliente.status = 0
                            db.session.add(cliente)
                else:
                    return redirect('/approval-expenses')

            employee_id = transaction.employee_id
            
            employee = Employee.query.get(employee_id)
            if not employee:
                return jsonify({'message': 'Empleado no encontrado'}), 404

            user_id = employee.user_id
            user_role = User.query.get(user_id).role

            

            TransactionType = transaction.transaction_types

            def update_box_value(employee, amount, add=True):
                current_employee = employee
                while current_employee:
                    if add:
                        current_employee.box_value += amount
                    else:
                        current_employee.box_value -= amount
                    db.session.add(current_employee)
                    current_employee = current_employee.manager.employee if current_employee.manager else None

            if user_role.value == Role.COORDINADOR:
                if TransactionType == TransactionType.INGRESO:
                    update_box_value(employee, transaction.amount, add=True)
                elif TransactionType in [TransactionType.GASTO, TransactionType.RETIRO]:
                    update_box_value(employee, transaction.amount, add=False)

            if user_role.value == Role.VENDEDOR:
                salesman = Salesman.query.filter_by(
                    employee_id=employee_id).first()
                coordinator = salesman.manager.employee
                if TransactionType == TransactionType.INGRESO:
                    employee.box_value += transaction.amount
                    db.session.add(employee)
                    update_box_value(
                        coordinator, transaction.amount, add=False)
                elif TransactionType == TransactionType.GASTO:
                    employee.box_value -= transaction.amount
                elif TransactionType == TransactionType.RETIRO:
                    employee.box_value -= transaction.amount
                    db.session.add(employee)
                    update_box_value(coordinator, transaction.amount, add=True)

            db.session.commit()

        return redirect('/approval-expenses')

    except Exception as e:
        db.session.rollback()  # Revertir cambios en caso de error
        return jsonify({'message': 'Error interno del servidor', 'error': str(e)}), 500


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
        subadmins = Manager.query.filter(Manager.employee_id != employee.id).all()

        def get_boxes_for_manager(manager):
            if not manager:
                return []
            try:
                sellers = Salesman.query.filter_by(manager_id=manager.id).all()
                boxes = []
                for seller in sellers:
                    if not seller.employee or not seller.employee.user:
                        continue
                    seller_info = {
                        'Employee ID': seller.employee.id,
                        'First Name': seller.employee.user.first_name or '',
                        'Last Name': seller.employee.user.last_name or '',
                        'Number of Active Loans': 0,
                        'Total Amount of Overdue Loans': 0,
                        'Total Amount of Pending Installments': 0,
                    }
                    clients = seller.employee.clients
                    for client in clients:
                        active_loans = Loan.query.filter_by(client_id=client.id, status=True).count()
                        seller_info['Number of Active Loans'] += active_loans
                        for loan in client.loans:
                            for installment in loan.installments:
                                if installment.status == InstallmentStatus.MORA:
                                    seller_info['Total Amount of Overdue Loans'] += float(loan.amount or 0)
                                elif installment.status == InstallmentStatus.PENDIENTE:
                                    seller_info['Total Amount of Pending Installments'] += float(installment.amount or 0)
                    boxes.append(seller_info)
                return boxes
            except Exception as e:
        
                return []

        def get_all_sellers_boxes():
            """Obtiene todas las cajas de todos los vendedores"""
            try:
                all_sellers = Salesman.query.all()
                boxes = []
                for seller in all_sellers:
                    if not seller.employee or not seller.employee.user:
                        continue
                    manager_name = 'Sin administrador'
                    if seller.manager and seller.manager.employee and seller.manager.employee.user:
                        manager_name = f"{seller.manager.employee.user.first_name or ''} {seller.manager.employee.user.last_name or ''}"
                    
                    seller_info = {
                        'Employee ID': seller.employee.id,
                        'First Name': seller.employee.user.first_name or '',
                        'Last Name': seller.employee.user.last_name or '',
                        'Manager Name': manager_name,
                        'Number of Active Loans': 0,
                        'Total Amount of Overdue Loans': 0,
                        'Total Amount of Pending Installments': 0,
                    }
                    clients = seller.employee.clients
                    for client in clients:
                        active_loans = Loan.query.filter_by(client_id=client.id, status=True).count()
                        seller_info['Number of Active Loans'] += active_loans
                        for loan in client.loans:
                            for installment in loan.installments:
                                if installment.status == InstallmentStatus.MORA:
                                    seller_info['Total Amount of Overdue Loans'] += float(loan.amount or 0)
                                elif installment.status == InstallmentStatus.PENDIENTE:
                                    seller_info['Total Amount of Pending Installments'] += float(installment.amount or 0)
                    boxes.append(seller_info)
                return boxes
            except Exception as e:
        
                return []

        def get_only_sellers_boxes():
            """Obtiene solo las cajas de vendedores que pertenecen directamente al administrador principal"""
            try:
                if not main_admin:
                    return []
                all_sellers = Salesman.query.all()
                boxes = []
                for seller in all_sellers:
                    # Verificar que el vendedor no sea un manager (sub-administrador)
                    is_manager = Manager.query.filter_by(employee_id=seller.employee.id).first()
                    if not is_manager:  # Solo incluir si NO es un manager
                        # Verificar que el vendedor pertenezca directamente al administrador principal
                        if seller.manager_id == main_admin.id:
                            if not seller.employee or not seller.employee.user:
                                continue
                            manager_name = 'Sin administrador'
                            if seller.manager and seller.manager.employee and seller.manager.employee.user:
                                manager_name = f"{seller.manager.employee.user.first_name or ''} {seller.manager.employee.user.last_name or ''}"
                            
                            seller_info = {
                                'Employee ID': seller.employee.id,
                                'First Name': seller.employee.user.first_name or '',
                                'Last Name': seller.employee.user.last_name or '',
                                'Manager Name': manager_name,
                                'Number of Active Loans': 0,
                                'Total Amount of Overdue Loans': 0,
                                'Total Amount of Pending Installments': 0,
                            }
                            clients = seller.employee.clients
                            for client in clients:
                                active_loans = Loan.query.filter_by(client_id=client.id, status=True).count()
                                seller_info['Number of Active Loans'] += active_loans
                                for loan in client.loans:
                                    for installment in loan.installments:
                                        if installment.status == InstallmentStatus.MORA:
                                            seller_info['Total Amount of Overdue Loans'] += float(loan.amount or 0)
                                        elif installment.status == InstallmentStatus.PENDIENTE:
                                            seller_info['Total Amount of Pending Installments'] += float(installment.amount or 0)
                            boxes.append(seller_info)
                return boxes
            except Exception as e:
        
                return []

        # Obtener todas las cajas de todos los vendedores
        all_sellers_boxes = get_all_sellers_boxes()
        
        # Cajas del admin principal - incluir solo las cajas de vendedores (no sub-administradores)
        if main_admin:
            # Si es el administrador principal, mostrar solo las cajas de vendedores
            main_admin_boxes = get_only_sellers_boxes()
        else:
            main_admin_boxes = []
        
        # Cajas de subadmins
        subadmins_list = []
        for subadmin in subadmins:
            if subadmin.employee and subadmin.employee.user:
                subadmins_list.append({
                    'name': f"{subadmin.employee.user.first_name or ''} {subadmin.employee.user.last_name or ''}",
                    'boxes': get_boxes_for_manager(subadmin)
                })

        # Totales generales usando solo las cajas de vendedores (no sub-administradores)
        only_sellers_boxes = get_only_sellers_boxes()
        total_cash = sum([b.get('Total Amount of Pending Installments', 0) for b in only_sellers_boxes])
        total_active_sellers = len(only_sellers_boxes)

        # Porcentaje de recaudación del día (puedes ajustar la lógica si es necesario)
        try:
            paid_installments = LoanInstallment.query.filter_by(status=InstallmentStatus.PAGADA).count()
            debt_balance = total_cash
            day_collection = (paid_installments / debt_balance) * 100 if debt_balance > 0 else 0
        except Exception as e:
    
            day_collection = 0

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
            'all_sellers': all_sellers_boxes,  # Agregar todas las cajas de vendedores
            'Total Cash Value': str(total_cash),
            'Total Sellers with Active Loans': total_active_sellers,
            'Percentage of Day Collection': f'{day_collection:.2f}%',
            'Debt Balance': str(debt_balance)
        }

        return render_template('wallet.html', wallet_data=wallet_data, user_id=user_id)
    except Exception as e:

        return jsonify({'message': 'Error interno del servidor', 'error': str(e)}), 500


@routes.route('/wallet-detail/<int:employee_id>', methods=['GET'])
def wallet_detail(employee_id):
    show_all = request.args.get('show_all', '0') == '1'
    # Obtener el empleado
    employee = Employee.query.filter_by(id=employee_id).first()
    if not employee:
        return jsonify({'message': 'Empleado no encontrado'}), 404

    # Inicializar variables
    total_loans = 0
    total_overdue_amount = 0
    loans_detail = []

    # Obtener préstamos según el toggle
    if show_all:
        loans = Loan.query.all()
    else:
        loans = Loan.query.filter_by(status=True).all()

    for loan in loans:
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
        for installment in loan.installments:
            total_loan_amount += float(installment.amount)
            if installment.status == InstallmentStatus.MORA:
                total_overdue_amount_loan += float(installment.amount)
                total_overdue_installments_loan += 1
            elif installment.status == InstallmentStatus.PAGADA:
                total_paid_installments_loan += 1
        # Detalle de cada préstamo
        loan_info = {
            'Seller First Name': seller.employee.user.first_name,
            'Seller Last Name': seller.employee.user.last_name,
            'Client First Name': client.first_name,
            'Client Last Name': client.last_name,
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
    # Crear un diccionario con los datos solicitados
    wallet_detail_data = {
        'Total Loans': total_loans,
        'Total Overdue Amount': str(total_overdue_amount),
        'Loans Detail': loans_detail,
    }
    return render_template('wallet-detail.html', wallet_detail_data=wallet_detail_data, user_id=employee_id, show_all=show_all)


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

        # Obtener todas las transacciones asociadas a este empleado
        transacciones = Transaction.query.filter(
            Transaction.employee_id == empleado.id
        ).all()

        # Crear una lista para almacenar los detalles de las transacciones
        detalles_transacciones = []

        for transaccion in transacciones:
            # Obtener el concepto de la transacción
            concepto = Concept.query.get(transaccion.concept_id)

            # Crear un diccionario con los detalles de la transacción
            detalle_transaccion = {
                'id': transaccion.id,
                'tipo': transaccion.transaction_types.name,
                'concepto': concepto.name,
                'descripcion': transaccion.description,
                'monto': transaccion.amount,
                'attachment': transaccion.attachment,
                'status': transaccion.approval_status.value
            }
            

            # Agregar los detalles a la lista
            detalles_transacciones.append(detalle_transaccion)

        return render_template('list-expenses.html', detalles_transacciones=detalles_transacciones, user_role=user_role, user_id=user_id)

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
        if loan_date == datetime.today().date() and loan.is_renewal == 0:  # Verificar si el préstamo se realizó hoy
            loan_detail = {
                'client_name': loan.client.first_name + ' ' + loan.client.last_name,
                'loan_amount': loan.amount,
                'loan_dues': loan.dues,
                'loan_interest': loan.interest,
                # Agregar la fecha del préstamo
                'loan_date': loan_date.strftime('%d/%m/%Y')
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
    transactions = Transaction.query.filter_by(
        employee_id=employee_id).order_by(Transaction.creation_date.desc()).all()

    # Filtrar transacciones por tipo y fecha
    today = datetime.today().date()
    expenses = [trans for trans in transactions if
                trans.transaction_types == TransactionType.GASTO and trans.creation_date.date() == today]
    incomes = [trans for trans in transactions if
               trans.transaction_types == TransactionType.INGRESO and trans.creation_date.date() == today]
    withdrawals = [trans for trans in transactions if
                   trans.transaction_types == TransactionType.RETIRO and trans.creation_date.date() == today]

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
                            'total_loan_amount': loan.amount,
                            'loan_id': loan.id
                        }
                        clients_in_arrears.append(client_arrears)

    # Obtener todos los pagos realizados hoy
    payments_today = Payment.query.join(LoanInstallment).join(Loan).join(Employee).filter(Employee.id == employee_id,
                                                                                          func.date(
                                                                                              Payment.payment_date) == today).all()

    # Recopilar detalles de los pagos realizados hoy
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
                           user_role=user_role,
                           loan_id=loan_id,
                           installment_id=installment_id,
                           user_id=user_id)



@routes.route('/debtor-manager')
def debtor_manager():
    debtors_info = []
    total_mora = 0
    user_id = session.get('user_id')

    # Obtener todos los coordinadores
    coordinators = Manager.query.all()

    for coordinator in coordinators:
        # Obtener todos los vendedores asociados al coordinador
        salesmen = Salesman.query.filter_by(manager_id=coordinator.id).all()

        for salesman in salesmen:
            # Obtener todos los clientes morosos del vendedor
            debtors = Client.query.filter(
                Client.employee_id == salesman.employee_id, Client.debtor == True).all()

            for debtor in debtors:
                # Calcular la información requerida para cada cliente moroso
                loan = Loan.query.filter_by(client_id=debtor.id).first()
                
                if loan:
                    total_loan_amount = loan.amount + \
                        (loan.amount * loan.interest / 100)

                    # Obtener todas las cuotas de préstamo asociadas a este préstamo
                    loan_installments = LoanInstallment.query.filter_by(
                        loan_id=loan.id).all()
                    
                    # Calcular la mora
                    total_due = sum(installment.amount for installment in loan_installments if
                                    installment.status == InstallmentStatus.MORA)
                    

                    total_mora += total_due

                    # Verificar si el cliente está en mora
                    if total_due > 0:
                        overdue_installments = len([installment for installment in loan_installments if
                                                    installment.status == InstallmentStatus.MORA])
                        total_installments = len(loan_installments)
                        last_installment_date = max(
                            installment.due_date for installment in loan_installments)
                        last_payment_date = max(payment.payment_date for installment in loan_installments for payment in
                                                installment.payments)

                        # Calcular el saldo pendiente
                        total_payment = sum(
                            payment.amount for installment in loan.installments for payment in installment.payments)
                        balance = total_loan_amount - total_payment

                        debtor_info = {
                            'salesman_name': f"{salesman.employee.user.first_name} {salesman.employee.user.last_name}",
                            'client_name': f"{debtor.first_name} {debtor.last_name}",
                            'total_loan_amount': total_loan_amount,
                            'balance': balance,
                            'total_due': total_due,
                            'overdue_installments': overdue_installments,
                            'total_installments': total_installments,
                            'last_installment_date': last_installment_date,
                            'last_payment_date': last_payment_date
                        }

                        debtors_info.append(debtor_info)


    return render_template('debtor-manager.html', debtors_info=debtors_info, total_mora=total_mora, user_id=user_id)


@routes.route('/add-employee-record/<int:employee_id>', methods=['POST'])
def add_employee_record(employee_id):
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

        # Inicializar variables para el nuevo cálculo
        total_pending_installments_amount = 0
        total_pending_installments_loan_close_amount = 0
        
        # Calcular el debido cobrar del siguiente dia y préstamos cerrados
        for client in employee.clients:
            for loan in client.loans:
                # Excluir préstamos creados hoy mismo
                if loan.creation_date.date() == datetime.now().date():
                    continue
                
                if loan.status:
                    # Encuentra la última cuota pendiente a la fecha actual incluyendo la fecha de creación de la cuota
                    pending_installment = LoanInstallment.query.filter(
                        LoanInstallment.loan_id == loan.id
                    ).order_by(LoanInstallment.due_date.asc()).first()
                    if pending_installment:
                        total_pending_installments_amount += pending_installment.fixed_amount
                elif loan.status == False and loan.up_to_date and loan.modification_date.date() == datetime.now().date():
                    pending_installment_paid = LoanInstallment.query.filter(
                        LoanInstallment.loan_id == loan.id
                    ).order_by(LoanInstallment.due_date.asc()).first()
                    total_pending_installments_loan_close_amount += pending_installment_paid.fixed_amount

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

        # Obtener la cantidad de transacciones pendientes del vendedor
        pending_transactions = Transaction.query.filter(
            Transaction.employee_id == employee_id,
            Transaction.approval_status == ApprovalStatus.PENDIENTE
        ).count()

        # Obtener los IDs de las transacciones pendientes del vendedor
        pending_transaction_ids = Transaction.query.filter(
            Transaction.employee_id == employee_id,
            Transaction.approval_status == ApprovalStatus.PENDIENTE
        ).with_entities(Transaction.id).all()

        

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
            # Loan.creation_date <= datetime.now(),
            Loan.is_renewal == False  # Excluir renovaciones
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
                due_to_charge=total_pending_installments_loan_close_amount+total_pending_installments_amount,
                closing_total=Decimal(initial_state)
                + int(paid_installments)
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

    return redirect(url_for('routes.box'))


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

    return redirect(url_for('routes.box'))


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
            Loan.is_renewal == False  # Excluir renovaciones
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


@routes.route('/payments/edit/<int:loan_id>', methods=['POST'])
def edit_payment(loan_id):
    
    # Obtener el ID del usuario desde la sesión
    user_id = session.get('user_id')

    # Buscar el empleado asociado al usuario
    employee = Employee.query.filter_by(user_id=user_id).first()
    if not employee:
        return jsonify({'message': 'Empleado no encontrado'}), 404
    employee_id = employee.id

    # Obtener datos del formulario
    installment_number = request.form.get('InstallmentId')
    custom_payment = float(request.form.get('customPayment'))

    # Aumentar el valor en caja del empleado
    employee.box_value += Decimal(custom_payment)

    # Buscar el préstamo asociado
    loan = Loan.query.get(loan_id)
    if not loan:
        return jsonify({'message': 'Préstamo no encontrado'}), 404
    client = loan.client
    current_date = datetime.now().date()

    # 📌 **Registrar el nuevo pago**
    new_payment_value = custom_payment

    # 🔄 **Revertir pagos hechos hoy**
    installments_paid_today = LoanInstallment.query.filter(
        LoanInstallment.loan_id == loan_id,
        (func.date(LoanInstallment.payment_date) == current_date) | (LoanInstallment.payment_date == None),
        LoanInstallment.status.in_([InstallmentStatus.PAGADA, InstallmentStatus.ABONADA])
    ).all()

    for installment in installments_paid_today:
        if installment.status == InstallmentStatus.PAGADA:
            # ✅ Restaurar el monto original en cuotas pagadas completamente
            installment.amount = installment.fixed_amount
        elif installment.status == InstallmentStatus.ABONADA:
            # ✅ Restaurar el monto original en cuotas abonadas
            installment.amount = installment.fixed_amount
            
        installment.status = InstallmentStatus.PENDIENTE  # Volver a estado pendiente
        installment.payment_date = None  # Eliminar la fecha de pago

    db.session.commit()

    # 🔥 **Eliminar pagos hechos hoy**
    Payment.query.filter(
        Payment.installment_id.in_([i.id for i in installments_paid_today]),
        func.date(Payment.payment_date) == current_date,
        loan_id == loan_id
    ).delete(synchronize_session=False)

    db.session.commit()

    # 🔢 **Calcular el total adeudado considerando pagos previos**
    total_amount_due = 0
    
    for installment in loan.installments:
        if installment.status in [InstallmentStatus.PENDIENTE, InstallmentStatus.MORA, InstallmentStatus.ABONADA]:
            # Calcular cuánto se debe realmente de esta cuota
            # Sumar todos los pagos previos (excluyendo los del día actual que ya fueron eliminados)
            total_paid_for_installment = db.session.query(func.sum(Payment.amount)).filter(
                Payment.installment_id == installment.id,
                func.date(Payment.payment_date) != current_date
            ).scalar() or Decimal('0')
            
            # El monto adeudado es el monto fijo menos lo ya pagado
            amount_due_for_installment = installment.fixed_amount - total_paid_for_installment
            
            # Si la cuota ya está completamente pagada, no se incluye en el total
            if amount_due_for_installment > 0:
                total_amount_due += amount_due_for_installment
                # Actualizar el monto pendiente de la cuota
                installment.amount = amount_due_for_installment
            else:
                # La cuota ya está pagada completamente
                installment.status = InstallmentStatus.PAGADA
                installment.amount = Decimal('0')
                installment.payment_date = datetime.now().date()

    db.session.commit()

    # Cuando el valor de pago es mayor o igual al total de las cuotas pendientes
    if custom_payment >= total_amount_due:
        # Marcar todas las cuotas pendientes como "PAGADA" y actualizar la fecha de pago
        for installment in loan.installments:
            if installment.status in [InstallmentStatus.PENDIENTE, InstallmentStatus.MORA, InstallmentStatus.ABONADA]:
                # Calcular cuánto se debe realmente de esta cuota
                total_paid_for_installment = db.session.query(func.sum(Payment.amount)).filter(
                    Payment.installment_id == installment.id,
                    func.date(Payment.payment_date) != current_date
                ).scalar() or Decimal('0')
                
                amount_due_for_installment = installment.fixed_amount - total_paid_for_installment
                
                if amount_due_for_installment > 0:
                    installment.status = InstallmentStatus.PAGADA
                    installment.payment_date = datetime.now().date()
                    installment.amount = Decimal('0')
                    
                    # Crear el pago asociado a esta cuota por el monto pendiente
                    payment = Payment(
                        amount=amount_due_for_installment, 
                        payment_date=datetime.now(), 
                        installment_id=installment.id
                    )
                    db.session.add(payment)
        
        # Actualizar el estado del préstamo y el campo up_to_date
        loan.status = False  # 0 indica que el préstamo está pagado en su totalidad
        loan.up_to_date = True
        db.session.commit()
        return jsonify({"message": "Todas las cuotas han sido pagadas correctamente."}), 200
        
    else:
        # Lógica para manejar el pago parcial
        remaining_payment = Decimal(custom_payment)
        
        for installment in loan.installments:
            if remaining_payment <= 0:
                break
                
            if installment.status in [InstallmentStatus.PENDIENTE, InstallmentStatus.MORA, InstallmentStatus.ABONADA]:
                # Calcular cuánto se debe realmente de esta cuota
                total_paid_for_installment = db.session.query(func.sum(Payment.amount)).filter(
                    Payment.installment_id == installment.id,
                    func.date(Payment.payment_date) != current_date
                ).scalar() or Decimal('0')
                
                amount_due_for_installment = installment.fixed_amount - total_paid_for_installment
                
                if amount_due_for_installment > 0:
                    if remaining_payment >= amount_due_for_installment:
                        # Se completa la cuota
                        installment.status = InstallmentStatus.PAGADA
                        installment.payment_date = datetime.now().date()
                        installment.amount = Decimal('0')
                        
                        payment = Payment(
                            amount=amount_due_for_installment, 
                            payment_date=datetime.now(), 
                            installment_id=installment.id
                        )
                        db.session.add(payment)
                        remaining_payment -= amount_due_for_installment
                    else:
                        # Solo se abona una parte
                        installment.status = InstallmentStatus.ABONADA
                        installment.amount = amount_due_for_installment - remaining_payment
                        
                        payment = Payment(
                            amount=remaining_payment, 
                            payment_date=datetime.now(), 
                            installment_id=installment.id
                        )
                        db.session.add(payment)
                        remaining_payment = Decimal('0')
        
        client.debtor = False
        db.session.commit()

    # Redirigir a la vista de detalles de caja del empleado
    return redirect(url_for('routes.box_detail', employee_id=employee_id))



@routes.route('/history-box', methods=['POST', 'GET'])
def history_box():

    # obtiene el ID del usuario desde la sesión
    user_id = session.get('user_id')

    if request.method == 'POST':
        filter_date = request.form.get('filter_date')
    else:
        filter_date = datetime.now().date()

    if user_id is None:
        return jsonify({'message': 'Usuario no encontrado en la sesión'}), 401

    # Verificar si el usuario es un coordinador
    user = User.query.get(user_id)
    if user is None or user.role != Role.COORDINADOR:
        return jsonify({'message': 'El usuario no es un coordinador válido'}), 403

    # Obtener la información de la caja del coordinador
    coordinator = Employee.query.filter_by(user_id=user_id).first()
    coordinator_name = f"{user.first_name} {user.last_name}"

    if filter_date != None:
        coordinator_cash = db.session.query(
            func.sum(EmployeeRecord.closing_total)
        ).filter(
            EmployeeRecord.employee_id == coordinator.id,
            func.date(EmployeeRecord.creation_date) == filter_date
        ).scalar() or 0
    else:
        coordinator_cash = coordinator.box_value

    # Obtener el ID del manager del coordinador
    manager_id = db.session.query(Manager.id).filter_by(
        employee_id=coordinator.id).scalar()

    if not manager_id:
        return jsonify({'message': 'No se encontró ningún coordinador asociado a este empleado'}), 404

    # Filtrar las transacciones INGRESO de los Saleman para el día filtrado = RETIROS COORDINADOR.
    total_outbound_amount = db.session.query(
        func.sum(Transaction.amount).label('total_amount'),
        Salesman.manager_id
    ).join(Salesman, Transaction.employee_id == Salesman.employee_id).filter(
        Transaction.transaction_types == 'INGRESO',
        Transaction.approval_status == 'APROBADA',
        # Filtrar por fecha actual
        func.date(Transaction.creation_date) == filter_date
    ).group_by(Salesman.manager_id).all()

    # Filtrar las transacciones INGRESO de los Saleman para el día filtrado = INGRESOS COORDINADOR.
    total_inbound_amount = db.session.query(
        func.sum(Transaction.amount).label('total_amount'),
        Salesman.manager_id
    ).join(Salesman, Transaction.employee_id == Salesman.employee_id).filter(
        Transaction.transaction_types == 'RETIRO',
        Transaction.approval_status == 'APROBADA',
        # Filtrar por fecha actual
        func.date(Transaction.creation_date) == filter_date
    ).group_by(Salesman.manager_id).all()

    # Obtener los gastos del coordinador
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

    # Construir la respuesta como variables separadas
    coordinator_box = {
        'maximum_cash': coordinator_cash,
        'total_outbound_amount': float(total_outbound_amount[0][0]) if total_outbound_amount else 0,
        'total_inbound_amount': float(total_inbound_amount[0][0]) if total_inbound_amount else 0,
        'total_expenses': float(total_expenses),
        'expense_details': manager_expense_details
    }

    # Obtener todos los vendedores asociados al coordinador
    salesmen = Salesman.query.filter_by(manager_id=manager_id).all()

    # Inicializa la lista para almacenar las estadísticas de los vendedores
    salesmen_stats = []

    for salesman in salesmen:
        # Inicializa las variables para almacenar las estadísticas de cada vendedor
        total_collections_today = 0  # Recaudo Diario
        daily_collections_count = 0  # Cantidad Recaudos Diarios
        daily_expenses_count = 0  # Gastos Diarios
        daily_expenses_amount = 0  # Valor Gastos Diarios
        daily_withdrawals_amount = 0  # Retiros Diarios
        daily_withdrawals_count = 0  # Cantidad Retiros Diarios
        daily_incomes_amount = 0  # Ingresos Diarios
        daily_incomes_count = 0  # Cantidad Ingresos Diarios
        new_clients_loan = 0  # Clientes Nuevos
        new_clients_loan_amount = 0  # Valor Prestamos Nuevos
        total_renewal_loans = 0  # Cantidad de Renovaciones
        total_renewal_loans_amount = 0  # Valor Total Renovaciones
        customers_in_arrears = 0  # Clientes en MORA o NO PAGO
        total_customers = 0  # Clientes Totales (Activos)
        total_pending_installments_amount = 0  # Monto total de cuotas pendientes
        box_value = 0  # Valor de la caja del vendedor
        initial_box_value = 0
        loans_to_collect = 0

        # Obtener el valor de la caja del vendedor
        employee = Employee.query.get(salesman.employee_id)
        employee_id = employee.id
        employee_status = salesman.employee.status
        
        # Obtener el rol del empleado
        employee_userid = User.query.get(employee.user_id)
        role_employee = employee_userid.role.value

        # Obtener el valor inicial de la caja del vendedor
        employee_records = EmployeeRecord.query.filter(
            EmployeeRecord.employee_id == salesman.employee_id,
            func.date(EmployeeRecord.creation_date) == filter_date
        ).order_by(EmployeeRecord.id.desc()).first()

        if employee_records:
            initial_box_value = float(employee_records.closing_total)
        else:
            initial_box_value = float(employee.box_value)

            # Verificar si todos los préstamos tienen un PAGO, ABONO o MORA igual al de hoy
        all_loans_paid = Loan.query.filter_by(employee_id=employee_id).all()
        all_loans_paid_today = False
        all_loans_paid_count = 0
        for loan in all_loans_paid:
            loan_installments = LoanInstallment.query.filter_by(
                loan_id=loan.id).all()
            for installment in loan_installments:
                payments = Payment.query.filter_by(
                    installment_id=installment.id).all()
                for payment in payments:
                    if payment.payment_date.date() == filter_date:
                        all_loans_paid_count += 1
                        break

        if loans_to_collect == all_loans_paid_count:
            all_loans_paid_today = True

        # Calcula el total de cobros para el día con estado "PAGADA"
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

        # Calcula la cantidad de cobros para el día con estado "PAGADA"
        daily_collections_count = db.session.query(
            func.count(Payment.id)
        ).join(
            LoanInstallment, Payment.installment_id == LoanInstallment.id
        ).join(
            Loan, LoanInstallment.loan_id == Loan.id
        ).filter(
            Loan.client.has(employee_id=salesman.employee_id),
            func.date(Payment.payment_date) == filter_date
        ).scalar() or 0

        # Obtener el EmployeeRecord para la fecha filtrada
        employee_record = EmployeeRecord.query.filter(
            EmployeeRecord.employee_id == salesman.employee_id,
            func.date(EmployeeRecord.creation_date) == filter_date
        ).order_by(EmployeeRecord.id.desc()).first()
        
        # Si existe un EmployeeRecord para esta fecha, usar due_to_charge como valor principal
        if employee_record and employee_record.due_to_charge:
            from decimal import Decimal
            total_pending_installments_amount = Decimal(str(employee_record.due_to_charge))
        else:
            # Si no existe EmployeeRecord, calcular las cuotas pendientes manualmente
            for client in employee.clients:
                for loan in client.loans:
                    if loan.status:
                        pending_installment = LoanInstallment.query.filter(
                            LoanInstallment.loan_id == loan.id,
                            func.date(LoanInstallment.due_date) == filter_date,
                        ).order_by(LoanInstallment.due_date.asc()).first()
                        if pending_installment:
                            total_pending_installments_amount += pending_installment.fixed_amount

        # Calcula la cantidad de nuevos clientes registrados en el día
        new_clients_loan = Client.query.filter(
            Client.employee_id == salesman.employee_id,
            func.date(Client.creation_date) == filter_date,
        ).count()

        # Calcula el total de préstamos de los nuevos clientes
        new_clients_loan_amount = Loan.query.join(Client).filter(
            Client.employee_id == salesman.employee_id,
            func.date(Loan.creation_date) == filter_date,
            Loan.is_renewal == False  # Excluir renovaciones
        ).with_entities(func.sum(Loan.amount)).scalar() or 0

        # Calcula el total de renovaciones para el día actual para este vendedor
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

        # Calcula Valor de los GASTOS diarios
        daily_expenses_amount = Transaction.query.filter(
            Transaction.employee_id == salesman.employee_id,
            Transaction.transaction_types == TransactionType.GASTO,
            Transaction.approval_status == ApprovalStatus.APROBADA,
            func.date(Transaction.creation_date) == filter_date
        ).with_entities(func.sum(Transaction.amount)).scalar() or 0

        # Calcula el número de transacciones de GASTOS diarios
        daily_expenses_count = Transaction.query.filter(
            Transaction.employee_id == salesman.employee_id,
            Transaction.transaction_types == TransactionType.GASTO,
            Transaction.approval_status == ApprovalStatus.APROBADA,
            # Filtrar por fecha actual
            func.date(Transaction.creation_date) == filter_date
        ).count() or 0

        # Calcula los retiros diarios basados en transacciones de RETIRO
        daily_withdrawals_amount = Transaction.query.filter(
            Transaction.employee_id == salesman.employee_id,
            Transaction.transaction_types == TransactionType.RETIRO,
            Transaction.approval_status == ApprovalStatus.APROBADA,
            # Filtrar por fecha actual
            func.date(Transaction.creation_date) == filter_date
        ).with_entities(func.sum(Transaction.amount)).scalar() or 0

        daily_withdrawals_count = Transaction.query.filter(
            Transaction.employee_id == salesman.employee_id,
            Transaction.transaction_types == TransactionType.RETIRO,
            Transaction.approval_status == ApprovalStatus.APROBADA,
            # Filtrar por fecha actual
            func.date(Transaction.creation_date) == filter_date
        ).count() or 0

        # Calcula las colecciones diarias basadas en transacciones de INGRESO
        daily_incomes_amount = Transaction.query.filter(
            Transaction.employee_id == salesman.employee_id,
            Transaction.transaction_types == TransactionType.INGRESO,
            Transaction.approval_status == ApprovalStatus.APROBADA,
            # Filtrar por fecha actual
            func.date(Transaction.creation_date) == filter_date
        ).with_entities(func.sum(Transaction.amount)).scalar() or 0

        daily_incomes_count = Transaction.query.filter(
            Transaction.employee_id == salesman.employee_id,
            Transaction.transaction_types == TransactionType.INGRESO,
            Transaction.approval_status == ApprovalStatus.APROBADA,
            # Filtrar por fecha actual
            func.date(Transaction.creation_date) == filter_date
        ).count() or 0

        # Obtener detalles de gastos, ingresos y retiros asociados a ese vendedor y ordenar por fecha de creación descendente
        transactions = Transaction.query.filter_by(
            employee_id=employee_id).order_by(Transaction.creation_date.desc()).all()

        # Filtrar transacciones por tipo y fecha
        expenses = [trans for trans in transactions if
                    trans.transaction_types == TransactionType.GASTO and func.date(trans.creation_date.date()) == filter_date]
        incomes = [trans for trans in transactions if
                   trans.transaction_types == TransactionType.INGRESO and trans.approval_status == ApprovalStatus.APROBADA and func.date(trans.creation_date.date()) == filter_date]
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

        # Clientes morosos para el día
        customers_in_arrears = sum(
            1 for client in salesman.employee.clients
            for loan in client.loans
            for installment in loan.installments
            if loan.status and installment.status == InstallmentStatus.MORA
            for payment in installment.payments
            if payment.payment_date.date() == filter_date
        )

        box_value = initial_box_value + float(total_collections_today) - float(daily_withdrawals_amount) - float(
            daily_expenses_amount) + float(daily_incomes_amount) - float(new_clients_loan_amount) - float(total_renewal_loans_amount)

        salesman_data = {
            'salesman_name': f'{salesman.employee.user.first_name} {salesman.employee.user.last_name}',
            'employee_id': salesman.employee_id,
            'employee_status': employee_status,
            'role_employee': role_employee,
            'total_collections_today': total_collections_today,
            'new_clients': new_clients_loan,
            'daily_expenses': daily_expenses_count,
            'daily_expenses_amount': daily_expenses_amount,
            'daily_withdrawals': daily_withdrawals_amount,
            'daily_collections_made': daily_incomes_amount,
            'total_number_of_customers': total_customers,
            'customers_in_arrears_for_the_day': customers_in_arrears,
            'total_renewal_loans': total_renewal_loans,
            'total_new_clients_loan_amount': new_clients_loan_amount,
            'total_renewal_loans_amount': total_renewal_loans_amount,
            'daily_withdrawals_count': daily_withdrawals_count,
            'daily_collection_count': daily_incomes_count,
            'total_pending_installments_amount': total_pending_installments_amount,
            'all_loans_paid_today': all_loans_paid_today,
            'total_clients_collected': daily_collections_count,
            'box_value': box_value,
            'initial_box_value': initial_box_value,
            'expense_details': expense_details,
            'income_details': income_details,
            'withdrawal_details': withdrawal_details
        }

        salesmen_stats.append(salesman_data)

    # Obtener el término de búsqueda
    search_term = request.args.get('salesman_name')

    # Inicializar search_term como cadena vacía si es None
    search_term = search_term if search_term else ""

    # Realizar la búsqueda en la lista de salesmen_stats si hay un término de búsqueda
    if search_term:
        salesmen_stats = [salesman for salesman in salesmen_stats if
                          search_term.lower() in salesman['salesman_name'].lower()]

    # Renderizar la plantilla con las variables
    return render_template('history-box.html', coordinator_box=coordinator_box, salesmen_stats=salesmen_stats,
                           search_term=search_term, filter_date=filter_date, manager_id=manager_id, coordinator_name=coordinator_name, user_id=user_id, expense_details=expense_details, total_expenses=total_expenses)





@routes.route('/add-manager-record')
def add_manager_record():
    users_manager = User.query.filter_by(role=Role.COORDINADOR).all()
    users_salesman = User.query.filter_by(role=Role.VENDEDOR).all()
    current_date = datetime.now().date()
    tomorrow = datetime.now().date() + timedelta(days=1)

    for user in users_manager:
        user_id = user.id
        manager_array = Employee.query.filter_by(user_id=user_id).first()
        manager_id = manager_array.id
        

        # Verificar si ya existe un registro para este empleado en la fecha actual
        existing_record = EmployeeRecord.query.filter_by(employee_id=manager_id) \
            .filter(func.date(EmployeeRecord.creation_date) == current_date).first()
        
        if existing_record:
    
            continue

        # Inicializar las variables
        initial_state = 0.0
        loans_to_collect = 0
        paid_installments = 0
        partial_installments = 0
        overdue_installments_total = 0
        daily_incomes_amount = 0
        daily_expenses_amount = 0
        daily_withdrawals = 0
        total_collected = 0
        new_clients_loan_amount = 0
        total_renewal_loans_amount = 0
        total_pending_installments_amount = 0

        # Buscar el último registro en EmployeeRecord del día anterior
        last_record = EmployeeRecord.query.filter_by(employee_id=manager_id) \
            .filter(func.date(EmployeeRecord.creation_date) <= current_date) \
            .order_by(EmployeeRecord.creation_date.desc()).first()
            
            
        # Obtener el valor de la caja del manager
        manager_box_value = manager_array.box_value

        # Usar el valor de la caja del manager como el estado inicial
        initial_state = manager_box_value
        

        # Obtener Gastos del Coordinador
        transaction_expenses_today = Transaction.query.filter_by(employee_id=manager_id, transaction_types=TransactionType.GASTO,
                                                                 approval_status=ApprovalStatus.APROBADA).filter(func.date(Transaction.creation_date) == current_date).all()

        transaction_incomes_today = Transaction.query.filter_by(employee_id=manager_id, transaction_types=TransactionType.INGRESO,
                                                                approval_status=ApprovalStatus.APROBADA).filter(func.date(Transaction.creation_date) == current_date).all()

        transaction_withdrawals_today = Transaction.query.filter_by(employee_id=manager_id, transaction_types=TransactionType.RETIRO,
                                                                    approval_status=ApprovalStatus.APROBADA).filter(func.date(Transaction.creation_date) == current_date).all()

        # Inicializar acumuladores
        total_employee_incomes_amount = 0
        total_employee_withdrawals_amount = 0

        # Obtener todos los vendedores asociados al coordinador
        salesmen = Salesman.query.filter_by(manager_id=manager_id).all()


        for salesman in salesmen:
            employee_id = salesman.employee_id
            employee = Employee.query.get(employee_id)

            # Transacciones de tipo ingreso y aprobadas
            transaction_withdrawals = Transaction.query.filter_by(employee_id=employee_id, transaction_types=TransactionType.INGRESO,
                                                                  approval_status=ApprovalStatus.APROBADA).filter(func.date(Transaction.creation_date) == current_date).all()
            transaction_incomes = Transaction.query.filter_by(employee_id=employee_id, transaction_types=TransactionType.RETIRO,
                                                              approval_status=ApprovalStatus.APROBADA).filter(func.date(Transaction.creation_date) == current_date).all()

            # Obtener INGRESOS del Vendedor = RETIROS
            employee_withdrawals_amount = sum(
                transaction.amount for transaction in transaction_withdrawals)

            # Obtener RETIROS del Vendedor = INGRESOS
            employee_incomes_amount = sum(
                transaction.amount for transaction in transaction_incomes)

            # Acumular los valores
            total_employee_withdrawals_amount += float(
                employee_withdrawals_amount)
            total_employee_incomes_amount += float(employee_incomes_amount)

        # Valor total de INGRESOS Coordinador
        daily_incomes_amount = float(sum(
            transaction.amount for transaction in transaction_incomes_today)) + float(total_employee_incomes_amount)

        # Valor total de RETIROS Coordinador
        daily_withdrawals_amount = float(sum(
            transaction.amount for transaction in transaction_withdrawals_today)) + float(total_employee_withdrawals_amount)

        # Valor total de GASTOS Coordinador
        daily_expenses_amount = float(
            sum(transaction.amount for transaction in transaction_expenses_today))

        # Usar el cierre de caja del último registro como el estado inicial, si existe
        # if last_record:
        #     initial_state = float(last_record.closing_total) + daily_incomes_amount + total_employee_incomes_amount

        employee_record = EmployeeRecord(
            employee_id=manager_id,
            initial_state=initial_state,
            incomings=daily_incomes_amount,
            expenses=daily_expenses_amount,
            withdrawals=daily_withdrawals_amount,
            closing_total=float(initial_state) + float(daily_incomes_amount)
            - float(new_clients_loan_amount)
            - float(total_renewal_loans_amount)
            - float(daily_withdrawals_amount)
            - float(daily_expenses_amount),  # Calcular el cierre de caja
            creation_date=datetime.now(),
            loans_to_collect=loans_to_collect,  # NO SE USA
            paid_installments=paid_installments,  # NO SE USA
            partial_installments=partial_installments,  # NO SE USA
            overdue_installments=overdue_installments_total,  # NO SE USA
            sales=new_clients_loan_amount,  # NO SE USA
            renewals=total_renewal_loans_amount,  # NO SE USA
            due_to_collect_tomorrow=total_pending_installments_amount,  # NO SE USA
            total_collected=total_collected  # NO SE USA
        )
        
        # Actualizar el valor de box_value del modelo Employee
        # Obtener todos los vendedores asociados al coordinador

        # Actualizar el valor de box_value del modelo Employee
        manager = Employee.query.get(manager_id)
        if manager:
            manager.box_value = employee_record.closing_total
            db.session.add(manager)
            

        # # Actualizar el valor de box_value del modelo Employee
        # employee = Employee.query.get(manager_id)
        # if employee:
        #     employee.box_value = employee_record.closing_total
        #     db.session.add(employee)

        # Guardar los cambios en la base de datos
        db.session.add(employee_record)
        db.session.commit()

    # GUARDAR CAJAS DE LOS VENDEDORES
    for user in users_salesman:
        user_id = user.id

        employee = Employee.query.filter_by(user_id=user_id).first()
        employee_status = employee.status
        employee_id = employee.id

        # Verificar si ya existe un registro para este empleado en la fecha actual
        existing_record = EmployeeRecord.query.filter_by(employee_id=employee_id) \
            .filter(func.date(EmployeeRecord.creation_date) == current_date).first()
        
        if existing_record:
    
            continue

        # Inicializar las variables
        initial_state = 0
        loans_to_collect = 0
        paid_installments = 0
        partial_installments = 0
        overdue_installments_total = 0
        daily_incomes_amount = 0
        daily_expenses_amount = 0
        daily_withdrawals = 0
        total_collected = 0
        new_clients_loan_amount = 0
        total_renewal_loans_amount = 0
        total_pending_installments_amount = 0

        # Buscar el último registro en EmployeeRecord del día anterior
        last_record = EmployeeRecord.query.filter_by(employee_id=employee_id) \
            .filter(func.date(EmployeeRecord.creation_date) <= current_date) \
            .order_by(EmployeeRecord.creation_date.desc()).first()

        # Calcular la cantidad de préstamos por cobrar
        loans_to_collect = Loan.query.filter_by(
            employee_id=employee_id, status=True).count()

        # Subconsulta para obtener los IDs de las cuotas de préstamo PAGADA del empleado
        paid_installments_query = db.session.query(LoanInstallment.id) \
            .join(Loan) \
            .filter(Loan.employee_id == employee_id,
                    LoanInstallment.status == InstallmentStatus.PAGADA) \
            .subquery()

        # Calcular la cantidad de cuotas PAGADA y su total
        paid_installments_amount = db.session.query(func.sum(Payment.amount)) \
            .join(paid_installments_query, Payment.installment_id == paid_installments_query.c.id) \
            .filter(func.date(Payment.payment_date) == current_date) \
            .scalar() or 0

        # Inicializar variables para el nuevo cálculo
        total_pending_installments_loan_close_amount = 0
        
        # Calcular el debido cobrar del siguiente dia y préstamos cerrados
        for client in employee.clients:
            for loan in client.loans:
                # Excluir préstamos creados hoy mismo
                if loan.creation_date.date() == datetime.now().date():
                    continue
                
                if loan.status:
                    # Encuentra la última cuota pendiente a la fecha actual incluyendo la fecha de creación de la cuota
                    pending_installment = LoanInstallment.query.filter(
                        LoanInstallment.loan_id == loan.id
                    ).order_by(LoanInstallment.due_date.asc()).first()
                    if pending_installment:
                        total_pending_installments_amount += pending_installment.fixed_amount
                elif loan.status == False and loan.up_to_date and loan.modification_date.date() == datetime.now().date():
                    pending_installment_paid = LoanInstallment.query.filter(
                        LoanInstallment.loan_id == loan.id
                    ).order_by(LoanInstallment.due_date.asc()).first()
                    total_pending_installments_loan_close_amount += pending_installment_paid.fixed_amount



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
            .filter(func.date(Payment.payment_date) == current_date) \
            .scalar() or 0

        # Subconsulta para obtener los IDs de las cuotas de préstamo en MORA del empleado
        overdue_installments_query = db.session.query(LoanInstallment.id) \
            .join(Loan) \
            .filter(Loan.employee_id == employee_id,
                    LoanInstallment.status == InstallmentStatus.MORA) \
            .subquery()

        # Calcular la cantidad de cuotas en MORA y su total
        overdue_installments_total = db.session.query(func.sum(LoanInstallment.amount)) \
            .join(overdue_installments_query,
                  LoanInstallment.id == overdue_installments_query.c.id) \
            .join(Payment, Payment.installment_id == LoanInstallment.id) \
            .filter(func.date(Payment.payment_date) == current_date) \
            .scalar() or 0

        # Calcular el total recaudado en la fecha actual
        total_collected = db.session.query(
            db.func.sum(Payment.amount)
        ).join(LoanInstallment, LoanInstallment.id == Payment.installment_id).join(
            Loan, Loan.id == LoanInstallment.loan_id
        ).filter(
            and_(Loan.employee_id == employee_id, func.date(
                Payment.payment_date) == current_date)
        ).scalar() or 0

        # Calcula el total de préstamos de los nuevos clientes
        new_clients_loan_amount = Loan.query.join(Client).filter(
            Client.employee_id == employee_id,
            func.date(Loan.creation_date) >= current_date,
            Loan.is_renewal == False  # Excluir renovaciones
        ).with_entities(func.sum(Loan.amount)).scalar() or 0

        # Calcula el monto total de las renovaciones de préstamos para este vendedor
        total_renewal_loans_amount = Loan.query.filter(
            Loan.client.has(employee_id=employee_id),
            Loan.is_renewal == True,
            Loan.status == True,
            Loan.approved == True,
            func.date(Loan.creation_date) >= current_date
        ).with_entities(func.sum(Loan.amount)).scalar() or 0

        # Calcula Valor de los gastos diarios
        daily_expenses_amount = Transaction.query.filter(
            Transaction.employee_id == employee_id,
            Transaction.transaction_types == TransactionType.GASTO,
            Transaction.approval_status == ApprovalStatus.APROBADA,
            func.date(Transaction.creation_date) == current_date
        ).with_entities(func.sum(Transaction.amount)).scalar() or 0

        # Calcula los retiros diarios basados en transacciones de RETIRO
        daily_withdrawals_amount = Transaction.query.filter(
            Transaction.employee_id == employee_id,
            Transaction.transaction_types == TransactionType.RETIRO,
            Transaction.approval_status == ApprovalStatus.APROBADA,
            func.date(Transaction.creation_date) == current_date
        ).with_entities(func.sum(Transaction.amount)).scalar() or 0

        # Calcula las colecciones diarias basadas en transacciones de INGRESO
        daily_incomes_amount = Transaction.query.filter(
            Transaction.employee_id == employee_id,
            Transaction.transaction_types == TransactionType.INGRESO,
            Transaction.approval_status == ApprovalStatus.APROBADA,
            func.date(Transaction.creation_date) == current_date
        ).with_entities(func.sum(Transaction.amount)).scalar() or 0

        # Verificar si todos los préstamos tienen un PAGO, ABONO o MORA igual al de hoy
        all_loans_paid = Loan.query.filter_by(employee_id=employee_id).all()
        all_loans_paid_today = False
        all_loans_paid_count = 0
        for loan in all_loans_paid:
            loan_installments = LoanInstallment.query.filter_by(
                loan_id=loan.id).all()
            for installment in loan_installments:
                payments = Payment.query.filter_by(
                    installment_id=installment.id).all()
                for payment in payments:
                    if payment.payment_date.date() == current_date:
                        all_loans_paid_count += 1
                        break

        if loans_to_collect == all_loans_paid_count:
            all_loans_paid_today = True
            
        if last_record:
            initial_state = float(last_record.closing_total)

        # if employee_status == 1 and all_loans_paid_today == True:
        employee_record = EmployeeRecord(
            employee_id=employee_id,
            initial_state=initial_state,
            incomings=daily_incomes_amount,
            expenses=daily_expenses_amount,
            withdrawals=daily_withdrawals_amount,
            closing_total=int(initial_state) + int(paid_installments_amount)
            + int(partial_installments) + int(daily_incomes_amount)
            - int(new_clients_loan_amount)
            - int(total_renewal_loans_amount)
            - int(daily_withdrawals_amount)
            - int(daily_expenses_amount),  # Calcular el cierre de caja
            creation_date=datetime.now(),
            loans_to_collect=loans_to_collect,
            paid_installments=paid_installments_amount,
            partial_installments=partial_installments,
            overdue_installments=overdue_installments_total,
            sales=new_clients_loan_amount,
            renewals=total_renewal_loans_amount,
            due_to_collect_tomorrow=total_pending_installments_amount,
            total_collected=total_collected,
            due_to_charge=total_pending_installments_loan_close_amount+total_pending_installments_amount
        )
        employee.status = 0
        # Agregar la instancia a la sesión de la base de datos y guardar los cambios
        
        employee.box_value = employee_record.closing_total

        db.session.add(employee)
        db.session.add(employee_record)
        db.session.commit()

    return render_template('add-manager-record.html')

@routes.route('/closed-boxes')
def closed_boxes():
    # Código de la función que quieres ejecutar
    return "Tarea ejecutada con éxito"


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

    # Actualizar cada cuota a 0
    for installment in installments:
        installment.amount = 0

    # Desactivar el préstamo
    loan.status = False
    loan.modification_date = datetime.now()

    # Guardar cambios en la base de datos
    db.session.commit()

    return jsonify({'message': f'Préstamo {client_name} cancelado correctamente'}), 200




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
        
        if loan_date == filter_date and loan.is_renewal == 0:  # Verificar si el préstamo se realizó en la fecha filtrada
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
    transactions = Transaction.query.filter_by(
        employee_id=employee_id).order_by(Transaction.creation_date.desc()).all()

    # Filtrar transacciones por tipo y fecha
    expenses = [trans for trans in transactions if
                trans.transaction_types == TransactionType.GASTO and trans.creation_date.date() == filter_date]
    incomes = [trans for trans in transactions if
               trans.transaction_types == TransactionType.INGRESO and trans.creation_date.date() == filter_date]
    withdrawals = [trans for trans in transactions if
                   trans.transaction_types == TransactionType.RETIRO and trans.creation_date.date() == filter_date]

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

        # Funciones para sumar el valor de todas las transacciones en estado: APROBADO y Tipo: INGRESO/RETIRO
        # Calcular la fecha de inicio y fin del día filtrado
        start_of_day = datetime.combine(filter_date, datetime.min.time())
        end_of_day = datetime.combine(filter_date, datetime.max.time())

        # Filtrar las transacciones para el día filtrado del manager
        total_outbound_amount = db.session.query(
            func.sum(Transaction.amount).label('total_amount')
        ).join(Salesman, Transaction.employee_id == Salesman.employee_id).filter(
            Transaction.transaction_types == 'INGRESO',
            Transaction.approval_status == 'APROBADA',
            Salesman.manager_id == manager_id,  # Filtrar solo por el manager
            Transaction.creation_date.between(start_of_day, end_of_day)  # Filtrar por fecha filtrada
        ).scalar() or 0

        # Filtrar las transacciones para el día filtrado del manager
        total_inbound_amount = db.session.query(
            func.sum(Transaction.amount).label('total_amount')
        ).join(Salesman, Transaction.employee_id == Salesman.employee_id).filter(
            Transaction.transaction_types == 'RETIRO',
            Transaction.approval_status == 'APROBADA',
            Salesman.manager_id == manager_id,  # Filtrar solo por el manager
            func.date(Transaction.creation_date) == filter_date  # Filtrar por fecha filtrada
        ).scalar() or 0

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
            
            if employee_records:
                initial_box_value = employee_records.closing_total
            else:
                initial_box_value = employee.box_value

            # Verificar si ya existe un registro en EmployeeRecord con la fecha filtrada
            existing_record_today = EmployeeRecord.query.filter(
                EmployeeRecord.employee_id == salesman.employee_id,
                func.date(EmployeeRecord.creation_date) == filter_date
            ).first()

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

            # Calcula el total de cobros para el día filtrado con estado "PAGADA"
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
                Loan.is_renewal == False  # Excluir renovaciones
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
                        trans.transaction_types == TransactionType.GASTO and trans.creation_date.date() == filter_date]
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

            # Si ya existe un registro de la fecha filtrada, no sumar total_collections_today
            if existing_record_today:
                box_value = initial_box_value - float(daily_withdrawals) - float(
                    daily_expenses_amount) + float(daily_collection) - float(new_clients_loan_amount) - float(total_renewal_loans_amount)
            else:
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

        sub_admin_box = {
            'maximum_cash': float(sub_admin_cash),
            'total_outbound_amount': float(total_outbound_amount),
            'total_inbound_amount': float(total_inbound_amount),
            'final_box_value': float(sub_admin_cash) +
                            float(total_inbound_amount) -
                            float(total_outbound_amount) -
                            float(total_expenses),
        }

        # Renderizar la plantilla con las variables
        return render_template('history-box.html', coordinator_box=sub_admin_box, salesmen_stats=salesmen_stats,
                               search_term=search_term, all_boxes_closed=all_boxes_closed,
                               coordinator_name=sub_admin_name, user_id=user_id, expense_details=expense_details, 
                               total_expenses=total_expenses, filter_date=filter_date, manager_id=manager_id)
    except Exception as e:
        return jsonify({'message': 'Error interno del servidor', 'error': str(e)}), 500