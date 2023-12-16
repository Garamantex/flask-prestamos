import datetime
from datetime import timedelta
from datetime import date
import os
import uuid
from operator import and_
from datetime import datetime
from sqlalchemy import func
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, session, redirect, url_for, abort, request, jsonify
from app.models import db, InstallmentStatus, Concept, Transaction, Role, Manager, Salesman, TransactionType, \
    ApprovalStatus
from .models import User, Client, Loan, Employee, LoanInstallment

# Crea una instancia de Blueprint
routes = Blueprint('routes', __name__)


# ruta para el home de la aplicación web
@routes.route('/', methods=['GET', 'POST'])
def home():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'ADMINISTRADOR' or role == 'COORDINADOR':
            return redirect(url_for('routes.menu_manager'))
        elif role == 'VENDEDOR':
            return redirect(url_for('routes.menu_salesman'))
        else:
            abort(403)  # Acceso no autorizado

    if request.method == 'POST':
        # Obtener los datos del formulario
        username = request.form.get('username')
        password = request.form.get('password')

        # Verificar las credenciales del usuario en la base de datos
        user = User.query.filter_by(username=username, password=password).first()

        if user:
            # Guardar el usuario en la sesión
            session['user_id'] = user.id
            session['first_name'] = user.first_name
            session['last_name'] = user.last_name
            session['username'] = user.username
            session['role'] = user.role.name  # Guardar solo el nombre del rol

            # Redireccionar según el rol del usuario
            if user.role.name == 'ADMINISTRADOR' or user.role.name == 'COORDINADOR':
                return redirect(url_for('routes.menu_manager'))
            elif user.role.name == 'VENDEDOR':
                return redirect(url_for('routes.menu_salesman'))
            else:
                abort(403)  # Acceso no autorizado

        error_message = 'Credenciales inválidas. Inténtalo nuevamente.'
        return render_template('index.html', error_message=error_message)

    return render_template('index.html')


# ruta para el logout de la aplicación web
@routes.route('/logout')
def logout():
    # Limpiar la sesión
    session.clear()
    return redirect(url_for('routes.home'))


# ruta para el menú del administrador
@routes.route('/menu-manager')
def menu_manager():
    # Verificar si el usuario está logueado es administrador o coordinador
    if 'user_id' not in session:
        return redirect(url_for('routes.home'))

    # Verificar si el usuario es administrador o coordinador
    if session.get('role') != 'ADMINISTRADOR' and session.get('role') != 'COORDINADOR':
        abort(403)  # Acceso no autorizado

    # Mostrar el menú del administrador
    return render_template('menu-manager.html')


# ruta para el menú del vendedor
@routes.route('/menu-salesman')
def menu_salesman():
    # Verificar si el usuario está logueado es un vendedor
    if 'user_id' not in session:
        return redirect(url_for('routes.home'))

    # Verificar si el usuario es vendedor
    if session.get('role') != 'VENDEDOR':
        abort(403)  # Acceso no autorizado

    # Mostrar el menú del vendedor
    return render_template('menu-salesman.html')


@routes.route('/create-user', methods=['GET', 'POST'])
def create_user():
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

            # Verificar si se seleccionó el rol "Vendedor"
            if role == 'VENDEDOR':
                # Obtén el ID del empleado recién creado (el empleado asociado al usuario que acaba de registrarse)
                employee_id_recien_creado = employee.id

                # Obtén el ID del empleado de la sesión (el empleado que está logeado)
                user_id_empleado_sesion = session['user_id']
                employee_id_empleado_sesion = Employee.query.filter_by(user_id=user_id_empleado_sesion).first().id

                # Busca el ID del gerente (manager) a partir del  ID del empleado de la sesión
                manager = Manager.query.filter_by(employee_id=employee_id_empleado_sesion).first()

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

        return render_template('create-user.html')
    else:
        abort(403)  # Acceso no autorizado


@routes.route('/user-list')
def user_list():
    users = User.query.all()
    employees = Employee.query.all()

    return render_template('user-list.html', users=users, employees=employees)


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
    # Obtenemos el ID del empleado desde la sesión
    user_id = session['user_id']
    employee = Employee.query.filter_by(user_id=user_id).first()

    if employee is None:
        return "Error: No se encontrón los valores máximos para el préstamo."

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


@routes.route('/create-client', methods=['GET', 'POST'])
def create_client():
    try:
        if 'user_id' in session and (
                session['role'] == Role.COORDINADOR.value or session['role'] == Role.VENDEDOR.value):
            if request.method == 'POST':
                # Obtener el ID del empleado desde la sesión
                user_id = session['user_id']
                employee = Employee.query.filter_by(user_id=user_id).first()

                if not employee:
                    raise Exception("Error: No se encontró el empleado correspondiente al usuario.")

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
                    raise Exception("Error: Los campos obligatorios deben estar completos.")

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

                # Crear una instancia del préstamo con los datos proporcionados
                loan = Loan(
                    amount=amount,
                    dues=dues,
                    interest=interest,
                    payment=payment,
                    status=True,
                    up_to_date=False,
                    client_id=client_id,
                    employee_id=employee.id
                )

                # Guardar el préstamo en la base de datos
                db.session.add(loan)
                db.session.commit()

                return redirect(url_for('routes.credit_detail', id=loan.id))

            return render_template('create-client.html')
        else:
            return redirect(url_for('routes.menu_salesman'))
    except Exception as e:
        # Manejo de excepciones: mostrar un mensaje de error y registrar la excepción
        error_message = str(e)
        return render_template('error.html', error_message=error_message), 500


@routes.route('/client-list')
def client_list():
    if 'user_id' in session and (session['role'] == Role.COORDINADOR.value or session['role'] == Role.VENDEDOR.value):
        user_id = session['user_id']
        employee = Employee.query.filter_by(user_id=user_id).first()

        if employee is None:
            return "Error: No se encontró el empleado correspondiente al usuario."

        # Obtener la lista de clientes asociados al empleado actual que tienen préstamos en estado diferente de Falso
        if session['role'] == Role.COORDINADOR.value:
            clients = Client.query.filter_by(employee_id=employee.id) \
                .join(Loan).filter(Loan.status != False).all()
        else:  # Si es vendedor, obtener solo los clientes asociados al vendedor con préstamos en estado diferente de
            # Falso
            clients = Client.query.join(Loan).filter(Loan.employee_id == employee.id, Loan.status != False).all()

        return render_template('client-list.html', client_list=clients)
    else:
        return redirect(url_for('routes.menu_salesman'))


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
            selected_client = Client.query.filter_by(document=document_number).first()

            if selected_client is None:
                return "Error: No se encontró el cliente."

            # Verificar si el cliente tiene préstamos activos
            active_loans = Loan.query.filter_by(client_id=selected_client.id, status=True).count()

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
            clients = Client.query.join(Loan).filter(
                Loan.employee_id == employee.id,
                ~Loan.status
            ).distinct(Client.id).all()

        client_data = [(client.document, f"{client.first_name} {client.last_name}") for client in clients]

        return render_template('renewal.html', clients=client_data)
    else:
        return redirect(url_for('routes.menu_salesman'))


@routes.route('/credit-detail/<int:id>')
def credit_detail(id):
    loan = Loan.query.get(id)
    client = Client.query.get(loan.client_id)
    installments = LoanInstallment.query.filter_by(loan_id=loan.id).all()

    # Verificar si ya se generaron las cuotas del préstamo
    if not installments:
        generate_loan_installments(loan)
        installments = LoanInstallment.query.filter_by(loan_id=loan.id).all()

    loans = Loan.query.all()  # Obtener todos los créditos
    loan_detail = get_loan_details(id)

    return render_template('credit-detail.html', loans=loans, loan=loan, client=client, installments=installments,
                           loan_detail=loan_detail)


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
                installment.payment_date = datetime.now()  # Corrección

    # Guardar los cambios en la base de datos
    db.session.commit()

    # Verificar si hay cuotas en estado "MORA"
    mora_installments = LoanInstallment.query.filter_by(loan_id=loan.id, status=InstallmentStatus.MORA).count()
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
    pending_installments = LoanInstallment.query.filter_by(loan_id=loan.id, status=InstallmentStatus.PENDIENTE).count()
    if pending_installments == 0:
        loan.status = False
        db.session.commit()

    return redirect(url_for('routes.credit_detail', id=loan_id))


def generate_loan_installments(loan):
    amount = loan.amount
    dues = loan.dues
    interest = loan.interest
    payment = loan.payment
    creation_date = loan.creation_date.date()
    client_id = loan.client_id
    employee_id = loan.employee_id

    installment_amount = (amount + (amount * interest / 100)) / dues
    due_date = creation_date + timedelta(days=1)

    installments = []
    for installment_number in range(1, int(dues) + 1):
        installment = LoanInstallment(
            installment_number=installment_number,
            due_date=due_date,
            amount=installment_amount,
            status='PENDIENTE',
            loan_id=loan.id
        )
        installments.append(installment)

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

    # Calcular los datos requeridos
    total_cuotas = len(installments)
    cuotas_pagadas = sum(1 for installment in installments if installment.status == InstallmentStatus.PAGADA)
    cuotas_vencidas = sum(1 for installment in installments if installment.status == InstallmentStatus.MORA)
    valor_total = loan.amount + (loan.amount * loan.interest / 100)
    saldo_pendiente = valor_total - sum(
        installment.amount for installment in installments if installment.status == InstallmentStatus.PAGADA)

    # Formatear los valores sin decimales
    valor_total = int(valor_total)
    saldo_pendiente = int(saldo_pendiente)

    # Retornar los detalles del préstamo
    detalles_prestamo = {
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

            concept = Concept(transaction_types=transaction_types_str, name=name)
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


@routes.route('/transaction', methods=['GET', 'POST'])
def transactions():
    if 'user_id' in session and (session['role'] == 'COORDINADOR' or session['role'] == 'VENDEDOR'):
        user_id = session['user_id']

        # Obtener el empleado asociado al user_id
        employee = Employee.query.filter_by(user_id=user_id).first()

        if request.method == 'POST':
            # Manejar la creación de la transacción
            transaction_type = request.form.get('transaction_type')
            concept_id = request.form.get('concept_id')
            description = request.form.get('description')
            amount = request.form.get('quantity')
            attachment = request.files['photo']  # Obtener el archivo de imagen
            approval_status = request.form.get('status')
            concepts = Concept.query.filter_by(transaction_types=transaction_type).all()
            basephant = os.path.abspath(os.path.dirname(__file__))
            filename = secure_filename(attachment.filename)
            extension = filename.split('.')[-1]
            newfilename = str(uuid.uuid4()) + '.' + extension
            attachment.save(os.path.join(basephant, 'static', 'images', newfilename))

            # Usar el employee_id obtenido para crear la transacción
            transaction = Transaction(
                transaction_types=transaction_type,
                concept_id=concept_id,
                description=description,
                amount=amount,
                attachment=attachment.filename,
                approval_status=approval_status,
                employee_id=employee.id  # Usar el employee_id obtenido aquí
            )

            db.session.add(transaction)
            db.session.commit()

            return render_template('transactions.html', message='Transacción creada exitosamente.', alert='success',
                                   concepts=concepts)

        else:
            # Obtener todos los conceptos disponibles
            concepts = Concept.query.all()

            return render_template('transactions.html', concepts=concepts)
    else:
        # Manejar el caso en el que el usuario no esté autenticado o no tenga el rol adecuado
        return "Acceso no autorizado."


@routes.route('/get-concepts', methods=['GET'])
def get_concepts():
    transaction_type = request.args.get('transaction_type')

    # Consultar los conceptos relacionados con el tipo de transacción
    concepts = Concept.query.filter_by(transaction_types=transaction_type).all()

    # Convertir los conceptos a formato JSON
    concepts_json = [concept.to_json() for concept in concepts]

    return jsonify(concepts_json)


@routes.route('/box', methods=['GET'])
def box():
    try:
        # Get the user_id from the session
        user_id = session.get('user_id')

        # Check if user_id exists
        if user_id is None:
            return jsonify({'message': 'User not found'}), 404

        # Get the employee corresponding to user_id
        employee = Employee.query.filter_by(user_id=user_id).first()

        # Check if the employee exists
        if employee is None:
            return jsonify({'message': 'Employee not found'}), 404

        # Get the manager corresponding to the employee
        manager = Manager.query.filter_by(employee_id=employee.id).first()

        # Check if the manager exists
        if manager is None:
            return jsonify({'message': 'Manager not found'}), 404

        # Get the salesmen associated with that manager
        salesmen = Salesman.query.filter_by(manager_id=manager.id).all()

        # Initialize a list to collect statistics for each salesman
        salesmen_stats = []

        for salesman in salesmen:
            # Initialize variables to collect statistics for each salesman
            projected_collections = 0
            total_collections_today = 0
            new_clients = 0
            daily_expenses = 0
            daily_withdrawals = 0
            daily_collection = 0
            completed_collections = 0
            total_customers = 0
            customers_in_arrears = 0

            # Calculate collection projections based on pending loans
            projected_collections = LoanInstallment.query.join(Loan).filter(
                Loan.client.has(employee_id=salesman.employee_id),
                LoanInstallment.status.in_([InstallmentStatus.PENDIENTE, InstallmentStatus.MORA]),
                LoanInstallment.due_date <= date.today()
            ).with_entities(func.sum(LoanInstallment.amount)).scalar() or 0

            # Calculate the total collections for the day with status "PAGADA"
            total_collections_today = LoanInstallment.query.join(Loan).filter(
                Loan.client.has(employee_id=salesman.employee_id),
                LoanInstallment.status == InstallmentStatus.PAGADA,
                LoanInstallment.payment_date == date.today()
            ).with_entities(func.sum(LoanInstallment.amount)).scalar() or 0

            # Calcula la cantidad de nuevos clientes registrados en el día
            new_clients = Client.query.filter(
                Client.employee_id == salesman.employee_id,
                Client.creation_date >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            ).count()

            # Calcula el total de préstamos con is_renewal en True para el día actual
            today = datetime.combine(date.today(), datetime.min.time())
            total_renewal_loans = Loan.query.filter(
                Loan.client.has(employee_id=salesman.employee_id),
                Loan.is_renewal == True,
                Loan.creation_date >= today,
                Loan.creation_date < today + timedelta(days=1)
            ).count()

            # Calculate daily expenses
            daily_expenses = Transaction.query.filter_by(
                employee_id=salesman.employee_id,
                transaction_types=TransactionType.GASTO,
                creation_date=func.current_date()
            ).with_entities(func.sum(Transaction.amount)).scalar() or 0

            # Calculate daily withdrawals based on WITHDRAW transactions
            daily_withdrawals = Transaction.query.filter_by(
                employee_id=salesman.employee_id,
                creation_date=func.current_date(),
                transaction_types=TransactionType.RETIRO
            ).with_entities(func.sum(Transaction.amount)).scalar() or 0

            # Calculate daily collections based on INCOME transactions
            daily_collection = Transaction.query.filter_by(
                employee_id=salesman.employee_id,
                creation_date=func.current_date(),
                transaction_types=TransactionType.INGRESO
            ).with_entities(func.sum(Transaction.amount)).scalar() or 0

            # Total number of salesman's customers
            total_customers = sum(
                1 for client in salesman.employee.clients
                for loan in client.loans
                if loan.status
            )

            # Customers in arrears for the day
            customers_in_arrears = sum(
                1 for client in salesman.employee.clients
                for loan in client.loans
                if loan.status and not loan.up_to_date and any(
                    installment.status == InstallmentStatus.MORA
                    or (installment.status == InstallmentStatus.PENDIENTE and installment.due_date < datetime.now().date())
                    for installment in loan.installments
                )
            )

            # Create a dictionary with the results for this salesman
            salesman_data = {
                'salesman_name': f'{salesman.employee.user.first_name} {salesman.employee.user.last_name}',
                'projected_collections_for_the_day': str(projected_collections),
                'total_collections_today': str(total_collections_today),
                'new_clients_registered_today': str(new_clients),
                'how_many_renewals_have_been_made_today': total_renewal_loans,
                'daily_expenses': str(daily_expenses),
                'daily_withdrawals': str(daily_withdrawals),
                'daily_collections_made': str(daily_collection),
                'how_many_collections_for_the_day_have_been_completed': completed_collections,
                'total_number_of_customers': total_customers,
                'customers_in_arrears_for_the_day': customers_in_arrears
            }
            print(f'salesman_data: {salesman_data}')

            # Add the salesman's data to the list
            salesmen_stats.append(salesman_data)

        return render_template('box.html', coordinator_name=manager.employee.user.username,
                               salesmen_statistics=salesmen_stats)

    except Exception as e:
        return jsonify({'message': 'Internal server error', 'error': str(e)}), 500


# Define the endpoint route to list clients in arrears
@routes.route('/debtor', methods=['GET'])
def debtor():
    try:
        # Obtener el user_id de la sesión
        user_id = session.get('user_id')

        if user_id is None:
            return jsonify({'message': 'Usuario no encontrado en la sesión'}), 401

        # Buscar al empleado correspondiente al user_id de la sesión
        empleado = Employee.query.filter_by(user_id=user_id).first()

        if not empleado:
            return jsonify({'message': 'Empleado no encontrado'}), 404

        # Crear una lista para almacenar los detalles de los clientes en MORA
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
            cuotas_pagadas = sum(1 for cuota in cuotas if cuota.status == InstallmentStatus.PAGADA)
            cuotas_vencidas = sum(1 for cuota in cuotas if cuota.status == InstallmentStatus.MORA)
            valor_total = prestamo.amount + (prestamo.amount * prestamo.interest / 100)
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
                'saldo_pendiente': saldo_pendiente
            }

            # Agregar los detalles del cliente en MORA a la lista
            mora_debtors_details.append(mora_debtor_details)

        return render_template('debtor.html', mora_debtors_details=mora_debtors_details)

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
            clients = Client.query.filter_by(employee_id=salesman.employee.id).all()

            for client in clients:
                # Calcular la información para cada cliente
                client_info = {
                    "client_name": client.first_name + " " + client.last_name,
                    "paid_installments": 0,  # Inicializar el número de cuotas pagadas en 0
                    "overdue_installments": 0,  # Inicializar el número de cuotas en mora en 0
                    "remaining_debt": 0,  # Inicializar el monto pendiente en 0
                    "total_overdue_amount": 0,  # Inicializar el monto total en mora en 0
                    "last_paid_installment_date": None  # Inicializar la fecha de la última cuota pagada como None
                }

                # Obtener todas las cuotas del cliente
                installments = LoanInstallment.query.filter_by(client_id=client.id).all()

                for installment in installments:
                    if installment.status == InstallmentStatus.PAGADA:
                        client_info["paid_installments"] += 1
                        client_info["last_paid_installment_date"] = installment.payment_date
                    elif installment.status == InstallmentStatus.MORA:
                        client_info["overdue_installments"] += 1
                        client_info["total_overdue_amount"] += float(installment.amount)
                    if installment.status != InstallmentStatus.PAGADA:
                        client_info["remaining_debt"] += float(installment.amount)

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
        clients = Client.query.filter_by(employee_id=salesman.employee.id).all()

        for client in clients:
            # Calcular la información para cada cliente
            client_info = {
                "client_name": client.first_name + " " + client.last_name,
                "paid_installments": 0,  # Inicializar el número de cuotas pagadas en 0
                "overdue_installments": 0,  # Inicializar el número de cuotas en mora en 0
                "remaining_debt": 0,  # Inicializar el monto pendiente en 0
                "total_overdue_amount": 0,  # Inicializar el monto total en mora en 0
                "last_paid_installment_date": None  # Inicializar la fecha de la última cuota pagada como None
            }

            # Obtener todas las cuotas del cliente
            installments = LoanInstallment.query.filter_by(client_id=client.id).all()

            for installment in installments:
                if installment.status == InstallmentStatus.PAGADA:
                    client_info["paid_installments"] += 1
                    client_info["last_paid_installment_date"] = installment.payment_date
                elif installment.status == InstallmentStatus.MORA:
                    client_info["overdue_installments"] += 1
                    client_info["total_overdue_amount"] += float(installment.amount)
                if installment.status != InstallmentStatus.PAGADA:
                    client_info["remaining_debt"] += float(installment.amount)

            # Agregar la información del cliente a la lista de clientes del vendedor
            salesman_info["clients"].append(client_info)

            # Actualizar el total de cuotas en mora del vendedor
            salesman_info["total_overdue_installments"] += client_info["overdue_installments"]

        # Agregar la información del vendedor a la lista principal
        debtors_info.append(salesman_info)
    print(debtors_info)
    return jsonify(debtors_info)


# Define una ruta para obtener la lista de pagos
@routes.route('/payment_list', methods=['GET'])
def payments_list():
    # Obtiene el ID de usuario desde la sesión
    user_id = session.get('user_id')

    # Busca al empleado asociado al usuario
    employee = Employee.query.filter_by(user_id=user_id).first()

    if not employee:
        return jsonify({"error": "No se encontró el empleado asociado al usuario."}), 404

    # Busca al vendedor correspondiente al empleado
    salesman = Salesman.query.filter_by(employee_id=employee.id).first()

    if not salesman:
        return jsonify({"error": "No se encontró el vendedor asociado al empleado."}), 404

    # Inicializa la lista para almacenar la información de los clientes
    clients_information = []

    # Obtiene los clientes del empleado con préstamos activos
    for client in employee.clients:
        for loan in client.loans:
            if loan.status:
                paid_installments = 0
                overdue_installments = 0
                total_outstanding_amount = 0
                total_overdue_amount = 0
                last_payment_date = None

                for installment in loan.installments:
                    if installment.status == InstallmentStatus.PAGADA:
                        paid_installments += 1
                        # Si es un pago realizado, actualiza la fecha de la última cuota pagada
                        if installment.payment_date and (
                                not last_payment_date or installment.payment_date > last_payment_date):
                            last_payment_date = installment.payment_date

                client_info = {
                    'First Name': client.first_name,
                    'Last Name': client.last_name,
                    'Paid Installments': paid_installments,
                    'Overdue Installments': overdue_installments,
                    'Total Outstanding Amount': str(total_outstanding_amount),
                    'Total Overdue Amount': str(total_overdue_amount),
                    'Last Payment Date': last_payment_date.isoformat() if last_payment_date else 'No se registraron pagos'
                }
                clients_information.append(client_info)

    # Finalmente, renderiza la información como una respuesta JSON y también renderiza una plantilla
    return render_template('payments-route.html', clients=clients_information)


# Ruta para la página de aprobación de gastos
@routes.route('/approval-expenses')
def approval_expenses():
    try:
        # Obtener el user_id de la sesión
        user_id = session.get('user_id')

        if user_id is None:
            return jsonify({'message': 'Usuario no encontrado en la sesión'}), 401

        # Buscar al empleado correspondiente al user_id de la sesión
        empleado = Employee.query.filter_by(user_id=user_id).first()

        if not empleado:
            return jsonify({'message': 'Empleado no encontrado'}), 404

        # Obtener todas las transacciones asociadas a este empleado en estado "PENDIENTE"
        transacciones_pendientes = Transaction.query.filter(
            Transaction.employee_id == empleado.id,
            Transaction.approval_status == ApprovalStatus.PENDIENTE
        ).all()

        # Crear una lista para almacenar los detalles de las transacciones pendientes
        detalles_transacciones = []

        for transaccion in transacciones_pendientes:
            # Obtener el concepto de la transacción
            concepto = Concept.query.get(transaccion.concept_id)

            # Crear un diccionario con los detalles de la transacción pendiente
            detalle_transaccion = {
                'id': transaccion.id,
                'tipo': transaccion.transaction_types.name,
                'concepto': concepto.name,
                'descripcion': transaccion.description,
                'monto': transaccion.amount,
                'attachment': transaccion.attachment,
            }
            # Agregar los detalles a la lista
            detalles_transacciones.append(detalle_transaccion)
            print(detalles_transacciones)

        return render_template('approval-expenses.html', detalles_transacciones=detalles_transacciones)

    except Exception as e:
        return jsonify({'message': 'Error interno del servidor', 'error': str(e)}), 500


# Ruta para modificar el estado de una transacción
@routes.route('/modify-transaction/<int:transaction_id>', methods=['POST'])
def modify_transaction(transaction_id):
    try:
        # Obtener la transacción
        transaction = Transaction.query.get(transaction_id)

        if not transaction:
            return jsonify({'message': 'Transacción no encontrada'}), 404

        # Obtener el nuevo estado de la transacción desde el formulario
        new_status = request.form.get('new_status')

        # Verificar si el nuevo estado es válido
        if new_status not in [ApprovalStatus.APROBADA.value, ApprovalStatus.RECHAZADA.value]:
            return jsonify({'message': 'Estado no válido'}), 400

        # Actualizar el estado de la transacción
        transaction.approval_status = ApprovalStatus(new_status)

        # Guardar los cambios en la base de datos
        db.session.commit()

        # Redirigir al usuario a la página de solicitudes pendientes
        return redirect('/approval-expenses')

    except Exception as e:
        return jsonify({'message': 'Error interno del servidor', 'error': str(e)}), 500


@routes.route('/wallet')
def wallet():
    # Initialize variables
    total_cash = 0
    total_active_sellers = 0
    sellers_detail = []

    # Get all coordinators
    coordinators = Manager.query.all()

    for coordinator in coordinators:
        # Get sellers associated with this coordinator
        sellers = Salesman.query.filter_by(manager_id=coordinator.id).all()
        total_max_cash = 0
        total_active_loans = 0
        total_overdue_installments = 0
        total_pending_installments = 0
        day_collection = 0
        debt_balance = 0

        for seller in sellers:
            # Calculate the total number of sellers with active loans
            if len(seller.employee.clients) > 0:
                total_active_sellers += 1

            # Calculate the total of maximum_cash for sellers
            total_max_cash += float(seller.employee.maximum_cash)

            # Calculate the detail for each seller
            seller_info = {
                'First Name': seller.employee.user.first_name,
                'Last Name': seller.employee.user.last_name,
                'Number of Active Loans': 0,  # Initialize to 0
                'Total Amount of Overdue Loans': 0,
                'Total Amount of Pending Installments': 0,
            }

            # Get clients associated with this seller
            clients = seller.employee.clients

            for client in clients:
                active_loans = Loan.query.filter_by(client_id=client.id, status=True).count()
                seller_info['Number of Active Loans'] += active_loans

                for loan in client.loans:
                    for installment in loan.installments:
                        if installment.status == InstallmentStatus.MORA:
                            seller_info['Total Amount of Overdue Loans'] += float(loan.amount)
                        elif installment.status == InstallmentStatus.PENDIENTE:
                            seller_info['Total Amount of Pending Installments'] += float(installment.amount)

            sellers_detail.append(seller_info)

        # Calculate the total cash associated with sellers of the coordinator
        total_cash += total_max_cash

    # Calculate the percentage of the day's collection based on Installments PAGADA
    # This is calculated by summing the Installments PAGADA and dividing it by the debt balance
    paid_installments = LoanInstallment.query.filter_by(status=InstallmentStatus.PAGADA).count()
    debt_balance = total_cash  # Assuming the debt balance is equal to the total cash
    if debt_balance > 0:
        day_collection = (paid_installments / debt_balance) * 100

    # Create the final dictionary with the requested data
    wallet_data = {
        'Total Cash Value': str(total_cash),
        'Total Sellers with Active Loans': total_active_sellers,
        'Sellers Detail': sellers_detail,
        'Percentage of Day Collection': f'{day_collection:.2f}%',
        'Debt Balance': str(debt_balance)
    }

    return render_template('wallet.html', wallet_data=wallet_data)


@routes.route('/wallet_detail/<int:employee_id>', methods=['GET'])
def wallet_detail(employee_id):
    # Obtener el empleado
    employee = Employee.query.filter_by(employee_id=employee_id).first()
    if not employee:
        return jsonify({'message': 'Empleado no encontrado'}), 404

    # Inicializar variables
    total_loans = 0
    total_overdue_amount = 0
    loans_detail = []

    # Obtener todos los préstamos
    loans = Loan.query.all()

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
            'Loan Amount': str(loan.amount),
            'Total Overdue Amount': str(total_overdue_amount_loan),
            'Overdue Installments Count': total_overdue_installments_loan,
            'Paid Installments Count': total_paid_installments_loan,
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
    print(wallet_detail_data)
    return render_template('wallet-detail.html', wallet_detail_data=wallet_detail_data)


@routes.route('/list-expenses')
def list_expenses():
    try:
        # Obtener el user_id de la sesión
        user_id = session.get('user_id')

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
                'status': transaccion.approval_status
            }

            # Agregar los detalles a la lista
            detalles_transacciones.append(detalle_transaccion)

        return render_template('list-expenses.html', detalles_transacciones=detalles_transacciones)

    except Exception as e:
        return jsonify({'message': 'Error interno del servidor', 'error': str(e)}), 500


@routes.route('/create-box')
def create_box():
    return render_template('create-box.html')


@routes.route('/box-archive')
def box_archive():
    return render_template('box-archive.html')


@routes.route('/box-detail')
def box_detail():
    return render_template('box-detail.html')


@routes.route('/reports')
def reports():
    return render_template('reports.html')
