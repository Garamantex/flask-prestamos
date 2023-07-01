from flask import Blueprint, render_template, session, redirect, url_for, abort, request
from app.models import db
from .models import User, Client, Loan, Employee

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
    return render_template('user-list.html')


@routes.route('/create-client',  methods=['GET', 'POST'])
def create_client():
    if 'user_id' in session and session['role'] == 'ADMINISTRADOR' or session['role'] == 'VENDEDOR':
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


@routes.route('/renewal')
def renewal():
    return render_template('renewal.html')


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


@routes.route('/credit-detail')
def credit_detail():
    return render_template('credit-detail.html')


@routes.route('/reports')
def reports():
    return render_template('reports.html')


@routes.route('/bills')
def bills():
    return render_template('bills.html')


@routes.route('/income')
def income():
    return render_template('income.html')


@routes.route('/outcome')
def outcome():
    return render_template('outcome.html')
