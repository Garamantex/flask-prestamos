from flask import Blueprint, render_template, session, redirect, url_for, abort, request, jsonify
from app.models import db, InstallmentStatus, Concept, Transaction
from .models import User, Client, Loan, Employee, LoanInstallment
from datetime import timedelta


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
            session['username'] = user.username
            session['role'] = user.role.name  # Guardar solo el nombre del rol

            # Redireccionar según el rol del usuario
            if user.role.name == 'ADMINISTRADOR':
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
    # Verificar si el usuario está logueado
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
    # Verificar si el usuario está logueado
    if 'user_id' not in session:
        return redirect(url_for('routes.home'))

    # Verificar si el usuario es vendedor
    if session.get('role') != 'VENDEDOR':
        abort(403)  # Acceso no autorizado

    # Mostrar el menú del vendedor
    return render_template('menu-salesman.html')

# ruta para crear un usuario


@routes.route('/create-user', methods=['GET', 'POST'])
def create_user():
    if 'user_id' in session and session['role'] == 'ADMINISTRADOR':
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
            maximum_payment = request.form['maximum_payment']
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
                maximum_payment=maximum_payment,
                minimum_interest=minimum_interest,
                percentage_interest=percentage_interest,
                fix_value=fix_value
            )

            # Guarda el nuevo empleado en la base de datos
            db.session.add(employee)
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


@routes.route('/create-client',  methods=['GET', 'POST'])
def create_client():
    if 'user_id' in session and session['role'] == 'COORDINADOR' or session['role'] == 'VENDEDOR':
        if request.method == 'POST':
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
            employee_id = session['user_id']
            # Crea una instancia del cliente con los datos proporcionados
            client = Client(
                first_name=first_name,
                last_name=last_name,
                alias=alias,
                document=document,
                cellphone=cellphone,
                address=address,
                neighborhood=neighborhood
            )

            # Guarda el cliente en la base de datos
            db.session.add(client)

            db.session.commit()

            # Obtiene el ID del cliente recién creado
            client_id = client.id

            # Crea una instancia del préstamo con los datos proporcionados
            loan = Loan(
                amount=amount,
                dues=dues,
                interest=interest,
                payment=payment,
                status=True,
                up_to_date=False,
                client_id=client_id,
                employee_id=employee_id
            )

            # Guarda el préstamo en la base de datos
            db.session.add(loan)
            db.session.commit()

            return redirect(url_for('routes.credit_detail', id=loan.id))

        return render_template('create-client.html')
    else:
        return redirect(url_for('routes.menu_salesman'))


@routes.route('/client-list')
def client_list():
    
    clients = Client.query.all()
    
    return render_template('client-list.html', client_list=clients)


@routes.route('/renewal')
def renewal():
    return render_template('renewal.html')


@routes.route('/credit-detail/<int:id>')
def credit_detail(id):
    loan = Loan.query.get(id)
    client = Client.query.get(loan.client_id)
    installments = LoanInstallment.query.filter_by(loan_id=loan.id).all()
    
     # Verificar si ya se generaron las cuotas del préstamo
    if not installments:
        generar_cuotas_prestamo(loan)
        installments = LoanInstallment.query.filter_by(loan_id=loan.id).all()
    
    loans = Loan.query.all()  # Obtener todos los créditos
    loan_detail = obtener_detalles_prestamo(id)
    
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

    return redirect(url_for('routes.credit_detail', id=loan_id))


def generar_cuotas_prestamo(loan):
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


def obtener_detalles_prestamo(loan_id):
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
            transaction_type = request.form.get('transaction_type')
            concept_id = request.form.get('concept_id')
            description = request.form.get('description')
            mount = request.form.get('mount')
            attachment = request.form.get('attachment')
            status = request.form.get('status')

            # Usar el employee_id obtenido para crear la transacción
            transaction = Transaction(
                transaction_types=transaction_type,
                concept_id=concept_id,
                description=description,
                mount=mount,
                attachment=attachment,
                status=status,
                employee_id=employee.id  # Usar el employee_id obtenido aquí
            )

            db.session.add(transaction)
            db.session.commit()

            return jsonify(transaction.to_json()), 201

        else:
            # Renderizar el formulario para crear una transacción
            return render_template('transaction.html')
    else:
        # Manejar el caso en el que el usuario no esté autenticado o no tenga el rol adecuado
        return "Acceso no autorizado."


@routes.route('/box')
def box():
    
    return render_template('box.html')


@routes.route('/create-box')
def create_box():
    return render_template('create-box.html')


@routes.route('/box-archive')
def box_archive():
    return render_template('box-archive.html')


@routes.route('/box-detail')
def box_detail():
    return render_template('box-detail.html')


@routes.route('/routesroval-expenses')
def routesroval_expenses():
    return render_template('routesroval-expenses.html')


@routes.route('/morosos')
def debtor():
    return render_template('debtor.html')


@routes.route('/wallet')
def wallet():
    return render_template('wallet.html')


@routes.route('/wallet-detail')
def wallet_detail():
    return render_template('wallet-detail.html')


@routes.route('/reports')
def reports():
    return render_template('reports.html')


@routes.route('/transactions')
def bills():
    return render_template('transactions.html')

