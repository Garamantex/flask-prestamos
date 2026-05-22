# app/routes/transactions_routes.py
# Transacciones, gastos, conceptos y morosos

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

@routes.route('/concept', methods=['GET', 'POST'])
def create_concept():
    """Crear un nuevo concepto de transacción
    ---
    tags:
      - Transacciones
    consumes:
      - application/x-www-form-urlencoded
    parameters:
      - name: concept
        in: formData
        type: string
        required: true
        description: Nombre del concepto
      - name: transaction_types
        in: formData
        type: string
        required: true
        description: Tipo de transacción (GASTO, INGRESO, RETIRO)
    responses:
      200:
        description: Concepto creado exitosamente
    """
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
    """Actualizar un concepto existente
    ---
    tags:
      - Transacciones
    consumes:
      - application/json
    parameters:
      - name: concept_id
        in: path
        type: integer
        required: true
        description: ID del concepto a actualizar
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              description: Nuevo nombre del concepto
            transaction_types:
              type: string
              description: Nuevo tipo de transacción
    responses:
      200:
        description: Concepto actualizado
        schema:
          type: object
          properties:
            id:
              type: integer
            name:
              type: string
            transaction_types:
              type: string
      404:
        description: Concepto no encontrado
    """
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
    """Listar conceptos por tipo de transacción
    ---
    tags:
      - Transacciones
    parameters:
      - name: transaction_type
        in: query
        type: string
        required: true
        description: Tipo de transacción (GASTO, INGRESO, RETIRO)
        enum: [GASTO, INGRESO, RETIRO]
    responses:
      200:
        description: Lista de conceptos
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              name:
                type: string
              transaction_types:
                type: string
    """
    transaction_type = request.args.get('transaction_type')

    # Consultar los conceptos relacionados con el tipo de transacción
    concepts = Concept.query.filter_by(
        transaction_types=transaction_type).all()

    # Convertir los conceptos a formato JSON
    concepts_json = [concept.to_json() for concept in concepts]

    return jsonify(concepts_json)




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
    """Obtener lista de clientes morosos con detalles de deuda
    ---
    tags:
      - Transacciones
    responses:
      200:
        description: Lista de vendedores con sus clientes morosos
        schema:
          type: array
          items:
            type: object
            properties:
              employee_name:
                type: string
                description: Nombre del vendedor
              total_overdue_installments:
                type: integer
                description: Total de cuotas en mora
              clients:
                type: array
                items:
                  type: object
                  properties:
                    client_name:
                      type: string
                    paid_installments:
                      type: integer
                    overdue_installments:
                      type: integer
                    remaining_debt:
                      type: number
                    total_overdue_amount:
                      type: number
      404:
        description: Empleado no encontrado
    """
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
                    # INGRESO y RETIRO se aprueban automáticamente
                    approval_status = "APROBADA"
                else:
                    # Para GASTOS: coordinadores se aprueban automáticamente, vendedores requieren aprobación
                    if user_role == 'COORDINADOR':
                        approval_status = "APROBADA"
                    else:
                        # VENDEDOR: requiere aprobación
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




@routes.route('/api/transactions/<int:employee_id>/<transaction_type>', methods=['GET'])
def get_transactions_by_type(employee_id, transaction_type):
    """Obtener transacciones aprobadas del día por tipo y empleado
    ---
    tags:
      - Transacciones
    parameters:
      - name: employee_id
        in: path
        type: integer
        required: true
        description: ID del empleado
      - name: transaction_type
        in: path
        type: string
        required: true
        description: Tipo de transacción
        enum: [GASTO, INGRESO, RETIRO]
    responses:
      200:
        description: Lista de transacciones del día
        schema:
          type: object
          properties:
            transactions:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  description:
                    type: string
                  amount:
                    type: number
                  approval_status:
                    type: string
                  creation_date:
                    type: string
                    format: date-time
                  employee_id:
                    type: integer
      400:
        description: Tipo de transacción inválido
      401:
        description: Usuario no autenticado
      403:
        description: Acceso denegado
    """
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
    """Editar una transacción existente
    ---
    tags:
      - Transacciones
    consumes:
      - application/json
    parameters:
      - name: transaction_id
        in: path
        type: integer
        required: true
        description: ID de la transacción a editar
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            amount:
              type: number
              description: Nuevo monto (debe ser mayor a 0)
            description:
              type: string
              description: Nueva descripción
            approval_status:
              type: string
              description: Nuevo estado
              enum: [APROBADA, RECHAZADA]
    responses:
      200:
        description: Transacción actualizada exitosamente
        schema:
          type: object
          properties:
            message:
              type: string
            transaction:
              type: object
              properties:
                id:
                  type: integer
                description:
                  type: string
                amount:
                  type: number
                approval_status:
                  type: string
      400:
        description: Datos inválidos
      401:
        description: Usuario no autenticado
      403:
        description: Acceso denegado
      404:
        description: Transacción no encontrada
    """
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
    """Eliminar transacción (soft delete)
    ---
    tags:
      - Transacciones
    parameters:
      - name: transaction_id
        in: path
        type: integer
        required: true
        description: ID de la transacción a eliminar
    responses:
      200:
        description: Transacción eliminada exitosamente
        schema:
          type: object
          properties:
            message:
              type: string
            transaction_id:
              type: integer
      400:
        description: Transacción ya eliminada
      401:
        description: Usuario no autenticado
      403:
        description: Acceso denegado
      404:
        description: Transacción no encontrada
    """
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


