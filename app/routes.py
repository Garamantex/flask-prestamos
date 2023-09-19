import datetime
from datetime import timedelta
import os
import uuid
from operator import and_

from sqlalchemy import func
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, session, redirect, url_for, abort, request, jsonify
from app.models import db, InstallmentStatus, Concept, Transaction, Role, Manager, Salesman, TransactionType
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


@routes.route('/get_maximum_values_create_salesman/<int:manager_id>', methods=['GET'])
def get_maximum_values_create_salesman(manager_id):
    if 'user_id' in session and session['role'] == 'COORDINADOR':
        # Verificar si el usuario tiene el rol de "Coordinador"

        # Buscar el coordinador en la tabla Manager
        manager = Manager.query.get(manager_id)

        if manager:
            # Obtener la suma de maximum_cash de los vendedores asociados al coordinador
            total_cash = db.session.query(db.func.sum(Employee.maximum_cash)).join(Salesman). \
                filter(Salesman.manager_id == manager_id).scalar()

            if total_cash is None:
                total_cash = 0

            # Obtener el valor máximo de maximum_cash para el coordinador
            maximum_cash_coordinator = manager.employee.maximum_cash

            # Calcular el valor máximo que se puede parametrizar a un nuevo vendedor
            maximum_cash_salesman = maximum_cash_coordinator - total_cash

            return {
                'maximum_cash_coordinator': str(maximum_cash_coordinator),
                'total_cash_salesman': str(total_cash),
                'maximum_cash_salesman': str(maximum_cash_salesman),
                'manager_id': str(manager_id)
            }
        else:
            abort(404)  # Coordinador no encontrado

    else:
        abort(403)  # Acceso no autorizado


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

        # Obtener la lista de clientes asociados al empleado actual
        if session['role'] == Role.COORDINADOR.value:
            clients = Client.query.filter_by(employee_id=employee.id).all()
        else:  # Si es vendedor, obtener solo los clientes asociados al vendedor
            clients = Client.query.join(Loan).filter(Loan.employee_id == employee.id).all()

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
            # Obtener el número de documento del cliente desde el formulario
            document_number = request.form.get('document_number')

            # Buscar el cliente por número de documento
            client = Client.query.filter_by(document=document_number).first()

            if client is None:
                return "Error: No se encontró un cliente con ese número de documento."

            # Verificar si el cliente tiene préstamos activos
            active_loans = Loan.query.filter_by(client_id=client.id, status=True).count()

            if active_loans > 0:
                return "Error: El cliente ya tiene préstamos activos y no puede realizar una renovación."

            # Obtener los datos del formulario
            amount = float(request.form.get('amount'))
            dues = float(request.form.get('dues'))
            interest = float(request.form.get('interest'))
            payment = float(request.form.get('payment'))

            # Crear la instancia de renovación de préstamo
            renewal_loan = Loan(
                amount=amount,
                dues=dues,
                interest=interest,
                payment=payment,
                status=True,
                up_to_date=False,
                is_renewal=True,
                client_id=client.id,
                employee_id=employee.id
            )

            # Guardar la renovación de préstamo en la base de datos
            db.session.add(renewal_loan)
            db.session.commit()

            return redirect(url_for('routes.credit_detail', id=renewal_loan.id))

        return render_template('renewal.html')
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
            mount = request.form.get('quantity')
            attachment = request.files['photo']  # Obtener el archivo de imagen
            status = request.form.get('status')
            concepts = Concept.query.all()

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
                mount=mount,
                attachment=attachment.filename,
                status=status,
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
        # Get user_id from session
        user_id = session.get('user_id')

        # Check if user_id exists
        if user_id is None:
            return jsonify({'message': 'User not found'}), 404

        # Get the employee corresponding to user_id
        employee = Employee.query.filter_by(user_id=user_id).first()

        # Check if employee exists
        if employee is None:
            return jsonify({'message': 'Employee not found'}), 404

        # Get the manager corresponding to the employee
        manager = Manager.query.filter_by(employee_id=employee.id).first()

        # Check if manager exists
        if manager is None:
            return jsonify({'message': 'Manager not found'}), 404

        # Get the salesmen associated with that manager
        salesmen = Salesman.query.filter_by(manager_id=manager.id).all()

        # Initialize a list to collect statistics for each salesman
        salesmen_stats = []

        # Iterate over the salesmen
        for salesman in salesmen:
            # Initialize variables to collect statistics for each salesman
            projected_collections = 0
            new_loans = 0
            daily_expenses = 0
            daily_withdrawals = 0
            daily_collection = 0
            daily_renewals = 0
            completed_collections = 0
            total_customers = 0
            customers_in_arrears = 0

            # Calculate based on daily RETIRO transactions
            daily_withdrawals = Transaction.query.filter_by(
                employee_id=salesman.employee_id,
                creation_date=func.current_date(),
                transaction_types=TransactionType.RETIRO
            ).with_entities(func.sum(Transaction.mount)).scalar() or 0

            # Calculate based on daily INGRESO transactions
            daily_collection = Transaction.query.filter_by(
                employee_id=salesman.employee_id,
                creation_date=func.current_date(),
                transaction_types=TransactionType.INGRESO
            ).with_entities(func.sum(Transaction.mount)).scalar() or 0

            # Calculate completed collections for the day
            sales_today = Transaction.query.filter_by(
                employee_id=salesman.employee_id,
                creation_date=func.current_date(),
                transaction_types=TransactionType.INGRESO
            ).all()

            completed_collections = len([sale for sale in sales_today if sale.status])

            # Total customers of the salesman
            total_customers = len(salesman.employee.clients)

            # Customers in arrears for the day
            customers_in_arrears = len([
                client for client in salesman.employee.clients
                if any(loan.status and not loan.up_to_date for loan in client.loans)
            ])

            # Create a dictionary with the results for this salesman
            salesman_data = {
                'salesman_name': f'{salesman.employee.user.first_name} {salesman.employee.user.last_name}',
                'projected_collections_for_the_day': projected_collections,
                'new_loans_made_today': new_loans,
                'daily_expenses': daily_expenses,
                'daily_withdrawals': daily_withdrawals,
                'daily_collections_made': daily_collection,
                'how_many_renewals_have_been_made_today': daily_renewals,
                'how_many_collections_of_the_day_have_been_completed': completed_collections,
                'total_number_of_customers': total_customers,
                'customers_in_arrears_for_the_day': customers_in_arrears
            }

            # Append the salesman's data to the list
            salesmen_stats.append(salesman_data)

        return render_template('box.html', manager_name=manager.employee.user.username, salesmen_stats=salesmen_stats)

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


@routes.route('/create-box')
def create_box():
    return render_template('create-box.html')


@routes.route('/box-archive')
def box_archive():
    return render_template('box-archive.html')


@routes.route('/box-detail')
def box_detail():
    return render_template('box-detail.html')


@routes.route('/approval-expenses')
def approval_expenses():
    return render_template('approval-expenses.html')


@routes.route('/wallet')
def wallet():
    return render_template('wallet.html')


@routes.route('/wallet-detail')
def wallet_detail():
    return render_template('wallet-detail.html')


@routes.route('/reports')
def reports():
    return render_template('reports.html')
