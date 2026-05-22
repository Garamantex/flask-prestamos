# app/routes/users.py
# Gestión de usuarios (crear, listar, cambiar contraseña)

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
    """Obtener valores máximos para crear un vendedor
    ---
    tags:
      - Usuarios
    responses:
      200:
        description: Valores máximos del coordinador para parametrizar nuevos vendedores
        schema:
          type: object
          properties:
            maximum_cash_coordinator:
              type: string
              description: Máxima caja del coordinador
            total_cash_salesman:
              type: string
              description: Total de caja ya asignada a vendedores
            maximum_cash_salesman:
              type: string
              description: Máximo disponible para nuevo vendedor
            maximum_sale_coordinator:
              type: string
              description: Máxima venta permitida
            maximum_expense_coordinator:
              type: string
              description: Máximo gasto permitido
            maximum_installments_coordinator:
              type: string
              description: Máximo de cuotas permitidas
            minimum_interest_coordinator:
              type: string
              description: Mínimo interés permitido
      404:
        description: Coordinador o empleado no encontrado
    """
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
    """Obtener valores máximos para crear un préstamo
    ---
    tags:
      - Usuarios
    responses:
      200:
        description: Valores máximos de préstamo del empleado actual
        schema:
          type: object
          properties:
            maximum_sale:
              type: string
              description: Monto máximo de venta
            maximum_installments:
              type: string
              description: Número máximo de cuotas
            minimum_interest:
              type: string
              description: Interés mínimo permitido
    """
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


@routes.route('/change-password/<int:employee_id>', methods=['POST'])
def change_password(employee_id):
    """Cambiar usuario y contraseña de un empleado subordinado
    ---
    tags:
      - Usuarios
    parameters:
      - name: employee_id
        in: path
        type: integer
        required: true
        description: ID del empleado al que se le cambiará la contraseña
      - name: new_username
        in: formData
        type: string
        required: true
        description: Nuevo nombre de usuario
      - name: new_password
        in: formData
        type: string
        required: true
        description: Nueva contraseña (mínimo 4 caracteres)
    responses:
      200:
        description: Credenciales actualizadas exitosamente
        schema:
          type: object
          properties:
            message:
              type: string
      400:
        description: Datos inválidos (usuario en uso o contraseña muy corta)
      403:
        description: Sin permisos (no es coordinador o no es subordinado)
      404:
        description: Empleado no encontrado
      500:
        description: Error interno del servidor
    """
    try:
        user_id, user = validate_coordinator_access()

        coordinator = Employee.query.filter_by(user_id=user_id).first()
        if not coordinator:
            return jsonify({'message': 'Empleado coordinador no encontrado'}), 404

        manager = Manager.query.filter_by(employee_id=coordinator.id).first()
        if not manager:
            return jsonify({'message': 'No se encontró manager asociado'}), 404

        salesman = Salesman.query.filter_by(
            employee_id=employee_id,
            manager_id=manager.id
        ).first()

        is_sub_coordinator = False
        if not salesman:
            sub_manager = Manager.query.filter_by(employee_id=employee_id).first()
            if sub_manager:
                sub_as_salesman = Salesman.query.filter_by(
                    employee_id=employee_id,
                    manager_id=manager.id
                ).first()
                if sub_as_salesman:
                    is_sub_coordinator = True

        if not salesman and not is_sub_coordinator:
            return jsonify({'message': 'El empleado no es subordinado de este coordinador'}), 403

        target_employee = Employee.query.get(employee_id)
        if not target_employee:
            return jsonify({'message': 'Empleado no encontrado'}), 404

        target_user = User.query.get(target_employee.user_id)
        if not target_user:
            return jsonify({'message': 'Usuario no encontrado'}), 404

        new_username = request.form.get('new_username', '').strip()
        if not new_username:
            return jsonify({'message': 'El nombre de usuario es obligatorio'}), 400

        if new_username != target_user.username:
            taken = User.query.filter(
                User.username == new_username,
                User.id != target_user.id
            ).first()
            if taken:
                return jsonify({'message': 'Ese nombre de usuario ya está en uso'}), 400

        new_password = request.form.get('new_password', '').strip()
        if not new_password or len(new_password) < 4:
            return jsonify({'message': 'La contraseña debe tener al menos 4 caracteres'}), 400

        target_user.username = new_username
        target_user.password = new_password
        db.session.commit()

        return jsonify({
            'message': f'Usuario y contraseña de {target_user.first_name} {target_user.last_name} actualizados correctamente'
        }), 200

    except ValueError as e:
        return jsonify({'message': str(e)}), 403
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error interno del servidor', 'error': str(e)}), 500