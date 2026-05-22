# app/routes/helpers.py
# Funciones auxiliares compartidas para todas las rutas

# Importaciones estándar
from datetime import datetime, date, timedelta
from decimal import Decimal
import holidays

# Importaciones de SQLAlchemy
from sqlalchemy import func, case, join, tuple_, and_
from sqlalchemy.orm import joinedload

# Importaciones de Flask
from flask import session, request, jsonify, url_for

# Importaciones de modelos
from app.models import (
    db, User, Client, Loan, Employee, LoanInstallment,
    InstallmentStatus, Concept, Transaction, Role, Manager,
    Payment, Salesman, TransactionType, ApprovalStatus, EmployeeRecord
)


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


def distribute_advance_payment(loan, start_date, advance_amount, current_date):
    """
    Distribuye el monto abonado secuencialmente entre las cuotas desde la fecha de inicio hasta la fecha actual.
    Usa la misma lógica del pago regular: cubre completamente las cuotas hasta donde alcance,
    y si el restante no alcanza para una cuota completa, esa cuota queda abonada.
    
    Args:
        loan: Objeto Loan
        start_date: Fecha de inicio del préstamo (date)
        advance_amount: Monto total abonado (Decimal)
        current_date: Fecha actual (date)
    
    Returns:
        Número de cuotas procesadas
    """
    if advance_amount <= 0:
        return 0
    
    # Obtener todas las cuotas del préstamo ordenadas por fecha de vencimiento
    installments = LoanInstallment.query.filter_by(loan_id=loan.id)\
        .order_by(LoanInstallment.due_date.asc()).all()
    
    if not installments:
        return 0
    
    # Filtrar cuotas que están entre start_date y current_date
    # Las cuotas se generan desde la fecha de creación del préstamo (que es start_date)
    # Necesitamos las cuotas cuya fecha de vencimiento esté entre start_date y current_date
    installments_to_pay = [
        inst for inst in installments 
        if inst.due_date >= start_date and inst.due_date <= current_date
    ]
    
    if not installments_to_pay:
        return 0
    
    # Ordenar por fecha de vencimiento (ya deberían estar ordenadas, pero por seguridad)
    installments_to_pay.sort(key=lambda x: x.due_date if x.due_date else datetime.max)
    
    # Crear timestamp para los pagos
    payment_timestamp = datetime.combine(start_date, datetime.min.time())
    
    # Aplicar el monto secuencialmente (misma lógica que el pago regular)
    remaining_payment = Decimal(str(advance_amount))
    processed_count = 0
    
    for installment in installments_to_pay:
        if remaining_payment <= 0:
            break
        
        # Calcular cuánto se debe realmente de esta cuota
        total_paid_before = db.session.query(func.sum(Payment.amount)).filter(
            Payment.installment_id == installment.id
        ).scalar() or Decimal('0')
        
        # El monto pendiente de esta cuota
        amount_due = installment.fixed_amount - total_paid_before
        
        if amount_due <= 0:
            # Esta cuota ya está completamente pagada, continuar con la siguiente
            continue
        
        if remaining_payment >= amount_due:
            # El monto abonado cubre completamente esta cuota
            installment.status = InstallmentStatus.PAGADA
            installment.amount = Decimal('0')
            if not installment.payment_date:
                installment.payment_date = start_date
            
            # Crear el pago por el monto completo de la cuota
            payment = Payment(
                amount=amount_due,
                payment_date=payment_timestamp,
                installment_id=installment.id
            )
            db.session.add(payment)
            remaining_payment -= amount_due
            processed_count += 1
            
            # Si el pago restante es exactamente 0, terminar
            if remaining_payment == 0:
                break
        else:
            # El monto abonado solo cubre parcialmente esta cuota
            installment.status = InstallmentStatus.ABONADA
            installment.amount = amount_due - remaining_payment
            
            # Crear el pago por el monto parcial
            payment = Payment(
                amount=remaining_payment,
                payment_date=payment_timestamp,
                installment_id=installment.id
            )
            db.session.add(payment)
            remaining_payment = Decimal('0')
            processed_count += 1
            break
    
    db.session.commit()
    return processed_count


def recalculate_loan_installments(loan, new_amount, new_dues, new_interest):
    """
    Recalcula las cuotas del préstamo cuando se modifican parámetros.
    
    Args:
        loan: Objeto Loan
        new_amount: Nuevo monto del préstamo (Decimal)
        new_dues: Nuevo número de cuotas (int)
        new_interest: Nuevo interés (Decimal)
    """
    # Calcular nuevo monto de cuota
    new_installment_amount = Decimal(str((float(new_amount) + (float(new_amount) * float(new_interest) / 100)) / float(new_dues)))
    
    # Obtener todas las cuotas del préstamo
    installments = LoanInstallment.query.filter_by(loan_id=loan.id)\
        .order_by(LoanInstallment.installment_number.asc()).all()
    
    # Si hay más cuotas que las nuevas, eliminar las extras
    if len(installments) > new_dues:
        for inst in installments[new_dues:]:
            # Eliminar pagos asociados
            Payment.query.filter_by(installment_id=inst.id).delete()
            db.session.delete(inst)
        installments = installments[:new_dues]
    
    # Actualizar cuotas existentes y crear nuevas si es necesario
    for i in range(int(new_dues)):
        if i < len(installments):
            # Actualizar cuota existente
            installment = installments[i]
            
            # Calcular pagos existentes
            total_paid = db.session.query(func.sum(Payment.amount)).filter(
                Payment.installment_id == installment.id
            ).scalar() or Decimal('0')
            
            # Actualizar fixed_amount
            installment.fixed_amount = new_installment_amount
            
            # Recalcular amount pendiente
            installment.amount = new_installment_amount - total_paid
            
            # Actualizar estado
            if installment.amount <= 0:
                installment.status = InstallmentStatus.PAGADA
                installment.amount = Decimal('0')
            elif total_paid > 0:
                installment.status = InstallmentStatus.ABONADA
            else:
                installment.status = InstallmentStatus.PENDIENTE
        else:
            # Crear nueva cuota
            # Calcular fecha de vencimiento basada en la última cuota
            if installments:
                last_due_date = installments[-1].due_date
                new_due_date = last_due_date + timedelta(days=1)
            else:
                new_due_date = loan.creation_date.date() + timedelta(days=1)
            
            new_installment = LoanInstallment(
                installment_number=i + 1,
                due_date=new_due_date,
                fixed_amount=new_installment_amount,
                amount=new_installment_amount,
                status=InstallmentStatus.PENDIENTE,
                loan_id=loan.id
            )
            db.session.add(new_installment)
    
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
    cuotas_abonadas = sum(
        1 for installment in installments if installment.status == InstallmentStatus.ABONADA)
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
    
    # Obtener el valor inicial del último registro del día anterior, o usar box_value si no hay registro
    current_date = datetime.now().date()
    last_record = EmployeeRecord.query.filter_by(employee_id=coordinator.id) \
        .filter(func.date(EmployeeRecord.creation_date) < current_date) \
        .order_by(EmployeeRecord.creation_date.desc()).first()
    
    if last_record:
        coordinator_cash = float(last_record.closing_total)
    else:
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

def get_pure_salesmen_ids(manager_id):
    """
    Obtiene los IDs de empleados de vendedores puros (excluyendo subcoordinadores).
    Un subcoordinador es un Salesman que también tiene registro en Manager.
    """
    # Obtener todos los Salesman bajo este manager
    all_salesmen = Salesman.query.filter_by(manager_id=manager_id).all()
    
    # Obtener todos los employee_id que son Managers (subcoordinadores)
    subcoordinator_ids = db.session.query(Manager.employee_id).all()
    subcoordinator_ids_set = {subcoord[0] for subcoord in subcoordinator_ids}
    
    # Filtrar para obtener solo vendedores puros (que NO son Managers)
    pure_salesmen_ids = [
        salesman.employee_id 
        for salesman in all_salesmen 
        if salesman.employee_id not in subcoordinator_ids_set
    ]
    
    return pure_salesmen_ids

def calculate_daily_transaction_totals(manager_id, current_date, coordinator_id=None):
    """
    Calcula los totales de transacciones diarias para el coordinador.
    Excluye subcoordinadores de los cálculos.
    
    Retorna una tupla con:
    (salesman_incomes, salesman_withdrawals, coordinator_incomes, coordinator_withdrawals)
    
    Donde:
    - salesman_incomes: INGRESOS de vendedores puros aprobados (deben RESTAR de la caja del coordinador)
    - salesman_withdrawals: RETIROS de vendedores puros aprobados (deben SUMAR a la caja del coordinador)
    - coordinator_incomes: INGRESOS del coordinador (deben SUMAR a la caja del coordinador)
    - coordinator_withdrawals: RETIROS del coordinador (deben RESTAR de la caja del coordinador)
    """
    start_of_day = datetime.combine(current_date, datetime.min.time())
    end_of_day = datetime.combine(current_date, datetime.max.time())
    
    # Obtener IDs de vendedores puros (excluyendo subcoordinadores)
    pure_salesmen_ids = get_pure_salesmen_ids(manager_id)
    
    # INGRESOS de vendedores puros aprobados (RESTAR de la caja del coordinador)
    salesman_incomes = 0
    if pure_salesmen_ids:
        salesman_incomes = db.session.query(
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            Transaction.employee_id.in_(pure_salesmen_ids),
            Transaction.transaction_types == 'INGRESO',
            Transaction.approval_status == 'APROBADA',
            Transaction.creation_date.between(start_of_day, end_of_day),
            ~Transaction.description.like('[ELIMINADA]%')
        ).scalar() or 0
    
    # RETIROS de vendedores puros aprobados (SUMAR a la caja del coordinador)
    salesman_withdrawals = 0
    if pure_salesmen_ids:
        salesman_withdrawals = db.session.query(
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            Transaction.employee_id.in_(pure_salesmen_ids),
            Transaction.transaction_types == 'RETIRO',
            Transaction.approval_status == 'APROBADA',
            func.date(Transaction.creation_date) == current_date,
            ~Transaction.description.like('[ELIMINADA]%')
        ).scalar() or 0
    
    # INGRESOS del coordinador (SUMAR a la caja del coordinador)
    coordinator_incomes = 0
    if coordinator_id:
        coordinator_incomes = db.session.query(
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            Transaction.employee_id == coordinator_id,
            Transaction.transaction_types == 'INGRESO',
            Transaction.approval_status == 'APROBADA',
            func.date(Transaction.creation_date) == current_date,
            ~Transaction.description.like('[ELIMINADA]%')
        ).scalar() or 0
    
    # RETIROS del coordinador (RESTAR de la caja del coordinador)
    coordinator_withdrawals = 0
    if coordinator_id:
        coordinator_withdrawals = db.session.query(
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            Transaction.employee_id == coordinator_id,
            Transaction.transaction_types == 'RETIRO',
            Transaction.approval_status == 'APROBADA',
            func.date(Transaction.creation_date) == current_date,
            ~Transaction.description.like('[ELIMINADA]%')
        ).scalar() or 0
    
    return (
        float(salesman_incomes),
        float(salesman_withdrawals),
        float(coordinator_incomes),
        float(coordinator_withdrawals)
    )

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
    
    # 1. Obtener registros del día actual
    today_records = db.session.query(EmployeeRecord).filter(
        EmployeeRecord.employee_id.in_(employee_ids),
        func.date(EmployeeRecord.creation_date) == current_date
    ).all()
    today_records_dict = {record.employee_id: record for record in today_records}
    
    # 2. Obtener el último registro del día anterior para cada empleado
    # Esto es importante para obtener el valor inicial correcto
    previous_day_records = db.session.query(EmployeeRecord).filter(
        EmployeeRecord.employee_id.in_(employee_ids),
        func.date(EmployeeRecord.creation_date) < current_date
    ).order_by(EmployeeRecord.employee_id, EmployeeRecord.creation_date.desc()).all()
    
    # Agrupar por employee_id y tomar el más reciente del día anterior
    latest_records = {}
    for record in previous_day_records:
        if record.employee_id not in latest_records:
            latest_records[record.employee_id] = record
    
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
    # Separar el conteo de clientes nuevos del monto de préstamos nuevos
    # Clientes nuevos: filtrado por Client.creation_date
    new_clients_query = db.session.query(
        Client.employee_id,
        func.count(Client.id).label('new_clients_count')
    ).filter(
        Client.employee_id.in_(employee_ids),
        Client.creation_date >= start_of_day
    ).group_by(Client.employee_id).all()
    
    # Préstamos nuevos: filtrado por Loan.creation_date (no Client.creation_date)
    # Esto es importante para préstamos personalizados con fecha de inicio anterior
    new_loans_query = db.session.query(
        Client.employee_id,
        func.sum(Loan.amount).label('new_loans_amount')
    ).join(Loan, Client.id == Loan.client_id).filter(
        Client.employee_id.in_(employee_ids),
        Loan.creation_date >= start_of_day,  # Cambiar de Client.creation_date a Loan.creation_date
        Loan.is_renewal == False,
        Loan.status == True  # Solo préstamos activos
    ).group_by(Client.employee_id).all()
    
    new_clients_data = {emp_id: {'count': 0, 'amount': 0} for emp_id in employee_ids}
    
    # Procesar conteo de clientes nuevos
    for data in new_clients_query:
        new_clients_data[data.employee_id]['count'] = data.new_clients_count or 0
    
    # Procesar monto de préstamos nuevos (solo los creados HOY)
    for data in new_loans_query:
        new_clients_data[data.employee_id]['amount'] = data.new_loans_amount or 0
    
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
        # Siempre usar el último registro del día anterior (misma lógica que box_detail_admin)
        # Si hay registro del día anterior, usar su closing_total; si no, usar box_value
        initial_box_value = 0
        if emp_id in latest_records:
            # Usar closing_total del último registro del día anterior
            initial_box_value = latest_records[emp_id].closing_total
        else:
            # Si no hay registro previo, usar box_value actual
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
        # 1. Obtener registros del día actual
        today_records = db.session.query(EmployeeRecord).filter(
            EmployeeRecord.employee_id.in_(employee_ids),
            func.date(EmployeeRecord.creation_date) == current_date
        ).all()
        today_records_dict = {record.employee_id: record for record in today_records}
        
        # 2. Obtener el último registro del día anterior para cada empleado
        # Esto es importante para obtener el valor inicial correcto
        previous_day_records = db.session.query(EmployeeRecord).filter(
            EmployeeRecord.employee_id.in_(employee_ids),
            func.date(EmployeeRecord.creation_date) < current_date
        ).order_by(EmployeeRecord.employee_id, EmployeeRecord.creation_date.desc()).all()
        
        # Agrupar por employee_id y tomar el más reciente del día anterior
        latest_records = {}
        for record in previous_day_records:
            if record.employee_id not in latest_records:
                latest_records[record.employee_id] = record
        
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
    # Separar el conteo de clientes nuevos del monto de préstamos nuevos
    # Clientes nuevos: filtrado por Client.creation_date
    new_clients_query = db.session.query(
        Client.employee_id,
        func.count(Client.id).label('new_clients_count')
    ).filter(
        Client.employee_id.in_(employee_ids),
        func.date(Client.creation_date) == filter_date
    ).group_by(Client.employee_id).all()
    
    # Préstamos nuevos: filtrado por Loan.creation_date (no Client.creation_date)
    # Esto es importante para préstamos personalizados con fecha de inicio anterior
    new_loans_query = db.session.query(
        Client.employee_id,
        func.sum(Loan.amount).label('new_loans_amount')
    ).join(Loan, Client.id == Loan.client_id).filter(
        Client.employee_id.in_(employee_ids),
        func.date(Loan.creation_date) == filter_date,  # Cambiar de Client.creation_date a Loan.creation_date
        Loan.is_renewal == False,
        Loan.status == True  # Solo préstamos activos
    ).group_by(Client.employee_id).all()
    
    new_clients_data = {emp_id: {'count': 0, 'amount': 0} for emp_id in employee_ids}
    
    # Procesar conteo de clientes nuevos
    for data in new_clients_query:
        new_clients_data[data.employee_id]['count'] = data.new_clients_count or 0
    
    # Procesar monto de préstamos nuevos (solo los creados en la fecha filtrada)
    for data in new_loans_query:
        new_clients_data[data.employee_id]['amount'] = data.new_loans_amount or 0
    
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
            # Para día actual, usar la misma lógica que box_detail_admin
            # Siempre usar el último registro del día anterior (misma lógica que box_detail_admin)
            # Si hay registro del día anterior, usar su closing_total; si no, usar box_value
            if emp_id in latest_records:
                # Usar closing_total del último registro del día anterior
                initial_box_value = latest_records[emp_id].closing_total
            else:
                # Si no hay registro previo, usar box_value actual
                initial_box_value = float(employee.box_value)
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
    """
    Calcula los totales de transacciones diarias para el coordinador en history-box.
    Excluye subcoordinadores de los cálculos.
    
    Retorna una tupla con:
    (salesman_incomes, salesman_withdrawals, coordinator_incomes, coordinator_withdrawals)
    
    Donde:
    - salesman_incomes: INGRESOS de vendedores puros aprobados (deben RESTAR de la caja del coordinador)
    - salesman_withdrawals: RETIROS de vendedores puros aprobados (deben SUMAR a la caja del coordinador)
    - coordinator_incomes: INGRESOS del coordinador (deben SUMAR a la caja del coordinador)
    - coordinator_withdrawals: RETIROS del coordinador (deben RESTAR de la caja del coordinador)
    """
    start_of_day = datetime.combine(filter_date, datetime.min.time())
    end_of_day = datetime.combine(filter_date, datetime.max.time())
    
    # Obtener IDs de vendedores puros (excluyendo subcoordinadores)
    pure_salesmen_ids = get_pure_salesmen_ids(manager_id)
    
    # INGRESOS de vendedores puros aprobados (RESTAR de la caja del coordinador)
    salesman_incomes = 0
    if pure_salesmen_ids:
        salesman_incomes = db.session.query(
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            Transaction.employee_id.in_(pure_salesmen_ids),
            Transaction.transaction_types == 'INGRESO',
            Transaction.approval_status == 'APROBADA',
            Transaction.creation_date.between(start_of_day, end_of_day),
            ~Transaction.description.like('[ELIMINADA]%')
        ).scalar() or 0
    
    # RETIROS de vendedores puros aprobados (SUMAR a la caja del coordinador)
    salesman_withdrawals = 0
    if pure_salesmen_ids:
        salesman_withdrawals = db.session.query(
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            Transaction.employee_id.in_(pure_salesmen_ids),
            Transaction.transaction_types == 'RETIRO',
            Transaction.approval_status == 'APROBADA',
            func.date(Transaction.creation_date) == filter_date,
            ~Transaction.description.like('[ELIMINADA]%')
        ).scalar() or 0
    
    # INGRESOS del coordinador (SUMAR a la caja del coordinador)
    coordinator_incomes = 0
    if coordinator_id:
        coordinator_incomes = db.session.query(
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            Transaction.employee_id == coordinator_id,
            Transaction.transaction_types == 'INGRESO',
            Transaction.approval_status == 'APROBADA',
            func.date(Transaction.creation_date) == filter_date,
            ~Transaction.description.like('[ELIMINADA]%')
        ).scalar() or 0
    
    # RETIROS del coordinador (RESTAR de la caja del coordinador)
    coordinator_withdrawals = 0
    if coordinator_id:
        coordinator_withdrawals = db.session.query(
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            Transaction.employee_id == coordinator_id,
            Transaction.transaction_types == 'RETIRO',
            Transaction.approval_status == 'APROBADA',
            func.date(Transaction.creation_date) == filter_date,
            ~Transaction.description.like('[ELIMINADA]%')
        ).scalar() or 0
    
    return (
        float(salesman_incomes),
        float(salesman_withdrawals),
        float(coordinator_incomes),
        float(coordinator_withdrawals)
    )


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



def process_salesman_record(employee_id, current_date):
    """
    Procesa el registro de cierre de caja para un vendedor.
    Si ya existe un registro para el día, lo actualiza en lugar de crear uno nuevo.
    Retorna True si se procesó correctamente.
    
    NOTA: No hace commit — el llamador es responsable de hacer db.session.commit().
    """
    # Verificar si ya existe un registro para este empleado en la fecha actual
    existing_record = EmployeeRecord.query.filter_by(employee_id=employee_id) \
        .filter(func.date(EmployeeRecord.creation_date) == current_date).first()
    
    employee = Employee.query.get(employee_id)
    if not employee:
        return False
    
    employee_status = employee.status

    # Buscar el último registro en EmployeeRecord del día anterior
    last_record = EmployeeRecord.query.filter_by(employee_id=employee_id) \
        .filter(func.date(EmployeeRecord.creation_date) < current_date) \
        .order_by(EmployeeRecord.creation_date.desc()).first()

    # Calcular la cantidad de préstamos por cobrar
    loans_to_collect = Loan.query.filter_by(
        employee_id=employee_id, status=True).count()

    # --- Cuotas PAGADAS: monto total de pagos del día ---
    paid_installments_query = db.session.query(LoanInstallment.id) \
        .join(Loan) \
        .filter(Loan.employee_id == employee_id,
                LoanInstallment.status == InstallmentStatus.PAGADA) \
        .subquery()

    paid_installments_amount = db.session.query(func.sum(Payment.amount)) \
        .join(paid_installments_query, Payment.installment_id == paid_installments_query.c.id) \
        .filter(func.date(Payment.payment_date) == current_date) \
        .scalar() or 0

    # --- Debido cobrar del siguiente día y préstamos cerrados (optimizado con bulk queries) ---
    total_pending_installments_amount = 0
    total_pending_installments_loan_close_amount = 0

    # Préstamos activos: obtener la primera cuota de cada préstamo (excluyendo préstamos creados hoy)
    active_first_installments = db.session.query(
        LoanInstallment.loan_id,
        func.min(LoanInstallment.due_date).label('first_due_date')
    ).join(Loan).join(Client).filter(
        Client.employee_id == employee_id,
        Loan.status == True,
        func.date(Loan.creation_date) != current_date
    ).group_by(LoanInstallment.loan_id).subquery()

    # Sumar los fixed_amount de las primeras cuotas de préstamos activos
    total_pending_installments_amount = db.session.query(
        func.sum(LoanInstallment.fixed_amount)
    ).join(
        active_first_installments,
        and_(
            LoanInstallment.loan_id == active_first_installments.c.loan_id,
            LoanInstallment.due_date == active_first_installments.c.first_due_date
        )
    ).scalar() or 0

    # Préstamos cerrados hoy y al día: obtener la primera cuota
    closed_first_installments = db.session.query(
        LoanInstallment.loan_id,
        func.min(LoanInstallment.due_date).label('first_due_date')
    ).join(Loan).join(Client).filter(
        Client.employee_id == employee_id,
        Loan.status == False,
        Loan.up_to_date == True,
        func.date(Loan.modification_date) == current_date
    ).group_by(LoanInstallment.loan_id).subquery()

    total_pending_installments_loan_close_amount = db.session.query(
        func.sum(LoanInstallment.fixed_amount)
    ).join(
        closed_first_installments,
        and_(
            LoanInstallment.loan_id == closed_first_installments.c.loan_id,
            LoanInstallment.due_date == closed_first_installments.c.first_due_date
        )
    ).scalar() or 0

    # --- Cuotas ABONADAS: monto total de pagos del día ---
    partial_installments_query = db.session.query(LoanInstallment.id) \
        .join(Loan) \
        .filter(Loan.employee_id == employee_id,
                LoanInstallment.status == InstallmentStatus.ABONADA) \
        .subquery()

    partial_installments = db.session.query(func.sum(Payment.amount)) \
        .join(partial_installments_query,
              Payment.installment_id == partial_installments_query.c.id) \
        .filter(func.date(Payment.payment_date) == current_date) \
        .scalar() or 0

    # --- Cuotas en MORA: monto total ---
    overdue_installments_query = db.session.query(LoanInstallment.id) \
        .join(Loan) \
        .filter(Loan.employee_id == employee_id,
                LoanInstallment.status == InstallmentStatus.MORA) \
        .subquery()

    overdue_installments_total = db.session.query(func.sum(LoanInstallment.amount)) \
        .join(overdue_installments_query,
              LoanInstallment.id == overdue_installments_query.c.id) \
        .join(Payment, Payment.installment_id == LoanInstallment.id) \
        .filter(func.date(Payment.payment_date) == current_date) \
        .scalar() or 0

    # --- Total recaudado en la fecha actual ---
    total_collected = db.session.query(
        db.func.sum(Payment.amount)
    ).join(LoanInstallment, LoanInstallment.id == Payment.installment_id).join(
        Loan, Loan.id == LoanInstallment.loan_id
    ).filter(
        and_(Loan.employee_id == employee_id, func.date(
            Payment.payment_date) == current_date)
    ).scalar() or 0

    # --- Préstamos nuevos y renovaciones (2 queries en vez de 2, sin cambio) ---
    new_clients_loan_amount = Loan.query.join(Client).filter(
        Client.employee_id == employee_id,
        func.date(Loan.creation_date) == current_date,
        Loan.is_renewal == False,
        Loan.status == True
    ).with_entities(func.sum(Loan.amount)).scalar() or 0

    total_renewal_loans_amount = Loan.query.filter(
        Loan.client.has(employee_id=employee_id),
        Loan.is_renewal == True,
        Loan.status == True,
        Loan.approved == True,
        func.date(Loan.creation_date) == current_date
    ).with_entities(func.sum(Loan.amount)).scalar() or 0

    # --- OPTIMIZACIÓN: Consolidar 3 queries de transacciones en 1 con GROUP BY ---
    transaction_totals = db.session.query(
        Transaction.transaction_types,
        func.sum(Transaction.amount)
    ).filter(
        Transaction.employee_id == employee_id,
        Transaction.approval_status == ApprovalStatus.APROBADA,
        func.date(Transaction.creation_date) == current_date,
        Transaction.transaction_types.in_([
            TransactionType.GASTO,
            TransactionType.RETIRO,
            TransactionType.INGRESO
        ])
    ).group_by(Transaction.transaction_types).all()

    # Mapear los resultados
    transaction_map = {t_type: float(amount) for t_type, amount in transaction_totals}
    daily_expenses_amount = transaction_map.get(TransactionType.GASTO, 0)
    daily_withdrawals_amount = transaction_map.get(TransactionType.RETIRO, 0)
    daily_incomes_amount = transaction_map.get(TransactionType.INGRESO, 0)

    # --- OPTIMIZACIÓN: Verificar pagos del día con una sola query JOIN ---
    # En vez del triple loop O(n³), contamos préstamos distintos con pago hoy
    all_loans_paid_count = db.session.query(
        func.count(func.distinct(Loan.id))
    ).join(
        LoanInstallment, LoanInstallment.loan_id == Loan.id
    ).join(
        Payment, Payment.installment_id == LoanInstallment.id
    ).filter(
        Loan.employee_id == employee_id,
        func.date(Payment.payment_date) == current_date
    ).scalar() or 0

    all_loans_paid_today = (loans_to_collect == all_loans_paid_count)

    # Determinar initial_state
    initial_state = 0
    if last_record:
        initial_state = float(last_record.closing_total)

    # Calcular closing_total
    closing_total = int(initial_state) + int(paid_installments_amount) \
        + int(partial_installments) + int(daily_incomes_amount) \
        - int(new_clients_loan_amount) \
        - int(total_renewal_loans_amount) \
        - int(daily_withdrawals_amount) \
        - int(daily_expenses_amount)

    # Si existe un registro, actualizarlo; si no, crear uno nuevo
    if existing_record:
        # Actualizar registro existente
        existing_record.initial_state = initial_state
        existing_record.incomings = daily_incomes_amount
        existing_record.expenses = daily_expenses_amount
        existing_record.withdrawals = daily_withdrawals_amount
        existing_record.closing_total = closing_total
        existing_record.loans_to_collect = loans_to_collect
        existing_record.paid_installments = paid_installments_amount
        existing_record.partial_installments = partial_installments
        existing_record.overdue_installments = overdue_installments_total
        existing_record.sales = new_clients_loan_amount
        existing_record.renewals = total_renewal_loans_amount
        existing_record.due_to_collect_tomorrow = total_pending_installments_amount
        existing_record.total_collected = total_collected
        existing_record.due_to_charge = total_pending_installments_loan_close_amount + total_pending_installments_amount
        
        employee.status = 0
        employee.box_value = closing_total
        
        db.session.add(employee)
        db.session.add(existing_record)
    else:
        # Crear nuevo registro
        employee_record = EmployeeRecord(
            employee_id=employee_id,
            initial_state=initial_state,
            incomings=daily_incomes_amount,
            expenses=daily_expenses_amount,
            withdrawals=daily_withdrawals_amount,
            closing_total=closing_total,
            creation_date=datetime.combine(current_date, datetime.now().time()),
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
        employee.box_value = closing_total

        db.session.add(employee)
        db.session.add(employee_record)
    
    # Flush para que los datos sean visibles en la misma sesión sin commit
    db.session.flush()
    return True


def process_coordinator_hierarchy(manager_id, current_date):
    """
    Procesa coordinadores recursivamente de abajo hacia arriba.
    Primero procesa todos los sub-coordinadores, luego vendedores puros, finalmente el coordinador padre.
    
    NOTA: No hace commit — el llamador es responsable de hacer db.session.commit().
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
    
    manager_array = Employee.query.get(employee_id)
    if not manager_array:
        return

    # Obtener todos los Salesman bajo este manager
    salesmen = Salesman.query.filter_by(manager_id=manager_id).all()
    
    # OPTIMIZACIÓN: Pre-cargar todos los employee_ids que son managers en una sola query
    all_manager_employee_ids = {
        m.employee_id for m in db.session.query(Manager.employee_id).all()
    }
    
    # Separar vendedores puros de sub-coordinadores sin queries individuales
    pure_salesmen = []
    sub_coordinators = []
    
    for salesman in salesmen:
        if salesman.employee_id in all_manager_employee_ids:
            sub_coordinators.append(salesman)
        else:
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
    # Inicializar las variables (que no se usan para coordinadores)
    loans_to_collect = 0
    paid_installments = 0
    partial_installments = 0
    overdue_installments_total = 0
    total_collected = 0
    new_clients_loan_amount = 0
    total_renewal_loans_amount = 0
    total_pending_installments_amount = 0

    # Buscar el último registro en EmployeeRecord del día anterior
    last_record = EmployeeRecord.query.filter_by(employee_id=employee_id) \
        .filter(func.date(EmployeeRecord.creation_date) < current_date) \
        .order_by(EmployeeRecord.creation_date.desc()).first()

    # Usar el initial_state del último registro como estado inicial para hoy
    if last_record:
        initial_state = float(last_record.initial_state) + float(last_record.incomings) - float(last_record.withdrawals) - float(last_record.expenses)
    else:
        initial_state = float(manager_array.box_value)

    # --- OPTIMIZACIÓN: Consolidar 3 queries de transacciones del coordinador en 1 ---
    coordinator_transaction_totals = db.session.query(
        Transaction.transaction_types,
        func.sum(Transaction.amount)
    ).filter(
        Transaction.employee_id == employee_id,
        Transaction.approval_status == ApprovalStatus.APROBADA,
        func.date(Transaction.creation_date) == current_date,
        Transaction.transaction_types.in_([
            TransactionType.GASTO,
            TransactionType.INGRESO,
            TransactionType.RETIRO
        ])
    ).group_by(Transaction.transaction_types).all()

    coord_tx_map = {t_type: float(amount) for t_type, amount in coordinator_transaction_totals}
    coordinator_expenses = coord_tx_map.get(TransactionType.GASTO, 0)
    coordinator_incomes = coord_tx_map.get(TransactionType.INGRESO, 0)
    coordinator_withdrawals = coord_tx_map.get(TransactionType.RETIRO, 0)

    # --- OPTIMIZACIÓN: Consolidar 2N queries de subordinados en 2 queries bulk ---
    pure_salesmen_ids = [s.employee_id for s in pure_salesmen]
    
    total_employee_incomes_amount = 0
    total_employee_withdrawals_amount = 0

    if pure_salesmen_ids:
        # INGRESO de subordinados = RETIRO para el coordinador (subordinado recibe dinero)
        # RETIRO de subordinados = INGRESO para el coordinador (subordinado devuelve dinero)
        subordinate_totals = db.session.query(
            Transaction.transaction_types,
            func.sum(Transaction.amount)
        ).filter(
            Transaction.employee_id.in_(pure_salesmen_ids),
            Transaction.approval_status == ApprovalStatus.APROBADA,
            func.date(Transaction.creation_date) == current_date,
            Transaction.transaction_types.in_([
                TransactionType.INGRESO,
                TransactionType.RETIRO
            ])
        ).group_by(Transaction.transaction_types).all()

        sub_tx_map = {t_type: float(amount) for t_type, amount in subordinate_totals}
        # INGRESO del subordinado = RETIRO para coordinador
        total_employee_withdrawals_amount = sub_tx_map.get(TransactionType.INGRESO, 0)
        # RETIRO del subordinado = INGRESO para coordinador
        total_employee_incomes_amount = sub_tx_map.get(TransactionType.RETIRO, 0)

    # Valor total de INGRESOS Coordinador
    # Incluye transacciones INGRESO del coordinador + RETIRO de subordinados
    daily_incomes_amount = coordinator_incomes + total_employee_incomes_amount

    # Valor total de RETIROS Coordinador
    # Incluye transacciones RETIRO del coordinador + INGRESO de subordinados
    daily_withdrawals_amount = coordinator_withdrawals + total_employee_withdrawals_amount

    # Valor total de GASTOS Coordinador
    daily_expenses_amount = coordinator_expenses

    # Calcular closing_total usando la misma fórmula que la interfaz
    closing_total_calculated = float(initial_state) + float(daily_incomes_amount) - float(daily_withdrawals_amount) - float(daily_expenses_amount)

    # Si existe un registro, actualizarlo; si no, crear uno nuevo
    if existing_record:
        # Actualizar registro existente
        existing_record.initial_state = initial_state
        existing_record.incomings = daily_incomes_amount
        existing_record.expenses = daily_expenses_amount
        existing_record.withdrawals = daily_withdrawals_amount
        existing_record.closing_total = closing_total_calculated
        existing_record.loans_to_collect = loans_to_collect
        existing_record.paid_installments = paid_installments
        existing_record.partial_installments = partial_installments
        existing_record.overdue_installments = overdue_installments_total
        existing_record.sales = new_clients_loan_amount
        existing_record.renewals = total_renewal_loans_amount
        existing_record.due_to_collect_tomorrow = total_pending_installments_amount
        existing_record.total_collected = total_collected
        
        # Actualizar el valor de box_value del modelo Employee
        manager_array.box_value = closing_total_calculated
        
        db.session.add(manager_array)
        db.session.add(existing_record)
    else:
        # Crear nuevo registro
        employee_record = EmployeeRecord(
            employee_id=employee_id,
            initial_state=initial_state,
            incomings=daily_incomes_amount,
            expenses=daily_expenses_amount,
            withdrawals=daily_withdrawals_amount,
            closing_total=closing_total_calculated,
            creation_date=datetime.combine(current_date, datetime.now().time()),
            loans_to_collect=loans_to_collect,
            paid_installments=paid_installments,
            partial_installments=partial_installments,
            overdue_installments=overdue_installments_total,
            sales=new_clients_loan_amount,
            renewals=total_renewal_loans_amount,
            due_to_collect_tomorrow=total_pending_installments_amount,
            total_collected=total_collected
        )
        
        # Actualizar el valor de box_value del modelo Employee
        manager_array.box_value = closing_total_calculated
        
        db.session.add(manager_array)
        db.session.add(employee_record)
    
    # Flush para que los datos sean visibles en la misma sesión sin commit
    db.session.flush()

