from flask import Flask, render_template, session, redirect, url_for, abort, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from models import User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


@app.route('/')
def home():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'ADMINISTRADOR' and role == 'COORDINADOR':
            return redirect(url_for('routes.menu-manager'))
        elif role == 'VENDEDOR':
            return redirect(url_for('routes.menu-salesman'))
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
            session['role'] = user.role

            # Redireccionar según el rol del usuario
            if user.role == 'ADMINISTRADOR':
                return redirect(url_for('routes.menu-manager'))
            elif user.role == 'vendedor':
                return redirect(url_for('routes.menu-salesman'))
            else:
                abort(403)  # Acceso no autorizado

        error_message = 'Credenciales inválidas. Inténtalo nuevamente.'
        return render_template('index.html', error_message=error_message)

    return render_template('index.html')


@app.route('/menu-manager')
def menu_manager():
    return render_template('menu-manager.html')


@app.route('/menu-salesman')
def menu_salesman():
    return render_template('menu-salesman.html')


@app.route('/create-client')
def create_client():
    return render_template('create-client.html')


@app.route('/renewal')
def renewal():
    return render_template('renewal.html')


@app.route('/box')
def box():
    return render_template('box.html')


@app.route('/create-box')
def create_box():
    return render_template('create-box.html')


@app.route('/box-archive')
def box_archive():
    return render_template('box-archive.html')


@app.route('/box-detail')
def box_detail():
    return render_template('box-detail.html')


@app.route('/approval-expenses')
def approval_expenses():
    return render_template('approval-expenses.html')


@app.route('/morosos')
def debtor():
    return render_template('debtor.html')


@app.route('/wallet')
def wallet():
    return render_template('wallet.html')


@app.route('/wallet-detail')
def wallet_detail():
    return render_template('wallet-detail.html')


@app.route('/credit-detail')
def credit_detail():
    return render_template('credit-detail.html')


@app.route('/create-user')
def create_user():
    return render_template('create-user.html')


@app.route('/user-list')
def user_list():
    return render_template('user-list.html')


@app.route('/reports')
def reports():
    return render_template('reports.html')


@app.route('/bills')
def bills():
    return render_template('bills.html')


@app.route('/income')
def income():
    return render_template('income.html')


@app.route('/outcome')
def outcome():
    return render_template('outcome.html')


if __name__ == '__main__':
    app.run(debug=True)
