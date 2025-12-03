# Importaciones del módulo estándar de Python
from sqlalchemy import join, tuple_
from sqlalchemy.orm import joinedload
from flask import request, render_template, session, redirect, url_for, flash
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
# from flask_caching import Cache
# import hashlib
# import json

# Importaciones de tu aplicación (módulos locales)
from app.models import db, InstallmentStatus, Concept, Transaction, Role, Manager, Payment, Salesman, TransactionType, \
    ApprovalStatus, EmployeeRecord

# Importaciones de modelos y otros componentes específicos de tu aplicación
from .models import User, Client, Loan, Employee, LoanInstallment

# Crea una instancia de Blueprint
routes = Blueprint('routes', __name__)

# ==================== CONFIGURACIÓN DE CACHÉ (DESHABILITADA) ====================

# Configuración del caché - DESHABILITADA PARA PRODUCCIÓN
# cache_config = {
#     'CACHE_TYPE': 'redis',
#     'CACHE_REDIS_HOST': 'localhost',
#     'CACHE_REDIS_PORT': 6379,
#     'CACHE_REDIS_DB': 0,
#     'CACHE_DEFAULT_TIMEOUT': 300,  # 5 minutos por defecto
#     'CACHE_KEY_PREFIX': 'flask_prestamos_',
#     'CACHE_REDIS_URL': 'redis://localhost:6379/0'
# }

# Inicializar caché - DESHABILITADO
# cache = Cache()

# def init_cache(app):
#     """Inicializa el caché con la aplicación Flask"""
#     cache.init_app(app, config=cache_config)
#     return cache

# Función para obtener el caché inicializado - DESHABILITADA
# def get_cache():
#     """Obtiene la instancia del caché inicializada"""
#     from flask import current_app
#     if current_app:
#         return current_app.extensions.get('cache', {}).get(cache)
#     return cache

# Decorador de caché seguro - DESHABILITADO
def safe_cache(timeout=300):
    """Decorador de caché que maneja la inicialización de forma segura - DESHABILITADO"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            # Ejecutar la función directamente sin caché
            return f(*args, **kwargs)
        return wrapper
    return decorator

# ==================== FUNCIONES AUXILIARES DE CACHÉ (DESHABILITADAS) ====================

# def generate_cache_key(prefix, *args, **kwargs):
#     """Genera una clave de caché única basada en argumentos"""
#     # Crear hash de los argumentos
#     key_data = {
#         'args': args,
#         'kwargs': sorted(kwargs.items()) if kwargs else {}
#     }
#     key_string = json.dumps(key_data, sort_keys=True, default=str)
#     key_hash = hashlib.md5(key_string.encode()).hexdigest()[:16]
#     return f"{prefix}_{key_hash}"

# def invalidate_coordinator_cache(coordinator_id):
#     """Invalida el caché de un coordinador específico"""
#     try:
#         current_cache = get_cache()
#         if hasattr(current_cache, 'app') and current_cache.app:
#             current_cache.delete_memoized(get_coordinator_data, coordinator_id)
#             current_cache.delete_memoized(get_all_salesmen_data_optimized, coordinator_id)
#             # Invalidar caché por patrón
#             current_cache.delete_memoized_pattern(f"coordinator_{coordinator_id}_*")
#     except Exception:
#         pass  # Si hay error, continuar sin invalidar

# def invalidate_salesman_cache(employee_id):
#     """Invalida el caché de un vendedor específico"""
#     try:
#         current_cache = get_cache()
#         if hasattr(current_cache, 'app') and current_cache.app:
#             current_cache.delete_memoized(get_salesman_customers_data, employee_id)
#             current_cache.delete_memoized(get_salesman_pending_installments, employee_id)
#             current_cache.delete_memoized(check_all_loans_paid_today, employee_id)
#             current_cache.delete_memoized(get_salesman_collected_clients, employee_id)
#             current_cache.delete_memoized(get_salesman_transaction_details, employee_id)
#     except Exception:
#         pass  # Si hay error, continuar sin invalidar

# ==================== ENDPOINTS DE GESTIÓN DE CACHÉ (DESHABILITADOS) ====================

# @routes.route('/cache/clear', methods=['POST'])
# def clear_cache():
#     """Endpoint para limpiar el caché (solo para administradores)"""
#     try:
#         user_id = session.get('user_id')
#         if not user_id:
#             return jsonify({'message': 'Usuario no autenticado'}), 401
#         
#         user = User.query.get(user_id)
#         if not user or user.role != Role.ADMINISTRADOR:
#             return jsonify({'message': 'Acceso denegado'}), 403
#         
#         # Limpiar todo el caché
#         try:
#             current_cache = get_cache()
#             if hasattr(current_cache, 'app') and current_cache.app:
#                 current_cache.clear()
#                 return jsonify({'message': 'Caché limpiado exitosamente'}), 200
#             else:
#                 return jsonify({'message': 'Caché no inicializado'}), 400
#         except Exception as e:
#             return jsonify({'message': 'Error al limpiar caché', 'error': str(e)}), 500
#         
#     except Exception as e:
#         return jsonify({'message': 'Error al limpiar caché', 'error': str(e)}), 500

# @routes.route('/cache/clear/coordinator/<int:coordinator_id>', methods=['POST'])
# def clear_coordinator_cache(coordinator_id):
#     """Endpoint para limpiar caché de un coordinador específico"""
#     try:
#         user_id = session.get('user_id')
#         if not user_id:
#             return jsonify({'message': 'Usuario no autenticado'}), 401
#         
#         user = User.query.get(user_id)
#         if not user or user.role not in [Role.ADMINISTRADOR, Role.COORDINADOR]:
#             return jsonify({'message': 'Acceso denegado'}), 403
#         
#         # Limpiar caché del coordinador
#         invalidate_coordinator_cache(coordinator_id)
#         return jsonify({'message': f'Caché del coordinador {coordinator_id} limpiado exitosamente'}), 200
#         
#     except Exception as e:
#         return jsonify({'message': 'Error al limpiar caché del coordinador', 'error': str(e)}), 500

# @routes.route('/cache/clear/salesman/<int:employee_id>', methods=['POST'])
# def clear_salesman_cache(employee_id):
#     """Endpoint para limpiar caché de un vendedor específico"""
#     try:
#         user_id = session.get('user_id')
#         if not user_id:
#             return jsonify({'message': 'Usuario no autenticado'}), 401
#         
#         user = User.query.get(user_id)
#         if not user or user.role not in [Role.ADMINISTRADOR, Role.COORDINADOR]:
#             return jsonify({'message': 'Acceso denegado'}), 403
#         
#         # Limpiar caché del vendedor
#         invalidate_salesman_cache(employee_id)
#         return jsonify({'message': f'Caché del vendedor {employee_id} limpiado exitosamente'}), 200
#         
#     except Exception as e:
#         return jsonify({'message': 'Error al limpiar caché del vendedor', 'error': str(e)}), 500

# @routes.route('/cache/stats', methods=['GET'])
# def cache_stats():
#     """Endpoint para obtener estadísticas del caché"""
#     try:
#         user_id = session.get('user_id')
#         if not user_id:
#             return jsonify({'message': 'Usuario no autenticado'}), 401
#         
#         user = User.query.get(user_id)
#         if not user or user.role != Role.ADMINISTRADOR:
#             return jsonify({'message': 'Acceso denegado'}), 403
#         
#         # Obtener estadísticas del caché
#         stats = {
#             'cache_type': cache_config.get('CACHE_TYPE', 'unknown'),
#             'cache_timeout': cache_config.get('CACHE_DEFAULT_TIMEOUT', 300),
#             'cache_prefix': cache_config.get('CACHE_KEY_PREFIX', ''),
#             'redis_host': cache_config.get('CACHE_REDIS_HOST', 'localhost'),
#             'redis_port': cache_config.get('CACHE_REDIS_PORT', 6379)
#         }
#         
#         return jsonify(stats), 200
#         
#     except Exception as e:
#         return jsonify({'message': 'Error al obtener estadísticas del caché', 'error': str(e)}), 500

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

        return render_template('credit-detail.html', loans=loans, loan=loan, client=client, installments=installments,
                               loan_detail=loan_detail, payments=payments, payments_by_datetime=payments_by_datetime, user_id=session['user_id'])
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


@routes.route('/confirm_payment', methods=['POST'])
def confirm_payment():
    # Obtener y normalizar parámetros del formulario
    loan_id_raw = request.form.get('loan_id') or request.form.get('loanId')
    custom_payment_raw = (request.form.get('customPayment') or '').strip()

    # Normalización de monto: soporta formato español (puntos miles, coma decimal)
    # "10.000" -> 10000 ; "10,5" -> 10.5 ; "10,000" (EN) no esperado en es-ES
    try:
        if not loan_id_raw:
            return jsonify({"error": "Falta el parámetro loan_id."}), 400
        loan_id = int(loan_id_raw)

        if not custom_payment_raw:
            return jsonify({"error": "Falta el monto de pago."}), 400

        normalized_amount = custom_payment_raw.replace('.', '').replace(',', '.')
        custom_payment = float(normalized_amount)
    except ValueError:
        return jsonify({"error": "Formato de monto inválido."}), 400

    # Validar que el pago sea mayor a 0
    if custom_payment <= 0:
        return jsonify({"error": "El monto del pago debe ser mayor a 0."}), 400

    # Optimización: Eager loading con una sola consulta
    loan = Loan.query.options(
        joinedload(Loan.client),
        joinedload(Loan.installments)
    ).get(loan_id)
    
    if not loan:
        return jsonify({"error": "Préstamo no encontrado."}), 404

    # Optimización: Calcular fechas una sola vez
    current_datetime = datetime.now()
    current_date = current_datetime.date()

    # Optimización: Pre-filtrar cuotas pendientes una sola vez
    pending_installments = [
        installment for installment in loan.installments 
        if installment.status in [InstallmentStatus.PENDIENTE, InstallmentStatus.MORA, InstallmentStatus.ABONADA]
        and installment.amount > 0
    ]

    # Validar que haya montos pendientes para pagar
    if not pending_installments:
        return jsonify({"error": "No hay montos pendientes para pagar."}), 400

    # Optimización: Calcular total pendiente una sola vez
    total_amount_due = sum(installment.amount for installment in pending_installments)

    # Actualizar caja del empleado
    employee = Employee.query.get(loan.employee_id)
    if not employee:
        return jsonify({"error": "Empleado asociado no encontrado."}), 404
    employee.box_value += Decimal(custom_payment)

    # Optimización: Preparar lista para operaciones en lote
    payments_to_create = []

    if custom_payment >= total_amount_due:
        # Pago completo - procesar todas las cuotas pendientes
        for installment in pending_installments:
            # Guardar el monto pendiente antes de ponerlo en 0
            installment_amount_due = installment.amount
            installment.status = InstallmentStatus.PAGADA
            installment.payment_date = current_datetime
            installment.amount = 0

            payment = Payment(
                amount=installment_amount_due,
                payment_date=current_datetime,
                installment_id=installment.id
            )
            payments_to_create.append(payment)
        
        # Actualizar el estado del préstamo y el campo up_to_date
        loan.status = False  # 0 indica que el préstamo está pagado en su totalidad
        loan.up_to_date = True
        loan.modification_date = current_datetime
        
    else:
        # Pago parcial - ordenar por fecha de vencimiento
        pending_installments.sort(key=lambda x: x.due_date if x.due_date else datetime.max)
        
        remaining_payment = Decimal(custom_payment)
        
        for installment in pending_installments:
            if remaining_payment <= 0:
                break
                
            # El monto pendiente de esta cuota
            installment_amount_due = installment.amount
            
            if remaining_payment >= installment_amount_due:
                # El pago cubre completamente esta cuota
                installment.status = InstallmentStatus.PAGADA
                installment.payment_date = current_datetime
                installment.amount = 0
                
                # Crear el pago por el monto completo de la cuota
                payment = Payment(
                    amount=installment_amount_due, 
                    payment_date=current_datetime,
                    installment_id=installment.id
                )
                payments_to_create.append(payment)
                remaining_payment -= installment_amount_due
                
                # Si el pago restante es exactamente 0, significa que se pagó completamente
                if remaining_payment == 0:
                    break
            else:
                # El pago solo cubre parcialmente esta cuota
                installment.status = InstallmentStatus.ABONADA
                installment.amount -= remaining_payment
                
                # Crear el pago por el monto parcial
                payment = Payment(
                    amount=remaining_payment, 
                    payment_date=current_datetime,
                    installment_id=installment.id
                )
                payments_to_create.append(payment)
                remaining_payment = 0
        
        # Actualizar el campo modification_date del préstamo después de procesar el pago parcial
        loan.modification_date = current_datetime
        # Resetear first_modification_date si es el primer cambio del día
        if not loan.client.first_modification_date or loan.client.first_modification_date.date() != current_date:
            loan.client.first_modification_date = current_datetime
        loan.client.debtor = False

    # Determinar si el préstamo debe marcarse como finalizado
    remaining_outstanding = sum(
        inst.amount for inst in loan.installments
        if inst.status in [InstallmentStatus.PENDIENTE, InstallmentStatus.ABONADA, InstallmentStatus.MORA]
        and inst.amount > 0
    )

    if remaining_outstanding == 0:
        loan.status = False
        loan.up_to_date = True
        loan.modification_date = current_datetime

    # Operaciones en lote
    db.session.add_all(payments_to_create)
    db.session.commit()

    # Invalidar cache después del pago - DESHABILITADO
    # current_cache = get_cache()
    # if hasattr(current_cache, 'app') and current_cache.app:
    #     current_cache.delete_memoized(get_salesman_customers_data, loan.employee_id)
    #     current_cache.delete_memoized(get_salesman_pending_installments, loan.employee_id)
    #     current_cache.delete_memoized(check_all_loans_paid_today, loan.employee_id)
    #     current_cache.delete_memoized(get_salesman_collected_clients, loan.employee_id)
    #     current_cache.delete_memoized(get_salesman_transaction_details, loan.employee_id)

    return jsonify({"message": "El pago se ha registrado correctamente."}), 200


@routes.route('/mark_overdue', methods=['POST'])
def mark_overdue():
    # Obtener el ID del préstamo de la solicitud POST
    loan_id_raw = request.form.get('loan_id') or request.form.get('loanId')
    try:
        if not loan_id_raw:
            return jsonify({"error": "Falta el parámetro loan_id."}), 400
        loan_id = int(loan_id_raw)
    except ValueError:
        return jsonify({"error": "loan_id inválido."}), 400

    # Buscar la primera cuota pendiente del préstamo específico
    pending_installment = LoanInstallment.query.filter(
        LoanInstallment.loan_id == loan_id,
         LoanInstallment.status.in_([InstallmentStatus.PENDIENTE, InstallmentStatus.ABONADA])
    ).order_by(LoanInstallment.due_date.asc()).first()

    if pending_installment:
        pending_installment.status = InstallmentStatus.MORA
        if pending_installment.payment_date is None:
            pending_installment.payment_date = datetime.now().date()

        client = Client.query.join(Loan).filter(Loan.id == loan_id).first()
        if client:
            client.debtor = True
            # Resetear first_modification_date si es el primer cambio del día
            if not client.first_modification_date or client.first_modification_date.date() != datetime.now().date():
                client.first_modification_date = datetime.now()
            db.session.add(client)

        payment = Payment(
            amount=0,
            payment_date=datetime.now(),
            installment_id=pending_installment.id
        )
        db.session.add(payment)
        db.session.commit()

        return jsonify({"message": "Cuota marcada como MORA y cliente marcado deudor."}), 200

    # Si no hay cuotas pendientes, verificar si ya hay cuotas en MORA
    overdue_installments = LoanInstallment.query.filter(
        LoanInstallment.loan_id == loan_id,
        LoanInstallment.status == InstallmentStatus.MORA
    ).all()

    if overdue_installments:
        client = Client.query.join(Loan).filter(Loan.id == loan_id).first()
        if client:
            client.debtor = True
            # Resetear first_modification_date si es el primer cambio del día
            if not client.first_modification_date or client.first_modification_date.date() != datetime.now().date():
                client.first_modification_date = datetime.now()
            db.session.add(client)

        first_overdue_installment = overdue_installments[0]
        payment = Payment(
            amount=0,
            payment_date=datetime.now(),
            installment_id=first_overdue_installment.id
        )
        db.session.add(payment)
        db.session.commit()

        return jsonify({"message": "Cliente marcado deudor, se registró pago 0 sobre cuota en MORA."}), 200

    return jsonify({"error": "No se encontraron cuotas para marcar como MORA"}), 404


# Constantes para estados de caja
BOX_STATUS = {
    'CLOSED': 'Cerrada',
    'ACTIVE': 'Activa', 
    'DEACTIVATED': 'Desactivada'
}

def calculate_status_box(employee_status, all_loans_paid_today):
    """
    Calcula el estado de la caja basado en el estado del empleado y si todos los préstamos están pagados hoy.
    
    Lógica de negocio:
    - Si empleado está activo y todos los préstamos pagados hoy → Caja Cerrada
    - Si empleado está inactivo y todos los préstamos pagados hoy → Caja Activa  
    - Si empleado está inactivo y no todos los préstamos pagados hoy → Caja Desactivada
    - Si empleado está activo y no todos los préstamos pagados hoy → Caja Activa (caso por defecto)
    
    Args:
        employee_status (bool): Estado del empleado (True=activo, False=inactivo)
        all_loans_paid_today (bool): Si todos los préstamos están pagados hoy
    
    Returns:
        str: Estado de la caja ("Cerrada", "Activa", "Desactivada")
    """
    # Validar parámetros
    if not isinstance(employee_status, bool) or not isinstance(all_loans_paid_today, bool):
        return BOX_STATUS['ACTIVE']  # Estado por defecto en caso de error
    
    # Empleado activo y todos los préstamos pagados hoy
    if employee_status and all_loans_paid_today:
        return BOX_STATUS['CLOSED']
    
    # Empleado inactivo y todos los préstamos pagados hoy
    if not employee_status and all_loans_paid_today:
        return BOX_STATUS['ACTIVE']
    
    # Empleado inactivo y no todos los préstamos pagados hoy
    if not employee_status and not all_loans_paid_today:
        return BOX_STATUS['DEACTIVATED']
    
    # Empleado activo y no todos los préstamos pagados hoy (caso por defecto)
    return BOX_STATUS['ACTIVE']


@routes.route('/payment_list/<int:user_id>', methods=['GET'])
def payments_list(user_id):
    # Validar user_id
    if not user_id or user_id <= 0:
        return jsonify({"error": "ID de usuario inválido"}), 400

    current_date = datetime.now().date()

    # Optimización 1: Una sola consulta para obtener empleado con sus clientes
    employee = db.session.query(Employee).options(
        joinedload(Employee.clients)
    ).filter_by(user_id=user_id).first()

    if not employee:
        return jsonify({"error": "No se encontró el empleado asociado al usuario."}), 404

    employee_id = employee.id
    employee_status = employee.status

    # Optimización 2: Una sola consulta para obtener clientes con pagos hoy
    clients_with_payments_today = set(
        db.session.query(Loan.client_id).join(
            LoanInstallment, Loan.id == LoanInstallment.loan_id
        ).join(
            Payment, LoanInstallment.id == Payment.installment_id
        ).filter(
            Loan.employee_id == employee_id,
            func.date(Payment.payment_date) == current_date
        ).distinct().all()
    )
    
    # La cantidad de clientes con pagos hoy es el tamaño del set
    all_loans_paid_count = len(clients_with_payments_today)

    # Optimización 3: Contar préstamos activos (status=True) más los inactivos modificados hoy
    active_loans_count = db.session.query(Loan).filter(
        Loan.employee_id == employee_id,
        (Loan.status == True) | 
        ((Loan.status == False) & (func.date(Loan.modification_date) == current_date))
    ).count()

    # Determinar si todos los préstamos están pagados hoy
    all_loans_paid_today = (active_loans_count == all_loans_paid_count)

    # Optimización 4: Calcular el total de cobros para el día
    total_collections_today = db.session.query(
        func.sum(Payment.amount)
    ).join(
        LoanInstallment, Payment.installment_id == LoanInstallment.id
    ).join(
        Loan, LoanInstallment.loan_id == Loan.id
    ).join(
        Client, Loan.client_id == Client.id
    ).filter(
        Client.employee_id == employee_id,
        func.date(Payment.payment_date) == current_date
    ).scalar() or 0


    # Optimización 9: Usar función separada para calcular status_box
    status_box = calculate_status_box(employee_status, all_loans_paid_today)


    # Inicializa la lista para almacenar la información de los clientes
    clients_information = []
    clients_information_paid = []
    processed_clients_information = []

    # Optimización 5: Obtener préstamos activos del empleado en una sola consulta
    loans = db.session.query(Loan).join(Client, Loan.client_id == Client.id).filter(
        Client.employee_id == employee_id,
        Loan.status == True
    ).all()

    # Obtener préstamos procesados hoy (con pagos)
    processed_loans = db.session.query(Loan).join(Client, Loan.client_id == Client.id).join(
        LoanInstallment, Loan.id == LoanInstallment.loan_id
    ).join(
        Payment, LoanInstallment.id == Payment.installment_id
    ).filter(
        Client.employee_id == employee_id,
        func.date(Payment.payment_date) == current_date
    ).distinct().all()

    if loans:
        loan_ids = [l.id for l in loans]

        # Optimización 6: Una sola consulta para todas las agregaciones por préstamo
        from sqlalchemy import case
        
        loan_aggregations = db.session.query(
            LoanInstallment.loan_id,
            func.count(case((LoanInstallment.status == InstallmentStatus.PAGADA, LoanInstallment.id), else_=None)).label('paid_installments'),
            func.coalesce(func.sum(case((LoanInstallment.status.in_([InstallmentStatus.PAGADA, InstallmentStatus.ABONADA]), Payment.amount), else_=0)), 0).label('total_paid_amount'),
            func.count(case((LoanInstallment.status == InstallmentStatus.MORA, LoanInstallment.id), else_=None)).label('overdue_installments'),
            func.coalesce(func.sum(case((LoanInstallment.status == InstallmentStatus.MORA, LoanInstallment.amount), else_=0)), 0).label('overdue_amount'),
            func.coalesce(func.sum(case((LoanInstallment.status.in_([InstallmentStatus.PENDIENTE, InstallmentStatus.ABONADA, InstallmentStatus.MORA]), LoanInstallment.amount), else_=0)), 0).label('outstanding_amount'),
            func.coalesce(func.sum(case((LoanInstallment.status.in_([InstallmentStatus.ABONADA, InstallmentStatus.PAGADA]), LoanInstallment.fixed_amount), else_=0)), 0).label('amount_paid_installments')
        ).outerjoin(Payment, Payment.installment_id == LoanInstallment.id) \
         .filter(LoanInstallment.loan_id.in_(loan_ids)) \
         .group_by(LoanInstallment.loan_id).all()

        # Convertir a diccionarios para compatibilidad
        paid_installments_by_loan = {row.loan_id: row.paid_installments for row in loan_aggregations}
        total_paid_amount_by_loan = {row.loan_id: float(row.total_paid_amount) for row in loan_aggregations}
        overdue_counts_by_loan = {row.loan_id: row.overdue_installments for row in loan_aggregations}
        overdue_amount_by_loan = {row.loan_id: float(row.overdue_amount) for row in loan_aggregations}
        outstanding_amount_by_loan = {row.loan_id: float(row.outstanding_amount) for row in loan_aggregations}
        amount_paid_installments_by_loan = {row.loan_id: float(row.amount_paid_installments) for row in loan_aggregations}

        # Optimización 7: Una sola consulta para datos adicionales de préstamos
        loan_additional_data = db.session.query(
            LoanInstallment.loan_id,
            func.max(case((Payment.payment_date.isnot(None), Payment.payment_date), else_=None)).label('last_payment_date'),
            func.min(case((LoanInstallment.status.in_([InstallmentStatus.PENDIENTE, InstallmentStatus.MORA, InstallmentStatus.ABONADA]), LoanInstallment.due_date), else_=None)).label('next_due_date'),
            func.min(LoanInstallment.fixed_amount).label('fixed_amount'),
            func.max(case((LoanInstallment.status.in_([InstallmentStatus.PAGADA, InstallmentStatus.ABONADA, InstallmentStatus.MORA]), LoanInstallment.due_date), else_=None)).label('prev_due_date')
        ).outerjoin(Payment, Payment.installment_id == LoanInstallment.id) \
         .filter(LoanInstallment.loan_id.in_(loan_ids)) \
         .group_by(LoanInstallment.loan_id).all()

        # Convertir a diccionarios
        last_payment_by_loan = {row.loan_id: row.last_payment_date for row in loan_additional_data if row.last_payment_date}
        next_due_by_loan = {row.loan_id: row.next_due_date for row in loan_additional_data if row.next_due_date}
        fixed_amount_by_loan = {row.loan_id: row.fixed_amount for row in loan_additional_data if row.fixed_amount}
        prev_due_by_loan = {row.loan_id: row.prev_due_date for row in loan_additional_data if row.prev_due_date}

        # Obtener estado de cuota previa y actual
        prev_status_by_loan = {}
        current_status_by_loan = {}
        if prev_due_by_loan:
            prev_status_rows = db.session.query(
                LoanInstallment.loan_id,
                LoanInstallment.status
            ).filter(
                tuple_(LoanInstallment.loan_id, LoanInstallment.due_date).in_(
                    [(lid, due) for lid, due in prev_due_by_loan.items()]
                )
            ).all()
            prev_status_by_loan = {lid: status for lid, status in prev_status_rows}
        
        # Obtener el estado actual de la cuota pendiente más próxima
        current_status_rows = db.session.query(
            LoanInstallment.loan_id,
            LoanInstallment.status,
            LoanInstallment.amount
        ).filter(
            LoanInstallment.loan_id.in_(loan_ids),
            LoanInstallment.status.in_([InstallmentStatus.PENDIENTE, InstallmentStatus.MORA, InstallmentStatus.ABONADA])
        ).order_by(LoanInstallment.loan_id, LoanInstallment.due_date.asc()).all()
        
        # Agrupar por loan_id y tomar la primera cuota pendiente
        for loan_id, status, amount in current_status_rows:
            if loan_id not in current_status_by_loan:
                # Si la cuota tiene monto 0, debería estar PAGADA
                if amount == 0:
                    current_status_by_loan[loan_id] = InstallmentStatus.PAGADA
                else:
                    current_status_by_loan[loan_id] = status
        
        # Obtener el estado de la última cuota procesada (pagada o abonada)
        last_processed_status_rows = db.session.query(
            LoanInstallment.loan_id,
            LoanInstallment.status,
            LoanInstallment.amount,
            LoanInstallment.due_date
        ).filter(
            LoanInstallment.loan_id.in_(loan_ids),
            LoanInstallment.status.in_([InstallmentStatus.PAGADA, InstallmentStatus.ABONADA])
        ).order_by(LoanInstallment.loan_id, LoanInstallment.due_date.desc()).all()
        
        # Agrupar por loan_id y tomar la última cuota procesada
        last_processed_by_loan = {}
        for loan_id, status, amount, due_date in last_processed_status_rows:
            if loan_id not in last_processed_by_loan:
                last_processed_by_loan[loan_id] = status

        # Construcción final sin N+1
        client_by_id = {c.id: c for c in employee.clients}
        for loan in loans:
            client = client_by_id.get(loan.client_id)
            if not client:
                continue

            installment_value = fixed_amount_by_loan.get(loan.id, 0) or 0
            total_paid_amount = float(total_paid_amount_by_loan.get(loan.id, 0) or 0)
            paid_installments = int(paid_installments_by_loan.get(loan.id, 0) or 0)
            cuota_number_with_decimal = (total_paid_amount / float(installment_value)) if installment_value else paid_installments

            overdue_installments = int(overdue_counts_by_loan.get(loan.id, 0) or 0)
            total_overdue_amount = float(overdue_amount_by_loan.get(loan.id, 0) or 0)
            
            # Calcular el saldo pendiente real usando la misma lógica que credit_detail
            valor_total_prestamo = float(loan.amount + (loan.amount * loan.interest / 100))
            # Usar la misma consulta que get_loan_details: sumar TODOS los pagos realizados
            total_pagos_realizados = db.session.query(func.sum(Payment.amount)).join(
                LoanInstallment, Payment.installment_id == LoanInstallment.id
            ).filter(
                LoanInstallment.loan_id == loan.id
            ).scalar() or 0
            total_outstanding_amount = float(valor_total_prestamo - float(total_pagos_realizados))
            
            total_amount_paid = float(amount_paid_installments_by_loan.get(loan.id, 0) or 0)

            next_due = next_due_by_loan.get(loan.id)
            last_payment_date = last_payment_by_loan.get(loan.id)
            prev_status = prev_status_by_loan.get(loan.id)
            current_status = current_status_by_loan.get(loan.id)
            last_processed_status = last_processed_by_loan.get(loan.id)

            approved = 'Aprobado' if loan.approved else 'Pendiente de Aprobación'

            # Calcular el estado de la cuota de manera más precisa
            if total_outstanding_amount == 0:
                installment_status = 'PAGADA'
            elif overdue_installments > 0:
                installment_status = 'MORA'
            elif last_processed_status:
                # Si hay una cuota procesada recientemente, mostrar su estado
                installment_status = last_processed_status.value
            elif current_status:
                # Verificar si la cuota actual tiene monto 0 (completamente pagada)
                if current_status == InstallmentStatus.PAGADA or current_status.value == 'PAGADA':
                    installment_status = 'PAGADA'
                else:
                    installment_status = current_status.value
            else:
                installment_status = 'PENDIENTE'

            client_info = {
                'First Name': client.first_name,
                'Last Name': client.last_name,
                'Alias Client': client.alias,
                'Paid Installments': paid_installments,
                'Overdue Installments': overdue_installments,
                'Total Outstanding Amount': total_outstanding_amount,
                'Total Amount Paid': total_amount_paid,
                'Total Overdue Amount': total_overdue_amount,
                'Last Payment Date': last_payment_date.isoformat() if last_payment_date else 0,
                'Last Payment Date front': last_payment_date.strftime('%Y-%m-%d') if last_payment_date else '0',
                'Loan ID': loan.id,
                'Approved': approved,
                'Installment Value': installment_value,
                'Total Installments': loan.dues,
                'Sales Date': loan.creation_date.isoformat(),
                'Next Installment Date': next_due.isoformat() if next_due else 0,
                'Next Installment Date front': next_due.strftime('%Y-%m-%d') if next_due else '0',
                'Cuota Number': round(cuota_number_with_decimal, 2),
                'Due Date': next_due.isoformat() if next_due else 0,
                'Installment Status': installment_status,
                'Previous Installment Status': prev_status.value if prev_status else None,
                'Last Loan Modification Date': loan.modification_date.isoformat() if loan.modification_date else None,
                'Previous Installment Paid Amount': 0,
                'Current Date': current_date,
                'First Installment Value': installment_value if loan.creation_date.date() != datetime.now().date() else 0,
                'First Modification Date': client.first_modification_date.isoformat() if client.first_modification_date else None,
            }

            # Filtrar préstamos: ocultar si el estado actual no es PENDIENTE y el último pago fue hoy
            should_hide = (
                installment_status != 'PENDIENTE' and 
                last_payment_date and 
                last_payment_date.date() == current_date
            )
            
            if not should_hide:
                clients_information.append(client_info)


        # Optimización 8: Préstamos cerrados hoy con una sola consulta
        closed_loans_today = db.session.query(
            Loan.id,
            func.sum(Payment.amount).label('total_paid')
        ).join(LoanInstallment, Loan.id == LoanInstallment.loan_id) \
         .join(Payment, LoanInstallment.id == Payment.installment_id) \
         .join(Client, Loan.client_id == Client.id) \
         .filter(
            Client.employee_id == employee_id,
            Loan.status == False,
            Loan.up_to_date == True,
            func.date(Loan.modification_date) == current_date
         ).group_by(Loan.id).all()

        # Agregar datos de préstamos cerrados
        for loan_id, total_paid in closed_loans_today:
            client_information_paid = {
                'Total Installment Value Paid': float(total_paid) if total_paid else 0,
            }
            clients_information_paid.append(client_information_paid)

    # Procesar préstamos procesados hoy (con pagos)
    if processed_loans:
        processed_loan_ids = [l.id for l in processed_loans]
        
        # Obtener datos de agregación para préstamos procesados
        processed_loan_aggregations = db.session.query(
            LoanInstallment.loan_id,
            db.func.count(db.case((LoanInstallment.status == InstallmentStatus.PAGADA, LoanInstallment.id), else_=None)).label('paid_installments'),
            db.func.coalesce(db.func.sum(db.case((LoanInstallment.status.in_([InstallmentStatus.PAGADA, InstallmentStatus.ABONADA]), Payment.amount), else_=0)), 0).label('total_paid_amount'),
            db.func.count(db.case((LoanInstallment.status == InstallmentStatus.MORA, LoanInstallment.id), else_=None)).label('overdue_installments'),
            db.func.coalesce(db.func.sum(db.case((LoanInstallment.status == InstallmentStatus.MORA, LoanInstallment.amount), else_=0)), 0).label('overdue_amount'),
            db.func.coalesce(db.func.sum(db.case((LoanInstallment.status.in_([InstallmentStatus.PENDIENTE, InstallmentStatus.ABONADA, InstallmentStatus.MORA]), LoanInstallment.amount), else_=0)), 0).label('outstanding_amount'),
            db.func.coalesce(db.func.sum(db.case((LoanInstallment.status.in_([InstallmentStatus.ABONADA, InstallmentStatus.PAGADA]), LoanInstallment.fixed_amount), else_=0)), 0).label('amount_paid_installments')
        ).outerjoin(Payment, Payment.installment_id == LoanInstallment.id) \
         .filter(LoanInstallment.loan_id.in_(processed_loan_ids)) \
         .group_by(LoanInstallment.loan_id).all()

        # Convertir a diccionarios
        processed_paid_installments_by_loan = {row.loan_id: row.paid_installments for row in processed_loan_aggregations}
        processed_total_paid_amount_by_loan = {row.loan_id: float(row.total_paid_amount) for row in processed_loan_aggregations}
        processed_overdue_counts_by_loan = {row.loan_id: row.overdue_installments for row in processed_loan_aggregations}
        processed_overdue_amount_by_loan = {row.loan_id: float(row.overdue_amount) for row in processed_loan_aggregations}
        processed_outstanding_amount_by_loan = {row.loan_id: float(row.outstanding_amount) for row in processed_loan_aggregations}
        processed_amount_paid_installments_by_loan = {row.loan_id: float(row.amount_paid_installments) for row in processed_loan_aggregations}

        # Obtener datos adicionales para préstamos procesados
        processed_loan_additional_data = db.session.query(
            LoanInstallment.loan_id,
            db.func.max(db.case((Payment.payment_date.isnot(None), Payment.payment_date), else_=None)).label('last_payment_date'),
            db.func.min(db.case((LoanInstallment.status.in_([InstallmentStatus.PENDIENTE, InstallmentStatus.MORA, InstallmentStatus.ABONADA]), LoanInstallment.due_date), else_=None)).label('next_due_date'),
            db.func.min(LoanInstallment.fixed_amount).label('fixed_amount'),
            db.func.max(db.case((LoanInstallment.status.in_([InstallmentStatus.PAGADA, InstallmentStatus.ABONADA, InstallmentStatus.MORA]), LoanInstallment.due_date), else_=None)).label('prev_due_date')
        ).outerjoin(Payment, Payment.installment_id == LoanInstallment.id) \
         .filter(LoanInstallment.loan_id.in_(processed_loan_ids)) \
         .group_by(LoanInstallment.loan_id).all()

        # Convertir a diccionarios
        processed_last_payment_by_loan = {row.loan_id: row.last_payment_date for row in processed_loan_additional_data if row.last_payment_date}
        processed_next_due_by_loan = {row.loan_id: row.next_due_date for row in processed_loan_additional_data if row.next_due_date}
        processed_fixed_amount_by_loan = {row.loan_id: row.fixed_amount for row in processed_loan_additional_data if row.fixed_amount}
        processed_prev_due_by_loan = {row.loan_id: row.prev_due_date for row in processed_loan_additional_data if row.prev_due_date}

        # Obtener estado de la última cuota procesada para préstamos procesados
        processed_last_processed_status_rows = db.session.query(
            LoanInstallment.loan_id,
            LoanInstallment.status,
            LoanInstallment.amount,
            LoanInstallment.due_date
        ).filter(
            LoanInstallment.loan_id.in_(processed_loan_ids),
            LoanInstallment.status.in_([InstallmentStatus.PAGADA, InstallmentStatus.ABONADA])
        ).order_by(LoanInstallment.loan_id, LoanInstallment.due_date.desc()).all()
        
        processed_last_processed_by_loan = {}
        for loan_id, status, amount, due_date in processed_last_processed_status_rows:
            if loan_id not in processed_last_processed_by_loan:
                processed_last_processed_by_loan[loan_id] = status

        # Construir información de clientes procesados
        processed_client_by_id = {c.id: c for c in employee.clients}
        for loan in processed_loans:
            client = processed_client_by_id.get(loan.client_id)
            if not client:
                continue

            installment_value = processed_fixed_amount_by_loan.get(loan.id, 0) or 0
            total_paid_amount = float(processed_total_paid_amount_by_loan.get(loan.id, 0) or 0)
            paid_installments = int(processed_paid_installments_by_loan.get(loan.id, 0) or 0)
            cuota_number_with_decimal = (total_paid_amount / float(installment_value)) if installment_value else paid_installments

            overdue_installments = int(processed_overdue_counts_by_loan.get(loan.id, 0) or 0)
            total_overdue_amount = float(processed_overdue_amount_by_loan.get(loan.id, 0) or 0)
            
            # Calcular el saldo pendiente real usando la misma lógica que credit_detail
            valor_total_prestamo = float(loan.amount + (loan.amount * loan.interest / 100))
            # Usar la misma consulta que get_loan_details: sumar TODOS los pagos realizados
            total_pagos_realizados = db.session.query(func.sum(Payment.amount)).join(
                LoanInstallment, Payment.installment_id == LoanInstallment.id
            ).filter(
                LoanInstallment.loan_id == loan.id
            ).scalar() or 0
            total_outstanding_amount = float(valor_total_prestamo - float(total_pagos_realizados))
            
            total_amount_paid = float(processed_amount_paid_installments_by_loan.get(loan.id, 0) or 0)

            next_due = processed_next_due_by_loan.get(loan.id)
            last_payment_date = processed_last_payment_by_loan.get(loan.id)
            last_processed_status = processed_last_processed_by_loan.get(loan.id)

            approved = 'Aprobado' if loan.approved else 'Pendiente de Aprobación'

            # Calcular el estado de la cuota de manera más precisa
            if total_outstanding_amount == 0:
                installment_status = 'PAGADA'
            elif overdue_installments > 0:
                installment_status = 'MORA'
            elif last_processed_status:
                installment_status = last_processed_status.value
            else:
                installment_status = 'PENDIENTE'

            processed_client_info = {
                'First Name': client.first_name,
                'Last Name': client.last_name,
                'Alias Client': client.alias,
                'Paid Installments': paid_installments,
                'Overdue Installments': overdue_installments,
                'Total Outstanding Amount': total_outstanding_amount,
                'Total Amount Paid': total_amount_paid,
                'Total Overdue Amount': total_overdue_amount,
                'Last Payment Date': last_payment_date.isoformat() if last_payment_date else 0,
                'Last Payment Date front': last_payment_date.strftime('%Y-%m-%d') if last_payment_date else '0',
                'Loan ID': loan.id,
                'Approved': approved,
                'Installment Value': installment_value,
                'Total Installments': loan.dues,
                'Sales Date': loan.creation_date.isoformat(),
                'Next Installment Date': next_due.isoformat() if next_due else 0,
                'Next Installment Date front': next_due.strftime('%Y-%m-%d') if next_due else '0',
                'Cuota Number': round(cuota_number_with_decimal, 2),
                'Due Date': next_due.isoformat() if next_due else 0,
                'Installment Status': installment_status,
                'Previous Installment Status': None,
                'Last Loan Modification Date': loan.modification_date.isoformat() if loan.modification_date else None,
                'Previous Installment Paid Amount': 0,
                'Current Date': current_date,
                'First Installment Value': installment_value if loan.creation_date.date() != datetime.now().date() else 0,
                'First Modification Date': client.first_modification_date.isoformat() if client.first_modification_date else None,
                'is_processed': True  # Marcar como procesado para el frontend
            }

            processed_clients_information.append(processed_client_info)

    # Obtén el término de búsqueda del formulario
    search_term = request.args.get('search', '')

    # Filtra los clientes según el término de búsqueda
    filtered_clients_information = [client_info for client_info in clients_information if
                                    search_term.lower() in f"{client_info['First Name']} {client_info['Last Name']}".lower()]

    # Ordena la lista filtrada por fecha de modificación ascendente
    filtered_clients_information.sort(
        key=lambda x: x['First Modification Date'] or datetime.max
    )

    # Calcular el debido cobrar usando la misma lógica que en el endpoint /box
    total_pending_installments_amount = 0
    total_pending_installments_loan_close_amount = 0
    
    # Calcular cuotas pendientes para préstamos activos
    for client in employee.clients:
        for loan in client.loans:
            # Excluir préstamos creados hoy mismo
            if loan.creation_date.date() == current_date:
                continue
            
            if loan.status:
                # Encuentra la primera cuota ordenada por fecha de vencimiento (igual que en /box)
                pending_installment = LoanInstallment.query.filter(
                    LoanInstallment.loan_id == loan.id
                ).order_by(LoanInstallment.due_date.asc()).first()
                if pending_installment:
                    total_pending_installments_amount += pending_installment.fixed_amount
            elif loan.status == False and loan.up_to_date and loan.modification_date.date() == current_date:
                pending_installment_paid = LoanInstallment.query.filter(
                    LoanInstallment.loan_id == loan.id
                ).order_by(LoanInstallment.due_date.asc()).first()
                if pending_installment_paid:
                    total_pending_installments_loan_close_amount += pending_installment_paid.fixed_amount

    # Calcular el total combinado (debido cobrar + préstamos cerrados hoy)
    total_combined_value = float(total_pending_installments_amount) + float(total_pending_installments_loan_close_amount)

    porcentaje_cobro = int(float(total_collections_today) / float(total_combined_value) *
                           100) if total_combined_value != 0 else 0

    # Renderiza la información filtrada como una respuesta JSON y también renderiza una plantilla
    return render_template('payments-route.html', 
                         clients=filtered_clients_information, 
                         processed_clients=processed_clients_information,
                         status_box=status_box, 
                         employee_id=employee_id, 
                         user_id=user_id, 
                         active_loans_count=active_loans_count, 
                         all_loans_paid_count=all_loans_paid_count, 
                         total_installment_value=total_combined_value, 
                         total_collections_today=total_collections_today, 
                         porcentaje_cobro=porcentaje_cobro)


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

    # Calcular el progreso de cuotas con decimales (incluyendo abonos parciales)
    total_pagos_realizados = db.session.query(func.sum(Payment.amount)).join(
        LoanInstallment, Payment.installment_id == LoanInstallment.id
    ).filter(
        LoanInstallment.loan_id == loan_id
    ).scalar() or 0
    
    # Calcular el valor de una cuota (asumiendo que todas tienen el mismo valor)
    valor_cuota = valor_total / total_cuotas if total_cuotas > 0 else 0
    cuotas_progreso_decimal = (total_pagos_realizados / valor_cuota) if valor_cuota > 0 else cuotas_pagadas
    
    saldo_pendiente = valor_total - total_pagos_realizados

        

    # Formatear los valores sin decimales
    valor_total = int(valor_total)
    saldo_pendiente = int(saldo_pendiente)

    # Retornar los detalles del préstamo
    detalles_prestamo = {
        'loan_id': loan_id,
        'cuotas_totales': total_cuotas,
        'cuotas_pagadas': cuotas_pagadas,
        'cuotas_progreso_decimal': round(cuotas_progreso_decimal, 1),
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


# ==================== FUNCIONES AUXILIARES PARA EL ENDPOINT /box ====================

def validate_coordinator_access():
    """Valida que el usuario esté autenticado y tenga rol de coordinador"""
    user_id = session.get('user_id')
    
    if user_id is None:
        raise ValueError('Usuario no encontrado en la sesión')
    
    user = User.query.get(user_id)
    if user is None or user.role != Role.COORDINADOR:
        raise ValueError('El usuario no es un coordinador válido')
    
    return user_id, user

@safe_cache(timeout=600)  # 10 minutos de caché
def get_coordinator_data(user_id):
    """Obtiene los datos del coordinador y sus vendedores asociados"""
    coordinator = Employee.query.filter_by(user_id=user_id).first()
    if not coordinator:
        raise ValueError('No se encontró el empleado coordinador')
    
    coordinator_cash = coordinator.box_value
    coordinator_name = f"{coordinator.user.first_name} {coordinator.user.last_name}"
    
    # Obtener el ID del manager del coordinador
    manager_id = db.session.query(Manager.id).filter_by(employee_id=coordinator.id).scalar()
    if not manager_id:
        raise ValueError('No se encontró ningún coordinador asociado a este empleado')
    
    # OPTIMIZACIÓN: Cargar vendedores con sus relaciones en una sola consulta
    salesmen = db.session.query(Salesman, Employee, User).join(
        Employee, Salesman.employee_id == Employee.id
    ).join(
        User, Employee.user_id == User.id
    ).filter(Salesman.manager_id == manager_id).all()
    
    return coordinator, coordinator_cash, coordinator_name, manager_id, salesmen

def calculate_daily_transaction_totals(manager_id, current_date, coordinator_id=None):
    """Calcula los totales de transacciones diarias para el coordinador"""
    start_of_day = datetime.combine(current_date, datetime.min.time())
    end_of_day = datetime.combine(current_date, datetime.max.time())
    
    # Total de retiros aprobados (RETIROS del coordinador = INGRESO de subordinados + RETIRO del coordinador)
    # Primero: INGRESO de subordinados (retiros del coordinador)
    total_outbound_from_subordinates = db.session.query(
        func.sum(Transaction.amount).label('total_amount')
    ).join(Salesman, Transaction.employee_id == Salesman.employee_id).filter(
        Transaction.transaction_types == 'INGRESO',
        Transaction.approval_status == 'APROBADA',
        Salesman.manager_id == manager_id,
        Transaction.creation_date.between(start_of_day, end_of_day),
        ~Transaction.description.like('[ELIMINADA]%')
    ).scalar() or 0
    
    # Segundo: RETIRO directo del coordinador (si existe)
    total_outbound_from_coordinator = 0
    if coordinator_id:
        total_outbound_from_coordinator = db.session.query(
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            Transaction.employee_id == coordinator_id,
            Transaction.transaction_types == 'RETIRO',
            Transaction.approval_status == 'APROBADA',
            func.date(Transaction.creation_date) == current_date,
            ~Transaction.description.like('[ELIMINADA]%')
        ).scalar() or 0
    
    total_outbound_amount = float(total_outbound_from_subordinates) + float(total_outbound_from_coordinator)
    
    # Total de ingresos aprobados (INGRESOS del coordinador = RETIRO de subordinados + INGRESO del coordinador)
    # Primero: RETIRO de subordinados (ingresos del coordinador)
    total_inbound_from_subordinates = db.session.query(
        func.sum(Transaction.amount).label('total_amount')
    ).join(Salesman, Transaction.employee_id == Salesman.employee_id).filter(
        Transaction.transaction_types == 'RETIRO',
        Transaction.approval_status == 'APROBADA',
        Salesman.manager_id == manager_id,
        func.date(Transaction.creation_date) == current_date,
        ~Transaction.description.like('[ELIMINADA]%')
    ).scalar() or 0
    
    # Segundo: INGRESO directo del coordinador (si existe)
    total_inbound_from_coordinator = 0
    if coordinator_id:
        total_inbound_from_coordinator = db.session.query(
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            Transaction.employee_id == coordinator_id,
            Transaction.transaction_types == 'INGRESO',
            Transaction.approval_status == 'APROBADA',
            func.date(Transaction.creation_date) == current_date,
            ~Transaction.description.like('[ELIMINADA]%')
        ).scalar() or 0
    
    total_inbound_amount = float(total_inbound_from_subordinates) + float(total_inbound_from_coordinator)
    
    return total_outbound_amount, total_inbound_amount

def get_salesman_daily_collections(salesman_employee_id, current_date):
    """Obtiene el total de cobros diarios de un vendedor"""
    return db.session.query(
        func.sum(Payment.amount)
    ).join(
        LoanInstallment, Payment.installment_id == LoanInstallment.id
    ).join(
        Loan, LoanInstallment.loan_id == Loan.id
    ).filter(
        Loan.client.has(employee_id=salesman_employee_id),
        func.date(Payment.payment_date) == current_date
    ).scalar() or 0

def get_salesman_new_clients_data(salesman_employee_id, current_date):
    """Obtiene datos de clientes nuevos del día"""
    start_of_day = datetime.combine(current_date, datetime.min.time())
    
    # Cantidad de nuevos clientes
    new_clients = Client.query.filter(
        Client.employee_id == salesman_employee_id,
        Client.creation_date >= start_of_day
    ).count()
    
    # Monto total de préstamos de nuevos clientes
    new_clients_loan_amount = Loan.query.join(Client).filter(
        Client.employee_id == salesman_employee_id,
        Loan.creation_date >= start_of_day,
        Loan.is_renewal == False,
        Loan.status == True  # Solo préstamos activos
    ).with_entities(func.sum(Loan.amount)).scalar() or 0
    
    return new_clients, new_clients_loan_amount

def get_salesman_renewals_data(salesman_employee_id, current_date):
    """Obtiene datos de renovaciones del día"""
    start_of_day = datetime.combine(current_date, datetime.min.time())
    
    # Cantidad de renovaciones
    total_renewal_loans = Loan.query.filter(
        Loan.client.has(employee_id=salesman_employee_id),
        Loan.is_renewal == True,
        Loan.status == True,
        Loan.approved == True,
        Loan.creation_date >= start_of_day
    ).count()
    
    # Monto total de renovaciones
    total_renewal_loans_amount = Loan.query.filter(
        Loan.client.has(employee_id=salesman_employee_id),
        Loan.is_renewal == True,
        Loan.status == True,
        Loan.approved == True,
        Loan.creation_date >= start_of_day
    ).with_entities(func.sum(Loan.amount)).scalar() or 0
    
    return total_renewal_loans, total_renewal_loans_amount

def get_salesman_transaction_data(salesman_employee_id, current_date):
    """Obtiene datos de transacciones del vendedor para el día"""
    # Gastos diarios
    daily_expenses_amount = Transaction.query.filter(
        Transaction.employee_id == salesman_employee_id,
        Transaction.transaction_types == TransactionType.GASTO,
        Transaction.approval_status == ApprovalStatus.APROBADA,
        func.date(Transaction.creation_date) == current_date,
        ~Transaction.description.like('[ELIMINADA]%')
    ).with_entities(func.sum(Transaction.amount)).scalar() or 0
    
    daily_expenses_count = Transaction.query.filter(
        Transaction.employee_id == salesman_employee_id,
        Transaction.transaction_types == TransactionType.GASTO,
        Transaction.approval_status == ApprovalStatus.APROBADA,
        func.date(Transaction.creation_date) == current_date,
        ~Transaction.description.like('[ELIMINADA]%')
    ).count() or 0
    
    # Retiros diarios
    daily_withdrawals = Transaction.query.filter(
        Transaction.employee_id == salesman_employee_id,
        Transaction.transaction_types == TransactionType.RETIRO,
        Transaction.approval_status == ApprovalStatus.APROBADA,
        func.date(Transaction.creation_date) == current_date,
        ~Transaction.description.like('[ELIMINADA]%')
    ).with_entities(func.sum(Transaction.amount)).scalar() or 0
    
    daily_withdrawals_count = Transaction.query.filter(
        Transaction.employee_id == salesman_employee_id,
        Transaction.transaction_types == TransactionType.RETIRO,
        Transaction.approval_status == ApprovalStatus.APROBADA,
        func.date(Transaction.creation_date) == current_date,
        ~Transaction.description.like('[ELIMINADA]%')
    ).count() or 0
    
    # Ingresos diarios
    daily_collection = Transaction.query.filter(
        Transaction.employee_id == salesman_employee_id,
        Transaction.transaction_types == TransactionType.INGRESO,
        Transaction.approval_status == ApprovalStatus.APROBADA,
        func.date(Transaction.creation_date) == current_date,
        ~Transaction.description.like('[ELIMINADA]%')
    ).with_entities(func.sum(Transaction.amount)).scalar() or 0
    
    daily_collection_count = Transaction.query.filter(
        Transaction.employee_id == salesman_employee_id,
        Transaction.transaction_types == TransactionType.INGRESO,
        Transaction.approval_status == ApprovalStatus.APROBADA,
        func.date(Transaction.creation_date) == current_date,
        ~Transaction.description.like('[ELIMINADA]%')
    ).count() or 0
    
    return {
        'daily_expenses_amount': daily_expenses_amount,
        'daily_expenses_count': daily_expenses_count,
        'daily_withdrawals': daily_withdrawals,
        'daily_withdrawals_count': daily_withdrawals_count,
        'daily_collection': daily_collection,
        'daily_collection_count': daily_collection_count
    }

@safe_cache(timeout=900)  # 15 minutos de caché
def get_salesman_customers_data(salesman_employee_id):
    """Obtiene datos de clientes del vendedor"""
    employee = Employee.query.get(salesman_employee_id)
    
    # Clientes totales activos
    total_customers = sum(
        1 for client in employee.clients
        for loan in client.loans
        if loan.status
    )
    
    # Clientes en mora
    customers_in_arrears = sum(
        1 for client in employee.clients
        for loan in client.loans
        if loan.status and any(
            installment.status == InstallmentStatus.MORA
            for installment in loan.installments
        )
    )
    
    return total_customers, customers_in_arrears

@safe_cache(timeout=300)  # 5 minutos de caché
def get_salesman_pending_installments(salesman_employee_id, current_date):
    """Calcula cuotas pendientes del vendedor"""
    employee = Employee.query.get(salesman_employee_id)
    total_pending_installments_amount = 0
    total_pending_installments_loan_close_amount = 0
    
    for client in employee.clients:
        for loan in client.loans:
            # Excluir préstamos creados hoy mismo
            if loan.creation_date.date() == current_date:
                continue
            
            if loan.status:
                # Encuentra la última cuota pendiente
                pending_installment = LoanInstallment.query.filter(
                    LoanInstallment.loan_id == loan.id
                ).order_by(LoanInstallment.due_date.asc()).first()
                if pending_installment:
                    total_pending_installments_amount += pending_installment.fixed_amount
            elif loan.status == False and loan.up_to_date and loan.modification_date.date() == current_date:
                pending_installment_paid = LoanInstallment.query.filter(
                    LoanInstallment.loan_id == loan.id
                ).order_by(LoanInstallment.due_date.asc()).first()
                total_pending_installments_loan_close_amount += pending_installment_paid.fixed_amount
    
    return total_pending_installments_amount, total_pending_installments_loan_close_amount

@safe_cache(timeout=300)  # 5 minutos de caché
def check_all_loans_paid_today(salesman_employee_id, current_date):
    """Verifica si todos los préstamos fueron pagados hoy"""
    all_loans_paid = Loan.query.filter_by(employee_id=salesman_employee_id)
    all_loans_paid_today = False
    
    for loan in all_loans_paid:
        loan_installments = LoanInstallment.query.filter_by(loan_id=loan.id).all()
        for installment in loan_installments:
            payments = Payment.query.filter_by(installment_id=installment.id).all()
            if any(payment.payment_date.date() == current_date for payment in payments):
                all_loans_paid_today = True
                break
        if all_loans_paid_today:
            break
    
    return all_loans_paid_today

def calculate_box_value(initial_box_value, total_collections_today, daily_withdrawals, 
                       daily_expenses_amount, daily_collection, new_clients_loan_amount, 
                       total_renewal_loans_amount, existing_record_today):
    """
    Calcula el valor de caja del vendedor usando la misma fórmula que al guardar el registro.
    
    Fórmula de guardado (process_salesman_record):
    closing_total = initial_state + paid_installments_amount + partial_installments + daily_incomes_amount
                  - new_clients_loan_amount - total_renewal_loans_amount
                  - daily_withdrawals_amount - daily_expenses_amount
    
    En tiempo real, total_collections_today representa paid_installments_amount + partial_installments
    ya que suma todos los pagos del día (PAGADA y ABONADA).
    """
    # Valor inicial (último closing_total del día anterior)
    total_ingresos = float(initial_box_value)
    
    # Movimientos de ingreso: pagos del día + ingresos por transacciones
    # total_collections_today ya incluye pagos completos (paid) y parciales (partial)
    total_movimientos = float(total_collections_today) + float(daily_collection)
    
    # Egresos: retiros + gastos + nuevos préstamos + renovaciones
    total_egresos = float(daily_withdrawals) + float(daily_expenses_amount) + float(new_clients_loan_amount) + float(total_renewal_loans_amount)
    
    # Fórmula: inicial + movimientos - egresos
    return total_movimientos + total_ingresos - total_egresos

@safe_cache(timeout=180)  # 3 minutos de caché
def get_salesman_transaction_details(salesman_employee_id, current_date):
    """Obtiene detalles de transacciones del vendedor"""
    transactions = Transaction.query.filter(
        Transaction.employee_id == salesman_employee_id,
        ~Transaction.description.like('[ELIMINADA]%')
    ).order_by(Transaction.creation_date.desc()).all()
    
    today = current_date
    expenses = [trans for trans in transactions if
                trans.transaction_types == TransactionType.GASTO and trans.approval_status == ApprovalStatus.APROBADA and trans.creation_date.date() == today]
    incomes = [trans for trans in transactions if
               trans.transaction_types == TransactionType.INGRESO and trans.approval_status == ApprovalStatus.APROBADA and trans.creation_date.date() == today]
    withdrawals = [trans for trans in transactions if
                   trans.transaction_types == TransactionType.RETIRO and trans.approval_status == ApprovalStatus.APROBADA and trans.creation_date.date() == today]
    
    expense_details = [
        {'description': trans.description, 'amount': trans.amount, 'approval_status': trans.approval_status.name,
         'attachment': trans.attachment, 'date': trans.creation_date.strftime('%d/%m/%Y')} for trans in expenses]
    income_details = [
        {'description': trans.description, 'amount': trans.amount, 'approval_status': trans.approval_status.name,
         'attachment': trans.attachment, 'date': trans.creation_date.strftime('%d/%m/%Y'), 'employee_id': salesman_employee_id, 'username': Employee.query.get(salesman_employee_id).user.username} for trans in incomes]
    withdrawal_details = [
        {'description': trans.description, 'amount': trans.amount, 'approval_status': trans.approval_status.name,
         'attachment': trans.attachment, 'date': trans.creation_date.strftime('%d/%m/%Y'), 'employee_id': salesman_employee_id, 'username': Employee.query.get(salesman_employee_id).user.username} for trans in withdrawals]
    
    return expense_details, income_details, withdrawal_details

@safe_cache(timeout=300)  # 5 minutos de caché
def get_salesman_collected_clients(salesman_employee_id, current_date):
    """Obtiene el número de clientes recaudados hoy"""
    # Clientes recaudados cerrados
    total_clients_collected_close = sum(
        1 for client in Employee.query.get(salesman_employee_id).clients
        for loan in client.loans
        if loan.status == False and any(
            installment.status == InstallmentStatus.PAGADA and installment.payment_date == current_date
            for installment in loan.installments
        )
    )
    
    # Clientes recaudados activos (usando subconsulta)
    client_subquery = db.session.query(Client.id).filter(
        Client.employee_id == salesman_employee_id).subquery()
    
    loan_subquery = db.session.query(Loan.id).filter(
        Loan.client_id.in_(client_subquery.select())).subquery()
    
    subquery = db.session.query(
        Loan.id
    ).join(
        LoanInstallment, LoanInstallment.loan_id == Loan.id
    ).join(
        Payment, Payment.installment_id == LoanInstallment.id
    ).filter(
        Loan.id.in_(loan_subquery.select()),
        func.date(Payment.payment_date) == current_date,
        LoanInstallment.status.in_(['PAGADA', 'ABONADA'])
    ).group_by(
        Loan.id
    ).subquery()
    
    total_clients_collected = db.session.query(
        func.count()
    ).select_from(
        subquery
    ).scalar() or 0
    
    return total_clients_collected

@safe_cache(timeout=300)  # 5 minutos de caché
def get_coordinator_expenses(coordinator_id, current_date):
    """Obtiene gastos del coordinador para el día"""
    expenses = Transaction.query.filter(
        Transaction.employee_id == coordinator_id,
        Transaction.transaction_types == 'GASTO',
        func.date(Transaction.creation_date) == current_date,
        ~Transaction.description.like('[ELIMINADA]%')
    ).all()
    
    total_expenses = sum(expense.amount for expense in expenses)
    
    expense_details = [
        {'description': trans.description, 'amount': trans.amount, 'approval_status': trans.approval_status.name,
         'attachment': trans.attachment, 'date': trans.creation_date.strftime('%d/%m/%Y')} for trans in expenses]
    
    return total_expenses, expense_details

@safe_cache(timeout=300)  # 5 minutos de caché
def get_all_salesmen_data_optimized(salesmen, current_date):
    """OPTIMIZACIÓN: Obtiene todos los datos de vendedores en consultas optimizadas"""
    if not salesmen:
        return {}
    
    # Extraer IDs de empleados
    employee_ids = [salesman[0].employee_id for salesman in salesmen]
    
    # Validar que tenemos IDs de empleados
    if not employee_ids:
        return {}
    
    # 1. Obtener todos los EmployeeRecord en una sola consulta
    employee_records = db.session.query(EmployeeRecord).filter(
        EmployeeRecord.employee_id.in_(employee_ids)
    ).order_by(EmployeeRecord.employee_id, EmployeeRecord.id.desc()).all()
    
    # Agrupar por employee_id y tomar el más reciente
    latest_records = {}
    for record in employee_records:
        if record.employee_id not in latest_records:
            latest_records[record.employee_id] = record
    
    # 2. Obtener registros del día actual
    today_records = db.session.query(EmployeeRecord).filter(
        EmployeeRecord.employee_id.in_(employee_ids),
        func.date(EmployeeRecord.creation_date) == current_date
    ).all()
    today_records_dict = {record.employee_id: record for record in today_records}
    
    # 3. Obtener todas las transacciones del día en una sola consulta
    start_of_day = datetime.combine(current_date, datetime.min.time())
    
    transactions_query = db.session.query(
        Transaction.employee_id,
        Transaction.transaction_types,
        func.sum(Transaction.amount).label('total_amount'),
        func.count(Transaction.id).label('count')
    ).filter(
        Transaction.employee_id.in_(employee_ids),
        func.date(Transaction.creation_date) == current_date,
        Transaction.approval_status == ApprovalStatus.APROBADA,
        ~Transaction.description.like('[ELIMINADA]%')
    ).group_by(
        Transaction.employee_id, Transaction.transaction_types
    ).all()
    
    # Agrupar transacciones por empleado y tipo
    transactions_by_employee = {}
    for trans in transactions_query:
        emp_id = trans.employee_id
        if emp_id not in transactions_by_employee:
            transactions_by_employee[emp_id] = {}
        transactions_by_employee[emp_id][trans.transaction_types] = {
            'amount': trans.total_amount or 0,
            'count': trans.count or 0
        }
    
    # 4. Obtener datos de clientes nuevos en una sola consulta
    new_clients_query = db.session.query(
        Client.employee_id,
        func.count(Client.id).label('new_clients_count'),
        func.sum(Loan.amount).label('new_loans_amount')
    ).join(Loan, Client.id == Loan.client_id).filter(
        Client.employee_id.in_(employee_ids),
        Client.creation_date >= start_of_day,
        Loan.is_renewal == False,
        Loan.status == True  # Solo préstamos activos
    ).group_by(Client.employee_id).all()
    
    new_clients_data = {emp_id: {'count': 0, 'amount': 0} for emp_id in employee_ids}
    for data in new_clients_query:
        new_clients_data[data.employee_id] = {
            'count': data.new_clients_count or 0,
            'amount': data.new_loans_amount or 0
        }
    
    # 5. Obtener datos de renovaciones en una sola consulta optimizada
    renewals_query = db.session.query(
        Client.employee_id,
        func.count(Loan.id).label('renewals_count'),
        func.sum(Loan.amount).label('renewals_amount')
    ).join(Loan, Client.id == Loan.client_id).filter(
        Client.employee_id.in_(employee_ids),
        Loan.is_renewal == True,
        Loan.status == True,
        Loan.approved == True,
        Loan.creation_date >= start_of_day
    ).group_by(Client.employee_id).all()
    
    renewals_data = {emp_id: {'count': 0, 'amount': 0} for emp_id in employee_ids}
    for data in renewals_query:
        renewals_data[data.employee_id] = {
            'count': data.renewals_count or 0,
            'amount': data.renewals_amount or 0
        }
    
    # 6. Obtener cobros diarios en una sola consulta optimizada
    collections_query = db.session.query(
        Client.employee_id,
        func.sum(Payment.amount).label('total_collections')
    ).join(
        Loan, Client.id == Loan.client_id
    ).join(
        LoanInstallment, Loan.id == LoanInstallment.loan_id
    ).join(
        Payment, LoanInstallment.id == Payment.installment_id
    ).filter(
        Client.employee_id.in_(employee_ids),
        func.date(Payment.payment_date) == current_date
    ).group_by(Client.employee_id).all()
    
    collections_data = {emp_id: 0 for emp_id in employee_ids}
    for data in collections_query:
        collections_data[data.employee_id] = data.total_collections or 0
    
    # 7. Obtener datos de clientes en una sola consulta (simplificado)
    clients_query = db.session.query(
        Client.employee_id,
        func.count(Client.id).label('total_clients')
    ).filter(
        Client.employee_id.in_(employee_ids)
    ).group_by(Client.employee_id).all()
    
    # 8. Obtener préstamos activos por separado para evitar problemas con case
    active_loans_query = db.session.query(
        Client.employee_id,
        func.count(Loan.id).label('active_loans')
    ).join(Loan, Client.id == Loan.client_id).filter(
        Client.employee_id.in_(employee_ids),
        Loan.status == True
    ).group_by(Client.employee_id).all()
    
    clients_data = {emp_id: {'total': 0, 'active_loans': 0} for emp_id in employee_ids}
    
    # Procesar clientes totales
    for data in clients_query:
        clients_data[data.employee_id]['total'] = data.total_clients or 0
    
    # Procesar préstamos activos
    for data in active_loans_query:
        clients_data[data.employee_id]['active_loans'] = data.active_loans or 0
    
    # Compilar todos los datos
    result = {}
    for salesman, employee, user in salesmen:
        emp_id = salesman.employee_id
        
        # Obtener valor inicial de caja de forma segura
        initial_box_value = 0
        if emp_id in latest_records:
            initial_box_value = latest_records[emp_id].closing_total
        
        # Datos básicos
        result[emp_id] = {
            'employee_id': emp_id,
            'employee': employee,
            'user': user,
            'salesman': salesman,
            'role_employee': user.role.value,
            'employee_status': employee.status,
            'salesman_name': f'{user.first_name} {user.last_name}',
            
            # Valores de caja
            'initial_box_value': initial_box_value,
            'existing_record_today': emp_id in today_records_dict,
            
            # Transacciones del día
            'daily_expenses_amount': transactions_by_employee.get(emp_id, {}).get(TransactionType.GASTO, {}).get('amount', 0),
            'daily_expenses_count': transactions_by_employee.get(emp_id, {}).get(TransactionType.GASTO, {}).get('count', 0),
            'daily_withdrawals': transactions_by_employee.get(emp_id, {}).get(TransactionType.RETIRO, {}).get('amount', 0),
            'daily_withdrawals_count': transactions_by_employee.get(emp_id, {}).get(TransactionType.RETIRO, {}).get('count', 0),
            'daily_collection': transactions_by_employee.get(emp_id, {}).get(TransactionType.INGRESO, {}).get('amount', 0),
            'daily_collection_count': transactions_by_employee.get(emp_id, {}).get(TransactionType.INGRESO, {}).get('count', 0),
            
            # Clientes nuevos
            'new_clients': new_clients_data[emp_id]['count'],
            'new_clients_loan_amount': new_clients_data[emp_id]['amount'],
            
            # Renovaciones
            'total_renewal_loans': renewals_data[emp_id]['count'],
            'total_renewal_loans_amount': renewals_data[emp_id]['amount'],
            
            # Clientes
            'total_customers': clients_data[emp_id]['active_loans'],
            'customers_in_arrears': 0,  # Se calculará por separado si es necesario
            
            # Cobros diarios
            'total_collections_today': collections_data[emp_id],
            
            # Otros datos que requieren consultas más complejas
            'total_pending_installments_amount': 0,
            'total_pending_installments_loan_close_amount': 0,
            'all_loans_paid_today': False,
            'total_clients_collected': 0,
            'expense_details': [],
            'income_details': [],
            'withdrawal_details': []
        }
    
    return result

def get_all_salesmen_additional_data_optimized(employee_ids, current_date):
    """OPTIMIZACIÓN: Obtiene todos los datos adicionales de vendedores en consultas optimizadas"""
    if not employee_ids:
        return {}
    
    # 1. Obtener datos de clientes en una sola consulta optimizada
    clients_data_query = db.session.query(
        Client.employee_id,
        func.count(func.distinct(Client.id)).label('total_customers'),
        func.count(func.distinct(
            db.case(
                (LoanInstallment.status == InstallmentStatus.MORA, Client.id),
                else_=None
            )
        )).label('customers_in_arrears')
    ).join(
        Loan, Loan.client_id == Client.id
    ).join(
        LoanInstallment, LoanInstallment.loan_id == Loan.id
    ).filter(
        Client.employee_id.in_(employee_ids),
        Loan.status == True
    ).group_by(Client.employee_id).all()
    
    clients_data = {}
    for result in clients_data_query:
        clients_data[result.employee_id] = {
            'total_customers': result.total_customers,
            'customers_in_arrears': result.customers_in_arrears
        }
    
    # 2. Obtener datos de cuotas pendientes usando la misma lógica que el código original
    # Para cada empleado, calcular manualmente como en el código original
    pending_installments_data = {}
    
    for emp_id in employee_ids:
        employee = Employee.query.get(emp_id)
        total_pending_installments_amount = 0
        total_pending_installments_loan_close_amount = 0
        
        for client in employee.clients:
            for loan in client.loans:
                # Excluir préstamos creados hoy mismo
                if loan.creation_date.date() == current_date:
                    continue
                
                if loan.status:
                    # Encuentra la primera cuota ordenada por fecha de vencimiento (igual que el original)
                    pending_installment = LoanInstallment.query.filter(
                        LoanInstallment.loan_id == loan.id
                    ).order_by(LoanInstallment.due_date.asc()).first()
                    if pending_installment:
                        total_pending_installments_amount += pending_installment.fixed_amount
                elif loan.status == False and loan.up_to_date and loan.modification_date.date() == current_date:
                    pending_installment_paid = LoanInstallment.query.filter(
                        LoanInstallment.loan_id == loan.id
                    ).order_by(LoanInstallment.due_date.asc()).first()
                    if pending_installment_paid:
                        total_pending_installments_loan_close_amount += pending_installment_paid.fixed_amount
        
        pending_installments_data[emp_id] = {
            'total_pending_amount': float(total_pending_installments_amount),
            'total_pending_loan_close_amount': float(total_pending_installments_loan_close_amount)
        }
    
    
    # 3. Verificar si todos los préstamos fueron pagados hoy en una sola consulta
    all_loans_paid_query = db.session.query(
        Loan.employee_id,
        func.count(Loan.id).label('total_loans'),
        func.count(
            db.case(
                (func.date(Payment.payment_date) == current_date, Loan.id),
                else_=None
            )
        ).label('paid_loans_today')
    ).join(
        LoanInstallment, LoanInstallment.loan_id == Loan.id
    ).join(
        Payment, Payment.installment_id == LoanInstallment.id
    ).filter(
        Loan.employee_id.in_(employee_ids),
        Loan.status == True,
        func.date(Loan.creation_date) != current_date
    ).group_by(Loan.employee_id).all()
    
    all_loans_paid_data = {}
    for result in all_loans_paid_query:
        all_loans_paid_data[result.employee_id] = result.total_loans == result.paid_loans_today
    
    # 4. Obtener clientes recaudados hoy en una sola consulta
    collected_clients_query = db.session.query(
        Loan.employee_id,
        func.count(func.distinct(Loan.id)).label('collected_clients')
    ).join(
        LoanInstallment, LoanInstallment.loan_id == Loan.id
    ).join(
        Payment, Payment.installment_id == LoanInstallment.id
    ).filter(
        Loan.employee_id.in_(employee_ids),
        func.date(Payment.payment_date) == current_date,
        LoanInstallment.status.in_(['PAGADA', 'ABONADA'])
    ).group_by(Loan.employee_id).all()
    
    collected_clients_data = {}
    for result in collected_clients_query:
        collected_clients_data[result.employee_id] = result.collected_clients
    
    # 5. Obtener detalles de transacciones en una sola consulta
    transaction_details_query = db.session.query(
        Transaction.employee_id,
        Transaction.transaction_types,
        Transaction.amount,
        Transaction.description,
        Transaction.creation_date
    ).filter(
        Transaction.employee_id.in_(employee_ids),
        func.date(Transaction.creation_date) == current_date,
        Transaction.approval_status == ApprovalStatus.APROBADA,
        ~Transaction.description.like('[ELIMINADA]%')
    ).order_by(Transaction.creation_date.desc()).all()
    
    transaction_details_data = {}
    for trans in transaction_details_query:
        emp_id = trans.employee_id
        if emp_id not in transaction_details_data:
            transaction_details_data[emp_id] = {
                'expense_details': [],
                'income_details': [],
                'withdrawal_details': []
            }
        
        detail = {
            'amount': float(trans.amount),
            'description': trans.description,
            'creation_date': trans.creation_date
        }
        
        if trans.transaction_types == TransactionType.GASTO:
            transaction_details_data[emp_id]['expense_details'].append(detail)
        elif trans.transaction_types == TransactionType.INGRESO:
            transaction_details_data[emp_id]['income_details'].append(detail)
        elif trans.transaction_types == TransactionType.RETIRO:
            transaction_details_data[emp_id]['withdrawal_details'].append(detail)
    
    # Inicializar datos por defecto
    for emp_id in employee_ids:
        if emp_id not in clients_data:
            clients_data[emp_id] = {'total_customers': 0, 'customers_in_arrears': 0}
        if emp_id not in pending_installments_data:
            pending_installments_data[emp_id] = {
                'total_pending_amount': 0,
                'total_pending_loan_close_amount': 0
            }
        if emp_id not in all_loans_paid_data:
            all_loans_paid_data[emp_id] = False
        if emp_id not in collected_clients_data:
            collected_clients_data[emp_id] = 0
        if emp_id not in transaction_details_data:
            transaction_details_data[emp_id] = {
                'expense_details': [],
                'income_details': [],
                'withdrawal_details': []
            }
    
    # Compilar todos los datos adicionales
    result = {}
    for emp_id in employee_ids:
        result[emp_id] = {
            'total_customers': clients_data[emp_id]['total_customers'],
            'customers_in_arrears': clients_data[emp_id]['customers_in_arrears'],
            'total_pending_installments_amount': pending_installments_data[emp_id]['total_pending_amount'],
            'total_pending_installments_loan_close_amount': pending_installments_data[emp_id]['total_pending_loan_close_amount'],
            'all_loans_paid_today': all_loans_paid_data[emp_id],
            'total_clients_collected': collected_clients_data[emp_id],
            'expense_details': transaction_details_data[emp_id]['expense_details'],
            'income_details': transaction_details_data[emp_id]['income_details'],
            'withdrawal_details': transaction_details_data[emp_id]['withdrawal_details']
        }
    
    return result

@safe_cache(timeout=300)  # 5 minutos de caché
def get_all_salesmen_data_optimized_history(salesmen, filter_date):
    """OPTIMIZACIÓN: Obtiene todos los datos de vendedores en consultas optimizadas para history-box"""
    if not salesmen:
        return {}
    
    # Extraer IDs de empleados
    employee_ids = [salesman[0].employee_id for salesman in salesmen]
    
    # Validar que tenemos IDs de empleados
    if not employee_ids:
        return {}
    
    # Si es el día actual, usar la misma lógica que get_all_salesmen_data_optimized
    current_date = datetime.now().date()
    is_current_day = filter_date == current_date
    
    if is_current_day:
        # 1. Obtener todos los EmployeeRecord en una sola consulta (último de cualquier día)
        employee_records = db.session.query(EmployeeRecord).filter(
            EmployeeRecord.employee_id.in_(employee_ids)
        ).order_by(EmployeeRecord.employee_id, EmployeeRecord.id.desc()).all()
        
        # Agrupar por employee_id y tomar el más reciente
        latest_records = {}
        for record in employee_records:
            if record.employee_id not in latest_records:
                latest_records[record.employee_id] = record
        
        # 2. Obtener registros del día actual
        today_records = db.session.query(EmployeeRecord).filter(
            EmployeeRecord.employee_id.in_(employee_ids),
            func.date(EmployeeRecord.creation_date) == current_date
        ).all()
        today_records_dict = {record.employee_id: record for record in today_records}
        
        # Inicializar variables para fechas históricas (no se usan en día actual)
        filter_date_records_dict = {}
        last_records_before_dict = {}
    else:
        # Para fechas históricas, usar la lógica original
        latest_records = {}
        today_records_dict = {}
        
        # 1. Obtener EmployeeRecord para la fecha filtrada específica
        filter_date_records = db.session.query(EmployeeRecord).filter(
            EmployeeRecord.employee_id.in_(employee_ids),
            func.date(EmployeeRecord.creation_date) == filter_date
        ).order_by(EmployeeRecord.employee_id, EmployeeRecord.id.desc()).all()
        
        filter_date_records_dict = {}
        for record in filter_date_records:
            # Tomar el más reciente para cada empleado
            if record.employee_id not in filter_date_records_dict:
                filter_date_records_dict[record.employee_id] = record
        
        # 1b. Para fechas históricas, buscar último registro anterior a la fecha filtrada
        last_records_before = db.session.query(EmployeeRecord).filter(
            EmployeeRecord.employee_id.in_(employee_ids),
            func.date(EmployeeRecord.creation_date) < filter_date
        ).order_by(EmployeeRecord.employee_id, EmployeeRecord.creation_date.desc()).all()
        
        last_records_before_dict = {}
        for record in last_records_before:
            if record.employee_id not in last_records_before_dict:
                last_records_before_dict[record.employee_id] = record
    
    # 2. Obtener todas las transacciones del día filtrado en una sola consulta
    transactions_query = db.session.query(
        Transaction.employee_id,
        Transaction.transaction_types,
        func.sum(Transaction.amount).label('total_amount'),
        func.count(Transaction.id).label('count')
    ).filter(
        Transaction.employee_id.in_(employee_ids),
        func.date(Transaction.creation_date) == filter_date,
        Transaction.approval_status == ApprovalStatus.APROBADA
    ).group_by(
        Transaction.employee_id, Transaction.transaction_types
    ).all()
    
    # Agrupar transacciones por empleado y tipo
    transactions_by_employee = {}
    for trans in transactions_query:
        emp_id = trans.employee_id
        if emp_id not in transactions_by_employee:
            transactions_by_employee[emp_id] = {}
        transactions_by_employee[emp_id][trans.transaction_types] = {
            'amount': trans.total_amount or 0,
            'count': trans.count or 0
        }
    
    # 3. Obtener datos de clientes nuevos en una sola consulta para la fecha filtrada
    new_clients_query = db.session.query(
        Client.employee_id,
        func.count(Client.id).label('new_clients_count'),
        func.sum(Loan.amount).label('new_loans_amount')
    ).join(Loan, Client.id == Loan.client_id).filter(
        Client.employee_id.in_(employee_ids),
        func.date(Client.creation_date) == filter_date,
        Loan.is_renewal == False,
        Loan.status == True  # Solo préstamos activos
    ).group_by(Client.employee_id).all()
    
    new_clients_data = {emp_id: {'count': 0, 'amount': 0} for emp_id in employee_ids}
    for data in new_clients_query:
        new_clients_data[data.employee_id] = {
            'count': data.new_clients_count or 0,
            'amount': data.new_loans_amount or 0
        }
    
    # 4. Obtener datos de renovaciones en una sola consulta optimizada para la fecha filtrada
    renewals_query = db.session.query(
        Client.employee_id,
        func.count(Loan.id).label('renewals_count'),
        func.sum(Loan.amount).label('renewals_amount')
    ).join(Loan, Client.id == Loan.client_id).filter(
        Client.employee_id.in_(employee_ids),
        Loan.is_renewal == True,
        Loan.status == True,
        Loan.approved == True,
        func.date(Loan.creation_date) == filter_date
    ).group_by(Client.employee_id).all()
    
    renewals_data = {emp_id: {'count': 0, 'amount': 0} for emp_id in employee_ids}
    for data in renewals_query:
        renewals_data[data.employee_id] = {
            'count': data.renewals_count or 0,
            'amount': data.renewals_amount or 0
        }
    
    # 5. Obtener cobros diarios en una sola consulta optimizada para la fecha filtrada
    collections_query = db.session.query(
        Client.employee_id,
        func.sum(Payment.amount).label('total_collections'),
        func.count(Payment.id).label('collections_count')
    ).join(
        Loan, Client.id == Loan.client_id
    ).join(
        LoanInstallment, Loan.id == LoanInstallment.loan_id
    ).join(
        Payment, LoanInstallment.id == Payment.installment_id
    ).filter(
        Client.employee_id.in_(employee_ids),
        func.date(Payment.payment_date) == filter_date
    ).group_by(Client.employee_id).all()
    
    collections_data = {emp_id: {'total': 0, 'count': 0} for emp_id in employee_ids}
    for data in collections_query:
        collections_data[data.employee_id] = {
            'total': data.total_collections or 0,
            'count': data.collections_count or 0
        }
    
    # Compilar todos los datos
    result = {}
    for salesman, employee, user in salesmen:
        emp_id = salesman.employee_id
        
        # Obtener valor inicial de caja según el tipo de fecha
        initial_box_value = 0
        if is_current_day:
            # Para día actual, usar la misma lógica que box
            if emp_id in latest_records:
                initial_box_value = latest_records[emp_id].closing_total
        else:
            # Para fechas históricas
            if emp_id in filter_date_records_dict:
                # Si existe registro del día, usar su initial_state (valor inicial guardado)
                initial_box_value = float(filter_date_records_dict[emp_id].initial_state)
            elif emp_id in last_records_before_dict:
                # Si no hay registro del día, usar closing_total del último día anterior
                initial_box_value = float(last_records_before_dict[emp_id].closing_total)
            else:
                # Como último recurso, usar employee.box_value
                initial_box_value = float(employee.box_value)
        
        # Datos básicos
        result[emp_id] = {
            'employee_id': emp_id,
            'employee': employee,
            'user': user,
            'salesman': salesman,
            'role_employee': user.role.value,
            'employee_status': employee.status,
            'salesman_name': f'{user.first_name} {user.last_name}',
            
            # Valores de caja
            'initial_box_value': initial_box_value,
            'existing_record_today': (emp_id in today_records_dict) if is_current_day else (emp_id in filter_date_records_dict),
            
            # Transacciones del día filtrado
            'daily_expenses_amount': transactions_by_employee.get(emp_id, {}).get(TransactionType.GASTO, {}).get('amount', 0),
            'daily_expenses_count': transactions_by_employee.get(emp_id, {}).get(TransactionType.GASTO, {}).get('count', 0),
            'daily_withdrawals': transactions_by_employee.get(emp_id, {}).get(TransactionType.RETIRO, {}).get('amount', 0),
            'daily_withdrawals_count': transactions_by_employee.get(emp_id, {}).get(TransactionType.RETIRO, {}).get('count', 0),
            'daily_collection': transactions_by_employee.get(emp_id, {}).get(TransactionType.INGRESO, {}).get('amount', 0),
            'daily_collection_count': transactions_by_employee.get(emp_id, {}).get(TransactionType.INGRESO, {}).get('count', 0),
            
            # Clientes nuevos
            'new_clients': new_clients_data[emp_id]['count'],
            'new_clients_loan_amount': new_clients_data[emp_id]['amount'],
            
            # Renovaciones
            'total_renewal_loans': renewals_data[emp_id]['count'],
            'total_renewal_loans_amount': renewals_data[emp_id]['amount'],
            
            # Cobros diarios
            'total_collections_today': collections_data[emp_id]['total'],
            'daily_collections_count': collections_data[emp_id]['count'],
            
            # Otros datos que requieren consultas más complejas
            'total_pending_installments_amount': 0,
            'all_loans_paid_today': False,
            'total_customers': 0,
            'customers_in_arrears': 0,
            'expense_details': [],
            'income_details': [],
            'withdrawal_details': []
        }
    
    return result

def get_all_salesmen_additional_data_optimized_history(employee_ids, filter_date):
    """OPTIMIZACIÓN: Obtiene todos los datos adicionales de vendedores en consultas optimizadas para history-box"""
    if not employee_ids:
        return {}
    
    # 1. Obtener EmployeeRecord para la fecha filtrada (para usar due_to_charge)
    employee_records = db.session.query(EmployeeRecord).filter(
        EmployeeRecord.employee_id.in_(employee_ids),
        func.date(EmployeeRecord.creation_date) == filter_date
    ).order_by(EmployeeRecord.employee_id, EmployeeRecord.id.desc()).all()
    
    employee_records_dict = {}
    for record in employee_records:
        if record.employee_id not in employee_records_dict:
            employee_records_dict[record.employee_id] = record
    
    # 2. Obtener datos de cuotas pendientes
    # Primero intentar usar EmployeeRecord.due_to_charge si existe, sino calcular manualmente
    pending_installments_data = {}
    
    for emp_id in employee_ids:
        total_pending_installments_amount = 0
        
        if emp_id in employee_records_dict and employee_records_dict[emp_id].due_to_charge:
            # Usar due_to_charge del EmployeeRecord si existe
            total_pending_installments_amount = float(employee_records_dict[emp_id].due_to_charge)
        else:
            # Si no existe EmployeeRecord, calcular las cuotas pendientes manualmente
            employee = Employee.query.get(emp_id)
            for client in employee.clients:
                for loan in client.loans:
                    if loan.status:
                        pending_installment = LoanInstallment.query.filter(
                            LoanInstallment.loan_id == loan.id,
                            func.date(LoanInstallment.due_date) == filter_date,
                        ).order_by(LoanInstallment.due_date.asc()).first()
                        if pending_installment:
                            total_pending_installments_amount += pending_installment.fixed_amount
        
        pending_installments_data[emp_id] = {
            'total_pending_amount': float(total_pending_installments_amount)
        }
    
    # 3. Verificar si todos los préstamos fueron pagados en la fecha filtrada
    all_loans_paid_query = db.session.query(
        Loan.employee_id,
        func.count(func.distinct(Loan.id)).label('total_loans'),
        func.count(func.distinct(
            db.case(
                (func.date(Payment.payment_date) == filter_date, Loan.id),
                else_=None
            )
        )).label('paid_loans_date')
    ).join(
        LoanInstallment, LoanInstallment.loan_id == Loan.id
    ).join(
        Payment, Payment.installment_id == LoanInstallment.id
    ).filter(
        Loan.employee_id.in_(employee_ids),
        Loan.status == True
    ).group_by(Loan.employee_id).all()
    
    # Obtener loans_to_collect (préstamos a cobrar)
    loans_to_collect_query = db.session.query(
        Loan.employee_id,
        func.count(func.distinct(Loan.id)).label('loans_to_collect')
    ).filter(
        Loan.employee_id.in_(employee_ids),
        Loan.status == True
    ).group_by(Loan.employee_id).all()
    
    loans_to_collect_data = {emp_id: 0 for emp_id in employee_ids}
    for result in loans_to_collect_query:
        loans_to_collect_data[result.employee_id] = result.loans_to_collect
    
    all_loans_paid_data = {}
    for result in all_loans_paid_query:
        loans_to_collect = loans_to_collect_data.get(result.employee_id, 0)
        all_loans_paid_data[result.employee_id] = loans_to_collect == result.paid_loans_date and loans_to_collect > 0
    
    # 4. Obtener datos de clientes totales (activos)
    total_customers_query = db.session.query(
        Client.employee_id,
        func.count(func.distinct(Loan.id)).label('total_customers')
    ).join(
        Loan, Loan.client_id == Client.id
    ).filter(
        Client.employee_id.in_(employee_ids),
        Loan.status == True
    ).group_by(Client.employee_id).all()
    
    total_customers_data = {emp_id: 0 for emp_id in employee_ids}
    for result in total_customers_query:
        total_customers_data[result.employee_id] = result.total_customers
    
    # 5. Obtener clientes en mora para la fecha filtrada (lógica específica de history_box)
    # Clientes con pagos en MORA en la fecha filtrada
    customers_in_arrears_query = db.session.query(
        Client.employee_id,
        func.count(func.distinct(Client.id)).label('customers_in_arrears')
    ).join(
        Loan, Loan.client_id == Client.id
    ).join(
        LoanInstallment, LoanInstallment.loan_id == Loan.id
    ).join(
        Payment, Payment.installment_id == LoanInstallment.id
    ).filter(
        Client.employee_id.in_(employee_ids),
        Loan.status == True,
        LoanInstallment.status == InstallmentStatus.MORA,
        func.date(Payment.payment_date) == filter_date
    ).group_by(Client.employee_id).all()
    
    customers_in_arrears_data = {emp_id: 0 for emp_id in employee_ids}
    for result in customers_in_arrears_query:
        customers_in_arrears_data[result.employee_id] = result.customers_in_arrears
    
    # 6. Obtener detalles de transacciones en una sola consulta para la fecha filtrada
    transaction_details_query = db.session.query(
        Transaction.employee_id,
        Transaction.transaction_types,
        Transaction.amount,
        Transaction.description,
        Transaction.creation_date,
        Transaction.approval_status,
        Transaction.attachment
    ).filter(
        Transaction.employee_id.in_(employee_ids),
        func.date(Transaction.creation_date) == filter_date
    ).order_by(Transaction.creation_date.desc()).all()
    
    transaction_details_data = {}
    for trans in transaction_details_query:
        emp_id = trans.employee_id
        if emp_id not in transaction_details_data:
            transaction_details_data[emp_id] = {
                'expense_details': [],
                'income_details': [],
                'withdrawal_details': []
            }
        
        # Obtener employee para username
        employee = Employee.query.get(emp_id)
        
        detail = {
            'description': trans.description,
            'amount': trans.amount,
            'approval_status': trans.approval_status.name,
            'attachment': trans.attachment,
            'date': trans.creation_date.strftime('%d/%m/%Y'),
            'employee_id': emp_id,
            'username': employee.user.username if employee else ''
        }
        
        if trans.transaction_types == TransactionType.GASTO and trans.approval_status == ApprovalStatus.APROBADA:
            transaction_details_data[emp_id]['expense_details'].append(detail)
        elif trans.transaction_types == TransactionType.INGRESO and trans.approval_status == ApprovalStatus.APROBADA:
            transaction_details_data[emp_id]['income_details'].append(detail)
        elif trans.transaction_types == TransactionType.RETIRO and trans.approval_status == ApprovalStatus.APROBADA:
            transaction_details_data[emp_id]['withdrawal_details'].append(detail)
    
    # Inicializar datos por defecto
    for emp_id in employee_ids:
        if emp_id not in pending_installments_data:
            pending_installments_data[emp_id] = {'total_pending_amount': 0}
        if emp_id not in all_loans_paid_data:
            all_loans_paid_data[emp_id] = False
        if emp_id not in total_customers_data:
            total_customers_data[emp_id] = 0
        if emp_id not in customers_in_arrears_data:
            customers_in_arrears_data[emp_id] = 0
        if emp_id not in transaction_details_data:
            transaction_details_data[emp_id] = {
                'expense_details': [],
                'income_details': [],
                'withdrawal_details': []
            }
    
    # Compilar todos los datos adicionales
    result = {}
    for emp_id in employee_ids:
        result[emp_id] = {
            'total_customers': total_customers_data[emp_id],
            'customers_in_arrears': customers_in_arrears_data[emp_id],
            'total_pending_installments_amount': pending_installments_data[emp_id]['total_pending_amount'],
            'all_loans_paid_today': all_loans_paid_data[emp_id],
            'expense_details': transaction_details_data[emp_id]['expense_details'],
            'income_details': transaction_details_data[emp_id]['income_details'],
            'withdrawal_details': transaction_details_data[emp_id]['withdrawal_details']
        }
    
    return result

def calculate_daily_transaction_totals_history(manager_id, filter_date, coordinator_id=None):
    """Calcula los totales de transacciones diarias para el coordinador en history-box"""
    start_of_day = datetime.combine(filter_date, datetime.min.time())
    end_of_day = datetime.combine(filter_date, datetime.max.time())
    
    # Total de retiros aprobados (RETIROS del coordinador = INGRESO de subordinados + RETIRO del coordinador)
    # Primero: INGRESO de subordinados (retiros del coordinador)
    total_outbound_from_subordinates = db.session.query(
        func.sum(Transaction.amount).label('total_amount')
    ).join(Salesman, Transaction.employee_id == Salesman.employee_id).filter(
        Transaction.transaction_types == 'INGRESO',
        Transaction.approval_status == 'APROBADA',
        Salesman.manager_id == manager_id,
        func.date(Transaction.creation_date) == filter_date,
        ~Transaction.description.like('[ELIMINADA]%')
    ).scalar() or 0
    
    # Segundo: RETIRO directo del coordinador (si existe)
    total_outbound_from_coordinator = 0
    if coordinator_id:
        total_outbound_from_coordinator = db.session.query(
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            Transaction.employee_id == coordinator_id,
            Transaction.transaction_types == 'RETIRO',
            Transaction.approval_status == 'APROBADA',
            func.date(Transaction.creation_date) == filter_date,
            ~Transaction.description.like('[ELIMINADA]%')
        ).scalar() or 0
    
    total_outbound_amount = float(total_outbound_from_subordinates) + float(total_outbound_from_coordinator)
    
    # Total de ingresos aprobados (INGRESOS del coordinador = RETIRO de subordinados + INGRESO del coordinador)
    # Primero: RETIRO de subordinados (ingresos del coordinador)
    total_inbound_from_subordinates = db.session.query(
        func.sum(Transaction.amount).label('total_amount')
    ).join(Salesman, Transaction.employee_id == Salesman.employee_id).filter(
        Transaction.transaction_types == 'RETIRO',
        Transaction.approval_status == 'APROBADA',
        Salesman.manager_id == manager_id,
        func.date(Transaction.creation_date) == filter_date,
        ~Transaction.description.like('[ELIMINADA]%')
    ).scalar() or 0
    
    # Segundo: INGRESO directo del coordinador (si existe)
    total_inbound_from_coordinator = 0
    if coordinator_id:
        total_inbound_from_coordinator = db.session.query(
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            Transaction.employee_id == coordinator_id,
            Transaction.transaction_types == 'INGRESO',
            Transaction.approval_status == 'APROBADA',
            func.date(Transaction.creation_date) == filter_date,
            ~Transaction.description.like('[ELIMINADA]%')
        ).scalar() or 0
    
    total_inbound_amount = float(total_inbound_from_subordinates) + float(total_inbound_from_coordinator)
    
    return total_outbound_amount, total_inbound_amount

@routes.route('/box', methods=['GET'])
def box():
    try:
        # Validar acceso del coordinador
        user_id, user = validate_coordinator_access()
        
        # Obtener datos del coordinador y sus vendedores
        coordinator, coordinator_cash, coordinator_name, manager_id, salesmen = get_coordinator_data(user_id)
        
        current_date = datetime.now().date()
        
        # Calcular totales de transacciones del coordinador (incluyendo transacciones directas del coordinador)
        total_outbound_amount, total_inbound_amount = calculate_daily_transaction_totals(manager_id, current_date, coordinator.id)
        
        # Inicializar lista para estadísticas de vendedores
        salesmen_stats = []
        
        # OPTIMIZACIÓN: Obtener todos los datos de vendedores en consultas optimizadas
        salesmen_data = get_all_salesmen_data_optimized(salesmen, current_date)
        
        # OPTIMIZACIÓN: Obtener datos adicionales en una sola consulta para todos los vendedores
        employee_ids = [salesman[0].employee_id for salesman in salesmen]
        additional_data = get_all_salesmen_additional_data_optimized(employee_ids, current_date)
        
        
        # Procesar cada vendedor con datos pre-cargados
        for salesman, employee, user in salesmen:
            employee_id = salesman.employee_id
            data = salesmen_data[employee_id]
            additional = additional_data[employee_id]
            
            # Actualizar datos con información adicional optimizada
            data.update(additional)
            
            # Verificar si es un subcoordinador (Manager)
            is_subcoordinator = Manager.query.filter_by(employee_id=employee_id).first()
            
            # Inicializar variables para valores de coordinador
            daily_withdrawals = data['daily_withdrawals']
            daily_withdrawals_count = data['daily_withdrawals_count']
            daily_collections_made = data['daily_collection']
            daily_collection_count = data['daily_collection_count']
            daily_expenses_amount = data['daily_expenses_amount']
            daily_expenses_count = data['daily_expenses_count']
            
            if is_subcoordinator:
                # Es un subcoordinador: usar fórmula de coordinador
                subcoord_manager_id = db.session.query(Manager.id).filter_by(employee_id=employee_id).scalar()
                if subcoord_manager_id:
                    # Calcular totales de transacciones del subcoordinador (incluyendo transacciones directas del subcoordinador)
                    subcoord_outbound, subcoord_inbound = calculate_daily_transaction_totals(subcoord_manager_id, current_date, employee_id)
                    # Obtener gastos del subcoordinador
                    subcoord_expenses, subcoord_expense_details = get_coordinator_expenses(employee_id, current_date)
                    
                    # Usar valores de coordinador para mostrar en la card
                    daily_withdrawals = float(subcoord_outbound)  # Retiros = transacciones INGRESO de subordinados
                    daily_collections_made = float(subcoord_inbound)  # Ingresos = transacciones RETIRO de subordinados
                    daily_expenses_amount = float(subcoord_expenses)
                    
                    # Contar transacciones para mostrar en la card
                    start_of_day = datetime.combine(current_date, datetime.min.time())
                    end_of_day = datetime.combine(current_date, datetime.max.time())
                    
                    # Contar retiros (transacciones INGRESO de subordinados)
                    daily_withdrawals_count = db.session.query(
                        func.count(Transaction.id)
                    ).join(Salesman, Transaction.employee_id == Salesman.employee_id).filter(
                        Transaction.transaction_types == 'INGRESO',
                        Transaction.approval_status == 'APROBADA',
                        Salesman.manager_id == subcoord_manager_id,
                        Transaction.creation_date.between(start_of_day, end_of_day)
                    ).scalar() or 0
                    
                    # Contar ingresos (transacciones RETIRO de subordinados)
                    daily_collection_count = db.session.query(
                        func.count(Transaction.id)
                    ).join(Salesman, Transaction.employee_id == Salesman.employee_id).filter(
                        Transaction.transaction_types == 'RETIRO',
                        Transaction.approval_status == 'APROBADA',
                        Salesman.manager_id == subcoord_manager_id,
                        func.date(Transaction.creation_date) == current_date
                    ).scalar() or 0
                    
                    # Contar gastos
                    daily_expenses_count = len(subcoord_expense_details)
                    
                    # Calcular valor de caja usando fórmula de coordinador
                    box_value = float(employee.box_value) + float(subcoord_inbound) - float(subcoord_outbound) - float(subcoord_expenses)
                else:
                    # Si no se encuentra manager_id, usar fórmula de vendedor como fallback
                    box_value = calculate_box_value(
                        data['initial_box_value'], data['total_collections_today'], 
                        data['daily_withdrawals'], data['daily_expenses_amount'],
                        data['daily_collection'], data['new_clients_loan_amount'],
                        data['total_renewal_loans_amount'], data['existing_record_today']
                    )
            else:
                # Es un vendedor regular: usar fórmula de vendedor
                box_value = calculate_box_value(
                    data['initial_box_value'], data['total_collections_today'], 
                    data['daily_withdrawals'], data['daily_expenses_amount'],
                    data['daily_collection'], data['new_clients_loan_amount'],
                    data['total_renewal_loans_amount'], data['existing_record_today']
                )
            
            # Determinar estado de la caja
            if data['employee_status'] == False and data['all_loans_paid_today'] == True:
                status_box = "Cerrada"
            elif data['employee_status'] == False and data['all_loans_paid_today'] == False:
                status_box = "Desactivada"
            elif data['employee_status'] == True and data['all_loans_paid_today'] == False:
                status_box = "Activa"
            else:
                status_box = "Activa"
            
            # Crear datos del vendedor
            salesman_data = {
                'salesman_name': data['salesman_name'],
                'employee_id': employee_id,
                'employee_status': data['employee_status'],
                'total_collections_today': data['total_collections_today'],
                'new_clients': data['new_clients'],
                'daily_expenses': daily_expenses_count,
                'daily_expenses_amount': daily_expenses_amount,
                'daily_withdrawals': daily_withdrawals,
                'daily_collections_made': daily_collections_made,
                'total_number_of_customers': data['total_customers'],
                'customers_in_arrears_for_the_day': data['customers_in_arrears'],
                'total_renewal_loans': data['total_renewal_loans'],
                'total_new_clients_loan_amount': data['new_clients_loan_amount'],
                'total_renewal_loans_amount': data['total_renewal_loans_amount'],
                'daily_withdrawals_count': daily_withdrawals_count,
                'daily_collection_count': daily_collection_count,
                'total_pending_installments_amount': data['total_pending_installments_amount'],
                'all_loans_paid_today': data['all_loans_paid_today'],
                'total_clients_collected': data['total_clients_collected'],
                'status_box': status_box,
                'box_value': box_value,
                'initial_box_value': data['initial_box_value'],
                'expense_details': data['expense_details'],
                'income_details': data['income_details'],
                'withdrawal_details': data['withdrawal_details'],
                'role_employee': data['role_employee'],
                'total_pending_installments_loan_close_amount': data['total_pending_installments_loan_close_amount']
            }
            
            salesmen_stats.append(salesman_data)
        
        # Procesar búsqueda
        search_term = request.args.get('salesman_name', '')
        if search_term:
            salesmen_stats = [salesman for salesman in salesmen_stats if
                              search_term.lower() in salesman['salesman_name'].lower()]
        
        # Verificar si todas las cajas están cerradas
        all_boxes_closed = all(
            salesman_data['status_box'] == 'Cerrada' for salesman_data in salesmen_stats)
        
        # Obtener gastos del coordinador
        total_expenses, coordinator_expense_details = get_coordinator_expenses(coordinator.id, current_date)
        
        # Crear datos de la caja del coordinador
        coordinator_box = {
            'maximum_cash': float(coordinator_cash),
            'total_outbound_amount': float(total_outbound_amount),
            'total_inbound_amount': float(total_inbound_amount),
            'final_box_value': float(coordinator_cash) + float(total_inbound_amount) - 
                             float(total_outbound_amount) - float(total_expenses),
        }
        
        # Renderizar la plantilla
        return render_template('box.html', 
                             coordinator_box=coordinator_box, 
                             salesmen_stats=salesmen_stats,
                             search_term=search_term, 
                             all_boxes_closed=all_boxes_closed,
                             coordinator_name=coordinator_name, 
                             coordinator_id=coordinator.id,
                             user_id=user_id, 
                             expense_details=coordinator_expense_details, 
                             total_expenses=total_expenses)
                             
    except ValueError as e:
        return jsonify({'message': str(e)}), 401 if 'Usuario no encontrado' in str(e) else 403
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

        # Calcular totales de transacciones del sub-administrador (incluyendo transacciones directas)
        current_date = datetime.now().date()
        total_outbound_amount, total_inbound_amount = calculate_daily_transaction_totals(manager_id, current_date, sub_admin_employee.id)

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
                Loan.is_renewal == False,  # Excluir renovaciones
                Loan.status == True  # Solo préstamos activos
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
            transactions = Transaction.query.filter(
                Transaction.employee_id == employee_id,
                ~Transaction.description.like('[ELIMINADA]%')
            ).order_by(Transaction.creation_date.desc()).all()

            # Filtrar transacciones por tipo y fecha
            today = datetime.today().date()
            expenses = [trans for trans in transactions if
                        trans.transaction_types == TransactionType.GASTO and trans.approval_status == ApprovalStatus.APROBADA and trans.creation_date.date() == today]
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

        # Función auxiliar para procesar transacciones
        def procesar_transaccion(transaccion, empleado_vendedor, es_coordinador=False):
            try:
                # Obtener el concepto de la transacción
                concepto = Concept.query.get(transaccion.concept_id)

                # Crear un diccionario con los detalles de la transacción pendiente, incluyendo el nombre del vendedor
                # Manejo seguro de nombres - usar getattr para evitar AttributeError
                first_name = getattr(empleado_vendedor.user, 'first_name', '') or ''
                last_name = getattr(empleado_vendedor.user, 'last_name', '') or ''
                vendedor_name = f"{first_name} {last_name}".strip()
                
                # Manejo seguro de concepto - verificar si existe
                concepto_name = getattr(concepto, 'name', 'Sin concepto') if concepto else 'Sin concepto'
                
                # Manejo seguro de transaction_types - verificar si existe
                tipo_name = getattr(transaccion.transaction_types, 'name', 'Sin tipo') if transaccion.transaction_types else 'Sin tipo'
                
                # Manejo seguro de attachment - verificar si existe y no es None
                attachment_name = transaccion.attachment if transaccion.attachment else ''

                detalle_transaccion = {
                    'id': transaccion.id,
                    'tipo': tipo_name,
                    'concepto': concepto_name,
                    'descripcion': transaccion.description or '',
                    'monto': transaccion.amount,
                    'attachment': attachment_name,
                    'vendedor': vendedor_name,
                    'es_coordinador': es_coordinador
                }

                # Agregar los detalles a la lista
                detalles_transacciones.append(detalle_transaccion)
                
            except Exception as e:
                # Si hay un error con una transacción específica, continuar con las demás
                return

        # 1. Obtener transacciones pendientes del coordinador
        query_coordinador = db.session.query(Transaction, Employee).join(Employee).filter(
            Transaction.employee_id == empleado.id,
            Transaction.approval_status == ApprovalStatus.PENDIENTE
        )

        for transaccion, empleado_coordinador in query_coordinador:
            procesar_transaccion(transaccion, empleado_coordinador, es_coordinador=True)

        # 2. Obtener transacciones de vendedores usando JOIN con Salesman
        query_vendedores = db.session.query(Transaction, Employee).join(
            Employee, Transaction.employee_id == Employee.id
        ).join(
            Salesman, Salesman.employee_id == Employee.id
        ).filter(
            Salesman.manager_id == empleado.manager.id,
            Transaction.approval_status == ApprovalStatus.PENDIENTE
        )

        for transaccion, empleado_vendedor in query_vendedores:
            procesar_transaccion(transaccion, empleado_vendedor, es_coordinador=False)

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

        # Obtener el empleado asociado al user_id (optimización: una sola consulta)
        employee = Employee.query.filter_by(user_id=user_id).first()
        
        # Validar que el empleado existe
        if not employee:
            return "Empleado no encontrado", 404

        transaction_type = ''  # Definir transaction_type por defecto
        concepts = []  # Definir concepts por defecto

        if request.method == 'POST':
            try:
                # Manejar la creación de la transacción
                transaction_type = request.form.get('transaction_type')
                concept_id = request.form.get('concept_id')
                description = request.form.get('description')
                amount = request.form.get('quantity')

                # Validar campos requeridos
                if not all([transaction_type, concept_id, description, amount]):
                    return "Faltan campos requeridos. Por favor, complete todos los campos.", 400

                # Validar que el monto sea un número válido
                try:
                    amount_decimal = Decimal(amount)
                    if amount_decimal <= 0:
                        return "El monto debe ser mayor a cero", 400
                except (ValueError, TypeError):
                    return "El monto debe ser un número válido", 400

                # Validar que el concepto existe
                concept = Concept.query.get(concept_id)
                if not concept:
                    return "El concepto seleccionado no existe", 400

                # Determinar estado de aprobación según el tipo de transacción
                if transaction_type != 'GASTO':
                    approval_status = "APROBADA"
                else:
                    approval_status = request.form.get('status', 'PENDIENTE')

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
                        print(f"Error al guardar archivo: {e}")
                        print(f"Upload folder: {upload_folder}")
                        print(f"Filename: {filename}")
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

                # Crear la transacción usando el employee_id correcto
                transaction = Transaction(
                    transaction_types=transaction_type,
                    concept_id=concept_id,
                    description=description,
                    amount=amount_decimal,
                    attachment=filename,  # Usar el nombre único del archivo
                    approval_status=approval_status,
                    employee_id=employee.id,
                    loan_id=None,
                    creation_date=current_date
                )

                # Guardar en la base de datos con manejo de errores
                db.session.add(transaction)
                db.session.commit()

                # Redireccionar según el rol del usuario
                if user_role == 'VENDEDOR':
                    return redirect(url_for('routes.menu_salesman', user_id=user_id))
                elif user_role == 'COORDINADOR':
                    return redirect(url_for('routes.menu_manager', user_id=user_id))

            except Exception as e:
                # Rollback en caso de error
                db.session.rollback()
                print(f"Error al crear transacción: {e}")
                return f"Error interno del servidor: {str(e)}", 500

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

            # Guardar el estado anterior antes de modificarlo
            old_status = transaction.approval_status
            new_status_enum = ApprovalStatus(new_status)
            transaction.approval_status = new_status_enum

            if transaction.loan_id:
                prestamo = Loan.query.get(transaction.loan_id)
                if prestamo:
                    if new_status_enum == ApprovalStatus.APROBADA:
                        prestamo.approved = True
                        generate_loan_installments(prestamo)
                    elif new_status_enum == ApprovalStatus.RECHAZADA:
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
                """Actualiza box_value de empleado y su coordinador si existe"""
                current_employee = employee
                while current_employee:
                    if add:
                        current_employee.box_value += amount
                    else:
                        current_employee.box_value -= amount
                    db.session.add(current_employee)
                    current_employee = current_employee.manager.employee if current_employee.manager else None

            # Solo modificar box_value según la transición de estados:
            # 1. PENDIENTE → APROBADA: Aplicar cambio (primera vez)
            # 2. RECHAZADA → APROBADA: Aplicar cambio (nueva aprobación)
            # 3. APROBADA → RECHAZADA: Revertir cambio (operación inversa)
            # 4. PENDIENTE → RECHAZADA: No hacer nada (nunca afectó box_value)
            # 5. APROBADA → APROBADA: No hacer nada (ya estaba procesada)

            should_apply_change = False  # Aplicar cambio normal
            should_revert_change = False  # Revertir cambio previo

            if old_status == ApprovalStatus.PENDIENTE and new_status_enum == ApprovalStatus.APROBADA:
                # Primera aprobación: aplicar cambio
                should_apply_change = True
            elif old_status == ApprovalStatus.RECHAZADA and new_status_enum == ApprovalStatus.APROBADA:
                # Nueva aprobación después de rechazo: aplicar cambio
                should_apply_change = True
            elif old_status == ApprovalStatus.APROBADA and new_status_enum == ApprovalStatus.RECHAZADA:
                # Rechazo de transacción previamente aprobada: revertir cambio
                should_revert_change = True
            # Si PENDIENTE → RECHAZADA: no hacer nada (nunca afectó box_value)
            # Si APROBADA → APROBADA: no hacer nada (sin cambio)

            if should_apply_change or should_revert_change:
                # Determinar si se suma o resta según el tipo de transacción
                # Si se revierte, se hace la operación inversa
                if user_role.value == Role.COORDINADOR:
                    if TransactionType == TransactionType.INGRESO:
                        # INGRESO aumenta box_value del coordinador
                        update_box_value(employee, transaction.amount, add=should_apply_change)
                    elif TransactionType == TransactionType.GASTO:
                        # GASTO disminuye box_value del coordinador
                        update_box_value(employee, transaction.amount, add=should_revert_change)
                    elif TransactionType == TransactionType.RETIRO:
                        # RETIRO disminuye box_value del coordinador
                        update_box_value(employee, transaction.amount, add=should_revert_change)

                elif user_role.value == Role.VENDEDOR:
                    salesman = Salesman.query.filter_by(
                        employee_id=employee_id).first()
                    if not salesman:
                        return jsonify({'message': 'Vendedor no encontrado'}), 404
                    
                    coordinator = salesman.manager.employee
                    
                    if TransactionType == TransactionType.INGRESO:
                        # INGRESO del vendedor: aumenta su box_value, disminuye del coordinador
                        if should_apply_change:
                            employee.box_value += transaction.amount
                            update_box_value(coordinator, transaction.amount, add=False)
                        elif should_revert_change:
                            employee.box_value -= transaction.amount
                            update_box_value(coordinator, transaction.amount, add=True)
                        db.session.add(employee)
                    elif TransactionType == TransactionType.GASTO:
                        # GASTO del vendedor: disminuye su box_value
                        if should_apply_change:
                            employee.box_value -= transaction.amount
                        elif should_revert_change:
                            employee.box_value += transaction.amount
                        db.session.add(employee)
                    elif TransactionType == TransactionType.RETIRO:
                        # RETIRO del vendedor: disminuye su box_value, aumenta del coordinador
                        if should_apply_change:
                            employee.box_value -= transaction.amount
                            update_box_value(coordinator, transaction.amount, add=True)
                        elif should_revert_change:
                            employee.box_value += transaction.amount
                            update_box_value(coordinator, transaction.amount, add=False)
                        db.session.add(employee)

            db.session.commit()

        return redirect('/approval-expenses')

    except Exception as e:
        db.session.rollback()  # Revertir cambios en caso de error
        return jsonify({'message': 'Error interno del servidor', 'error': str(e)}), 500


def validate_coordinator_employee_access(coordinator_user_id, employee_id):
    """Valida que el coordinador tiene acceso al empleado (es su subordinado o es él mismo)"""
    try:
        coordinator_employee = Employee.query.filter_by(user_id=coordinator_user_id).first()
        if not coordinator_employee:
            return False, None
        
        # Si es el mismo empleado, tiene acceso
        if coordinator_employee.id == employee_id:
            return True, coordinator_employee
        
        # Obtener el manager_id del coordinador
        manager_id = db.session.query(Manager.id).filter_by(employee_id=coordinator_employee.id).scalar()
        if not manager_id:
            return False, None
        
        # Verificar si el empleado es un subordinado del coordinador
        salesman = Salesman.query.filter_by(employee_id=employee_id, manager_id=manager_id).first()
        if salesman:
            return True, coordinator_employee
        
        return False, None
    except Exception:
        return False, None


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


@routes.route('/api/transactions/<int:employee_id>/<transaction_type>', methods=['GET'])
def get_transactions_by_type(employee_id, transaction_type):
    """Obtener transacciones aprobadas por tipo y empleado"""
    try:
        # Validar usuario autenticado y coordinador
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'message': 'Usuario no autenticado'}), 401
        
        user = User.query.get(user_id)
        if not user or user.role != Role.COORDINADOR:
            return jsonify({'message': 'Acceso denegado. Solo coordinadores pueden acceder'}), 403
        
        # Validar acceso al empleado
        has_access, coordinator_employee = validate_coordinator_employee_access(user_id, employee_id)
        if not has_access:
            return jsonify({'message': 'No tiene acceso a las transacciones de este empleado'}), 403
        
        # Validar tipo de transacción
        if transaction_type not in ['GASTO', 'RETIRO', 'INGRESO']:
            return jsonify({'message': 'Tipo de transacción inválido'}), 400
        
        # Obtener transacciones aprobadas del día actual
        current_date = datetime.now().date()
        transactions = Transaction.query.filter(
            Transaction.employee_id == employee_id,
            Transaction.transaction_types == transaction_type,
            Transaction.approval_status == ApprovalStatus.APROBADA,
            func.date(Transaction.creation_date) == current_date,
            ~Transaction.description.like('[ELIMINADA]%')
        ).order_by(Transaction.creation_date.desc()).all()
        
        # Formatear respuesta
        transactions_data = []
        for trans in transactions:
            # Remover prefijo [ELIMINADA] si existe (por si acaso)
            description = trans.description
            if description.startswith('[ELIMINADA]'):
                description = description[11:].strip()
            
            transactions_data.append({
                'id': trans.id,
                'description': description,
                'amount': float(trans.amount),
                'approval_status': trans.approval_status.name,
                'creation_date': trans.creation_date.isoformat(),
                'employee_id': trans.employee_id
            })
        
        return jsonify({'transactions': transactions_data}), 200
        
    except Exception as e:
        return jsonify({'message': 'Error interno del servidor', 'error': str(e)}), 500


@routes.route('/api/transactions/<int:transaction_id>', methods=['PUT'])
def update_transaction(transaction_id):
    """Editar transacción"""
    try:
        # Validar usuario autenticado y coordinador
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'message': 'Usuario no autenticado'}), 401
        
        user = User.query.get(user_id)
        if not user or user.role != Role.COORDINADOR:
            return jsonify({'message': 'Acceso denegado. Solo coordinadores pueden editar'}), 403
        
        # Obtener la transacción
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return jsonify({'message': 'Transacción no encontrada'}), 404
        
        # Validar acceso al empleado de la transacción
        has_access, coordinator_employee = validate_coordinator_employee_access(user_id, transaction.employee_id)
        if not has_access:
            return jsonify({'message': 'No tiene acceso a esta transacción'}), 403
        
        # Validar que la transacción no esté eliminada
        if transaction.description.startswith('[ELIMINADA]'):
            return jsonify({'message': 'No se puede editar una transacción eliminada'}), 400
        
        # Obtener datos del request
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Datos no proporcionados'}), 400
        
        # Validar y actualizar monto
        if 'amount' in data:
            try:
                new_amount = Decimal(str(data['amount']))
                if new_amount <= 0:
                    return jsonify({'message': 'El monto debe ser mayor a cero'}), 400
                transaction.amount = new_amount
            except (ValueError, TypeError):
                return jsonify({'message': 'Monto inválido'}), 400
        
        # Validar y actualizar estado
        if 'approval_status' in data:
            new_status = data['approval_status']
            if new_status not in ['APROBADA', 'RECHAZADA']:
                return jsonify({'message': 'Estado inválido'}), 400
            transaction.approval_status = ApprovalStatus(new_status)
        
        # Actualizar descripción (remover prefijo [ELIMINADA] si existe)
        if 'description' in data:
            new_description = data['description'].strip()
            if new_description:
                # Si tenía prefijo [ELIMINADA], removerlo
                if transaction.description.startswith('[ELIMINADA]'):
                    transaction.description = new_description
                else:
                    transaction.description = new_description
        
        # Actualizar fecha de modificación
        transaction.modification_date = datetime.now()
        
        db.session.commit()
        
        # Preparar respuesta (remover prefijo si existe)
        description = transaction.description
        if description.startswith('[ELIMINADA]'):
            description = description[11:].strip()
        
        return jsonify({
            'message': 'Transacción actualizada exitosamente',
            'transaction': {
                'id': transaction.id,
                'description': description,
                'amount': float(transaction.amount),
                'approval_status': transaction.approval_status.name,
                'creation_date': transaction.creation_date.isoformat(),
                'employee_id': transaction.employee_id
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error interno del servidor', 'error': str(e)}), 500


@routes.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    """Eliminar transacción (soft delete)"""
    try:
        # Validar usuario autenticado y coordinador
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'message': 'Usuario no autenticado'}), 401
        
        user = User.query.get(user_id)
        if not user or user.role != Role.COORDINADOR:
            return jsonify({'message': 'Acceso denegado. Solo coordinadores pueden eliminar'}), 403
        
        # Obtener la transacción
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return jsonify({'message': 'Transacción no encontrada'}), 404
        
        # Validar acceso al empleado de la transacción
        has_access, coordinator_employee = validate_coordinator_employee_access(user_id, transaction.employee_id)
        if not has_access:
            return jsonify({'message': 'No tiene acceso a esta transacción'}), 403
        
        # Validar que la transacción no esté ya eliminada
        if transaction.description.startswith('[ELIMINADA]'):
            return jsonify({'message': 'La transacción ya está eliminada'}), 400
        
        # Soft delete: agregar prefijo [ELIMINADA] y cambiar estado a RECHAZADA
        if not transaction.description.startswith('[ELIMINADA]'):
            transaction.description = f'[ELIMINADA] {transaction.description}'
        
        transaction.approval_status = ApprovalStatus.RECHAZADA
        transaction.modification_date = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Transacción eliminada exitosamente',
            'transaction_id': transaction_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
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
    search_term = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Mostrar 20 préstamos por página
    
    # Obtener el empleado
    employee = Employee.query.filter_by(id=employee_id).first()
    if not employee:
        return jsonify({'message': 'Empleado no encontrado'}), 404

    # Construir query base con joins para optimizar
    loans_query = db.session.query(Loan).join(
        Client, Loan.client_id == Client.id
    ).join(
        Salesman, Loan.employee_id == Salesman.employee_id
    ).join(
        Employee, Salesman.employee_id == Employee.id
    ).join(
        User, Employee.user_id == User.id
    )

    # Filtrar por estado según el toggle
    if not show_all:
        loans_query = loans_query.filter(Loan.status == True)

    # Filtrar por nombre del cliente si hay búsqueda
    if search_term:
        loans_query = loans_query.filter(
            (Client.first_name.ilike(f'%{search_term}%')) |
            (Client.last_name.ilike(f'%{search_term}%'))
        )

    # Paginar los resultados
    loans_paginated = loans_query.order_by(Loan.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Inicializar variables para totales
    total_loans = 0
    total_overdue_amount = 0
    loans_detail = []

    # Procesar cada préstamo de la página actual
    for loan in loans_paginated.items:
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
            'Seller First Name': seller.employee.user.first_name if seller and seller.employee else '',
            'Seller Last Name': seller.employee.user.last_name if seller and seller.employee else '',
            'Client First Name': client.first_name if client else '',
            'Client Last Name': client.last_name if client else '',
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

    # Calcular totales de todos los préstamos (no solo la página actual)
    total_query = db.session.query(Loan).join(
        Client, Loan.client_id == Client.id
    )
    if not show_all:
        total_query = total_query.filter(Loan.status == True)
    if search_term:
        total_query = total_query.filter(
            (Client.first_name.ilike(f'%{search_term}%')) |
            (Client.last_name.ilike(f'%{search_term}%'))
        )
    all_loans = total_query.all()
    
    total_all_loans = 0
    total_all_overdue = 0
    for loan in all_loans:
        total_all_loans += 1
        for installment in loan.installments:
            if installment.status == InstallmentStatus.MORA:
                total_all_overdue += float(installment.amount)

    # Crear un diccionario con los datos solicitados
    wallet_detail_data = {
        'Total Loans': total_all_loans,
        'Total Overdue Amount': str(int(total_all_overdue)),
        'Loans Detail': loans_detail,
    }
    return render_template('wallet-detail.html', 
                         wallet_detail_data=wallet_detail_data, 
                         user_id=employee_id, 
                         show_all=show_all,
                         search=search_term,
                         pagination=loans_paginated)


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

        # OPTIMIZACIÓN: Una sola consulta con JOIN para obtener transacciones y conceptos
        # Agregar paginación para mejorar el rendimiento
        page = request.args.get('page', 1, type=int)
        per_page = 20  # Mostrar 20 transacciones por página
        
        transacciones_con_conceptos = db.session.query(Transaction, Concept).outerjoin(
            Concept, Transaction.concept_id == Concept.id
        ).filter(
            Transaction.employee_id == empleado.id,
            ~Transaction.description.like('[ELIMINADA]%')
        ).order_by(Transaction.creation_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        # Crear una lista para almacenar los detalles de las transacciones
        detalles_transacciones = []

        for transaccion, concepto in transacciones_con_conceptos.items:
            # Crear un diccionario con los detalles de la transacción
            detalle_transaccion = {
                'id': transaccion.id,
                'tipo': transaccion.transaction_types.name if transaccion.transaction_types else 'N/A',
                'concepto': concepto.name if concepto else 'N/A',
                'descripcion': transaccion.description or 'Sin descripción',
                'monto': transaccion.amount,
                'attachment': transaccion.attachment or None,
                'status': transaccion.approval_status.value if transaccion.approval_status else 'N/A',
                'fecha': transaccion.creation_date.strftime('%d/%m/%Y %H:%M') if transaccion.creation_date else 'N/A'
            }

            # Agregar los detalles a la lista
            detalles_transacciones.append(detalle_transaccion)

        return render_template('list-expenses.html', 
                             detalles_transacciones=detalles_transacciones, 
                             user_role=user_role, 
                             user_id=user_id,
                             pagination=transacciones_con_conceptos)

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
        if loan_date == datetime.today().date() and loan.is_renewal == 0 and loan.status:  # Verificar si el préstamo se realizó hoy y está activo
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
    transactions = Transaction.query.filter(
        Transaction.employee_id == employee_id,
        ~Transaction.description.like('[ELIMINADA]%')
    ).order_by(Transaction.creation_date.desc()).all()

    # Filtrar transacciones por tipo y fecha
    today = datetime.today().date()
    expenses = [trans for trans in transactions if
                trans.transaction_types == TransactionType.GASTO and trans.approval_status == ApprovalStatus.APROBADA and trans.creation_date.date() == today]
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
                            'loan_id': loan.id,
                            '_sort_time': payment_today.payment_date
                        }
                        clients_in_arrears.append(client_arrears)

    # Ordenar lista de mora por fecha de procesamiento
    clients_in_arrears.sort(key=lambda x: x['_sort_time'])

    # Obtener todos los pagos realizados hoy
    payments_today = Payment.query.join(LoanInstallment).join(Loan).join(Employee).filter(Employee.id == employee_id,
                                                                                          func.date(
                                                                                              Payment.payment_date) == today).order_by(Payment.payment_date.asc()).all()

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

    employee = Employee.query.get(employee_id)
    if employee is not None:
        # Alternar estado: 0 (cerrada) -> 1 (abierta), 1 (activa) -> 0 (cerrada)
        current_status = getattr(employee, 'status', None)
        if current_status == 0:
            employee.status = 1
        elif current_status == 1:
            employee.status = 0

    # Guardar los cambios en la base de datos
    if employee is not None:
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
            Loan.is_renewal == False,  # Excluir renovaciones
            Loan.status == True  # Solo préstamos activos
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

    # 💰 **Calcular el total de TODOS los pagos del día actual para este préstamo**
    # Usar join para capturar todos los pagos del préstamo del día, no solo los de installments_paid_today
    total_payments_to_revert = db.session.query(func.sum(Payment.amount)).join(
        LoanInstallment, Payment.installment_id == LoanInstallment.id
    ).filter(
        LoanInstallment.loan_id == loan_id,
        func.date(Payment.payment_date) == current_date
    ).scalar() or Decimal('0')

    # 🔄 **Revertir el valor anterior de la caja del empleado**
    employee.box_value -= total_payments_to_revert

    # ➕ **Agregar el nuevo valor a la caja del empleado**
    employee.box_value += Decimal(custom_payment)

    # 📅 **Capturar el timestamp original del primer pago del día**
    original_payment_timestamp = None
    if installments_paid_today:
        # Obtener el timestamp más temprano de los pagos de hoy para este préstamo
        earliest_payment = db.session.query(func.min(Payment.payment_date)).filter(
            Payment.installment_id.in_([i.id for i in installments_paid_today]),
            func.date(Payment.payment_date) == current_date
        ).scalar()
        
        if earliest_payment:
            original_payment_timestamp = earliest_payment

    for installment in installments_paid_today:
        if installment.status == InstallmentStatus.PAGADA:
            # ✅ Restaurar el monto original en cuotas pagadas completamente
            installment.amount = installment.fixed_amount
        elif installment.status == InstallmentStatus.ABONADA:
            # ✅ Restaurar el monto original en cuotas abonadas
            installment.amount = installment.fixed_amount
            
        installment.status = InstallmentStatus.PENDIENTE  # Volver a estado pendiente

    db.session.commit()

    # 🔥 **Eliminar TODOS los pagos hechos hoy para este préstamo**
    # Obtener los IDs de los pagos a eliminar
    payment_ids_to_delete = db.session.query(Payment.id).join(
        LoanInstallment, Payment.installment_id == LoanInstallment.id
    ).filter(
        LoanInstallment.loan_id == loan_id,
        func.date(Payment.payment_date) == current_date
    ).all()
    
    # Extraer los IDs de la lista de tuplas
    payment_ids = [payment_id[0] for payment_id in payment_ids_to_delete]
    
    # Eliminar los pagos usando los IDs obtenidos
    if payment_ids:
        Payment.query.filter(Payment.id.in_(payment_ids)).delete(synchronize_session=False)

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
                if installment.payment_date is None:
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
                    if installment.payment_date is None:
                        installment.payment_date = datetime.now().date()
                    installment.amount = Decimal('0')
                    
                    # Crear el pago asociado a esta cuota por el monto pendiente
                    payment = Payment(
                        amount=amount_due_for_installment, 
                        payment_date=original_payment_timestamp if original_payment_timestamp else datetime.now(), 
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
                        if installment.payment_date is None:
                            installment.payment_date = datetime.now().date()
                        installment.amount = Decimal('0')
                        
                        payment = Payment(
                            amount=amount_due_for_installment, 
                            payment_date=original_payment_timestamp if original_payment_timestamp else datetime.now(), 
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
                            payment_date=original_payment_timestamp if original_payment_timestamp else datetime.now(), 
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

        # Calcular totales de transacciones del coordinador para la fecha filtrada (incluyendo transacciones directas del coordinador)
        total_outbound_amount, total_inbound_amount = calculate_daily_transaction_totals_history(manager_id, filter_date, coordinator.id)

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

        # Construir la respuesta como variables separadas
        coordinator_box = {
            'maximum_cash': coordinator_cash,
            'total_outbound_amount': float(total_outbound_amount) if total_outbound_amount else 0,
            'total_inbound_amount': float(total_inbound_amount) if total_inbound_amount else 0,
            'total_expenses': float(total_expenses),
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





def process_salesman_record(employee_id, current_date):
    """
    Procesa el registro de cierre de caja para un vendedor.
    Retorna True si se procesó correctamente, False si ya existía registro.
    """
    # Verificar si ya existe un registro para este empleado en la fecha actual
    existing_record = EmployeeRecord.query.filter_by(employee_id=employee_id) \
        .filter(func.date(EmployeeRecord.creation_date) == current_date).first()
    
    if existing_record:
        return False
    
    employee = Employee.query.get(employee_id)
    if not employee:
        return False
    
    employee_status = employee.status

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
        .filter(func.date(EmployeeRecord.creation_date) < current_date) \
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
        Loan.is_renewal == False,  # Excluir renovaciones
        Loan.status == True  # Solo préstamos activos
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
    employee.box_value = employee_record.closing_total

    db.session.add(employee)
    db.session.add(employee_record)
    db.session.commit()
    
    return True


def process_coordinator_hierarchy(manager_id, current_date):
    """
    Procesa coordinadores recursivamente de abajo hacia arriba.
    Primero procesa todos los sub-coordinadores, luego vendedores puros, finalmente el coordinador padre.
    """
    # Obtener el Manager object para acceder a su employee_id
    manager_obj = Manager.query.get(manager_id)
    if not manager_obj:
        return
    
    # Obtener el employee_id correcto del Manager
    employee_id = manager_obj.employee_id
    if not employee_id:
        return
    
    # Verificar si ya existe un registro para este coordinador en la fecha actual
    existing_record = EmployeeRecord.query.filter_by(employee_id=employee_id) \
        .filter(func.date(EmployeeRecord.creation_date) == current_date).first()
    
    if existing_record:
        return  # Ya procesado
    
    manager_array = Employee.query.get(employee_id)
    if not manager_array:
        return

    # Obtener todos los Salesman bajo este manager
    salesmen = Salesman.query.filter_by(manager_id=manager_id).all()
    
    # Separar vendedores puros de sub-coordinadores
    pure_salesmen = []  # Solo vendedores (NO son Manager)
    sub_coordinators = []  # Salesman que también son Manager (sub-coordinadores)
    
    for salesman in salesmen:
        # Verificar si este salesman también es un manager (sub-coordinador)
        is_manager = Manager.query.filter_by(employee_id=salesman.employee_id).first()
        if is_manager:
            # Es un sub-coordinador - procesarlo PRIMERO (recursivo)
            sub_coordinators.append(salesman)
        else:
            # Es un vendedor puro
            pure_salesmen.append(salesman)
    
    # 1. Procesar primero todos los sub-coordinadores (bottom-up)
    for sub_coord_salesman in sub_coordinators:
        sub_coord_manager = Manager.query.filter_by(employee_id=sub_coord_salesman.employee_id).first()
        if sub_coord_manager:
            process_coordinator_hierarchy(sub_coord_manager.id, current_date)
    
    # 2. Luego procesar vendedores puros
    for salesman in pure_salesmen:
        process_salesman_record(salesman.employee_id, current_date)
    
    # 3. Finalmente procesar este coordinador
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
    last_record = EmployeeRecord.query.filter_by(employee_id=employee_id) \
        .filter(func.date(EmployeeRecord.creation_date) < current_date) \
        .order_by(EmployeeRecord.creation_date.desc()).first()

    # Usar el último registro como estado inicial, si existe
    if last_record:
        initial_state = float(last_record.closing_total)
    else:
        # Solo usar box_value si no hay registros previos
        initial_state = float(manager_array.box_value)

    # Obtener Gastos del Coordinador
    transaction_expenses_today = Transaction.query.filter_by(employee_id=employee_id, transaction_types=TransactionType.GASTO,
                                                             approval_status=ApprovalStatus.APROBADA).filter(func.date(Transaction.creation_date) == current_date).all()

    transaction_incomes_today = Transaction.query.filter_by(employee_id=employee_id, transaction_types=TransactionType.INGRESO,
                                                            approval_status=ApprovalStatus.APROBADA).filter(func.date(Transaction.creation_date) == current_date).all()

    transaction_withdrawals_today = Transaction.query.filter_by(employee_id=employee_id, transaction_types=TransactionType.RETIRO,
                                                                approval_status=ApprovalStatus.APROBADA).filter(func.date(Transaction.creation_date) == current_date).all()

    # Inicializar acumuladores
    total_employee_incomes_amount = 0
    total_employee_withdrawals_amount = 0

    # Obtener TODOS los subordinados (vendedores Y sub-coordinadores)
    all_subordinates = Salesman.query.filter_by(manager_id=manager_id).all()

    for subordinate in all_subordinates:
        subordinate_employee_id = subordinate.employee_id
        employee = Employee.query.get(subordinate_employee_id)
        
        if not employee:
            continue

        # Transacciones de tipo INGRESO del subordinado = RETIRO para el coordinador
        # (El subordinado recibe dinero del coordinador)
        transaction_withdrawals = Transaction.query.filter_by(employee_id=subordinate_employee_id, transaction_types=TransactionType.INGRESO,
                                                              approval_status=ApprovalStatus.APROBADA).filter(func.date(Transaction.creation_date) == current_date).all()

        # Transacciones de tipo RETIRO del subordinado = INGRESO para el coordinador
        # (El subordinado devuelve dinero al coordinador)
        transaction_incomes = Transaction.query.filter_by(employee_id=subordinate_employee_id, transaction_types=TransactionType.RETIRO,
                                                          approval_status=ApprovalStatus.APROBADA).filter(func.date(Transaction.creation_date) == current_date).all()

        # Obtener RETIROS del Coordinador = INGRESOS del subordinado
        employee_withdrawals_amount = sum(
            transaction.amount for transaction in transaction_withdrawals)

        # Obtener INGRESOS del Coordinador = RETIROS del subordinado
        employee_incomes_amount = sum(
            transaction.amount for transaction in transaction_incomes)

        # Acumular los valores
        total_employee_withdrawals_amount += float(
            employee_withdrawals_amount)
        total_employee_incomes_amount += float(employee_incomes_amount)

    # Valor total de INGRESOS Coordinador
    # Incluye transacciones INGRESO del coordinador + RETIRO de subordinados
    daily_incomes_amount = float(sum(
        transaction.amount for transaction in transaction_incomes_today)) + float(total_employee_incomes_amount)

    # Valor total de RETIROS Coordinador
    # Incluye transacciones RETIRO del coordinador + INGRESO de subordinados
    daily_withdrawals_amount = float(sum(
        transaction.amount for transaction in transaction_withdrawals_today)) + float(total_employee_withdrawals_amount)

    # Valor total de GASTOS Coordinador
    daily_expenses_amount = float(
        sum(transaction.amount for transaction in transaction_expenses_today))

    # Calcular closing_total usando la misma fórmula que la interfaz
    # Usar box_value actual como base (ya incluye transacciones del coordinador)
    # Solo sumar/restar transacciones de subordinados y gastos
    # Fórmula: box_value + inbound (subordinados) - outbound (subordinados) - expenses
    closing_total_calculated = float(manager_array.box_value) + float(total_employee_incomes_amount) - float(total_employee_withdrawals_amount) - float(daily_expenses_amount)

    employee_record = EmployeeRecord(
        employee_id=employee_id,
        initial_state=initial_state,
        incomings=daily_incomes_amount,
        expenses=daily_expenses_amount,
        withdrawals=daily_withdrawals_amount,
        closing_total=closing_total_calculated,  # Usar el valor calculado como en la interfaz
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
    manager_array.box_value = employee_record.closing_total

    db.session.add(manager_array)
    db.session.add(employee_record)
    db.session.commit()


@routes.route('/add-manager-record')
def add_manager_record():
    try:
        users_manager = User.query.filter_by(role=Role.COORDINADOR).all()
        users_salesman = User.query.filter_by(role=Role.VENDEDOR).all()
        current_date = datetime.now().date()
        tomorrow = datetime.now().date() + timedelta(days=1)

        # PRIMERO: Procesar TODOS los vendedores que NO son coordinadores
        for user in users_salesman:
            user_id = user.id
            employee = Employee.query.filter_by(user_id=user_id).first()
            if not employee:
                continue
            
            # Verificar si este vendedor es también un coordinador (sub-coordinador)
            is_manager = Manager.query.filter_by(employee_id=employee.id).first()
            if not is_manager:
                # Es un vendedor puro - procesarlo
                process_salesman_record(employee.id, current_date)

        # SEGUNDO: Procesar coordinadores usando función recursiva (bottom-up)
        for user in users_manager:
            user_id = user.id
            manager_array = Employee.query.filter_by(user_id=user_id).first()
            if not manager_array:
                continue
            
            # Obtener el Manager ID
            manager = Manager.query.filter_by(employee_id=manager_array.id).first()
            if manager:
                process_coordinator_hierarchy(manager.id, current_date)
        
        return render_template('add-manager-record.html')
    except Exception as e:
        db.session.rollback()
        # Log del error (puedes usar logging aquí)
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

    # Obtener el empleado asociado al préstamo
    employee = Employee.query.get(loan.employee_id)
    
    # Reintegrar el monto del préstamo al box_value del empleado
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
                    Loan.status == True,  # Solo préstamos activos
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
                    Loan.status == True,  # Solo préstamos activos
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

        # Calcular totales de transacciones del sub-administrador para la fecha filtrada (incluyendo transacciones directas)
        total_outbound_amount, total_inbound_amount = calculate_daily_transaction_totals_history(manager_id, filter_date, sub_admin_employee.id)

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