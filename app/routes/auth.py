# app/routes/auth.py
# Autenticación, logout y menús de navegación

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
