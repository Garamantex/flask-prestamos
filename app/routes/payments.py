# app/routes/payments.py
# Pagos, cobros y cuotas

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
            func.max(case((LoanInstallment.status.in_([InstallmentStatus.PAGADA, InstallmentStatus.ABONADA, InstallmentStatus.MORA]), LoanInstallment.due_date), else_=None)).label('prev_due_date')
        ).outerjoin(Payment, Payment.installment_id == LoanInstallment.id) \
         .filter(LoanInstallment.loan_id.in_(loan_ids)) \
         .group_by(LoanInstallment.loan_id).all()

        # Convertir a diccionarios
        last_payment_by_loan = {row.loan_id: row.last_payment_date for row in loan_additional_data if row.last_payment_date}
        next_due_by_loan = {row.loan_id: row.next_due_date for row in loan_additional_data if row.next_due_date}
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

            installment_value = int((loan.amount + (loan.amount * loan.interest / 100)) / loan.dues) if loan.dues > 0 else 0
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
            db.func.max(db.case((LoanInstallment.status.in_([InstallmentStatus.PAGADA, InstallmentStatus.ABONADA, InstallmentStatus.MORA]), LoanInstallment.due_date), else_=None)).label('prev_due_date')
        ).outerjoin(Payment, Payment.installment_id == LoanInstallment.id) \
         .filter(LoanInstallment.loan_id.in_(processed_loan_ids)) \
         .group_by(LoanInstallment.loan_id).all()

        # Convertir a diccionarios
        processed_last_payment_by_loan = {row.loan_id: row.last_payment_date for row in processed_loan_additional_data if row.last_payment_date}
        processed_next_due_by_loan = {row.loan_id: row.next_due_date for row in processed_loan_additional_data if row.next_due_date}
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

            installment_value = int((loan.amount + (loan.amount * loan.interest / 100)) / loan.dues) if loan.dues > 0 else 0
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

    # 📌 **Escenario especial: Si el nuevo pago es 0, revertir y dejar crédito sin alterar**
    if custom_payment == 0:
        # Calcular el total de TODOS los pagos del día actual para este préstamo
        total_payments_to_revert = db.session.query(func.sum(Payment.amount)).join(
            LoanInstallment, Payment.installment_id == LoanInstallment.id
        ).filter(
            LoanInstallment.loan_id == loan_id,
            func.date(Payment.payment_date) == current_date
        ).scalar() or Decimal('0')
        
        # Revertir el valor de la caja del empleado
        employee.box_value -= total_payments_to_revert
        
        # Eliminar TODOS los pagos hechos hoy para este préstamo
        payment_ids_to_delete = db.session.query(Payment.id).join(
            LoanInstallment, Payment.installment_id == LoanInstallment.id
        ).filter(
            LoanInstallment.loan_id == loan_id,
            func.date(Payment.payment_date) == current_date
        ).all()
        
        payment_ids = [payment_id[0] for payment_id in payment_ids_to_delete]
        
        if payment_ids:
            Payment.query.filter(Payment.id.in_(payment_ids)).delete(synchronize_session=False)
        
        # Restaurar las cuotas que fueron pagadas hoy a su estado original
        installments_paid_today = LoanInstallment.query.filter(
            LoanInstallment.loan_id == loan_id,
            (func.date(LoanInstallment.payment_date) == current_date) | (LoanInstallment.payment_date == None),
            LoanInstallment.status.in_([InstallmentStatus.PAGADA, InstallmentStatus.ABONADA])
        ).all()
        
        for installment in installments_paid_today:
            # Calcular cuánto se había pagado antes de hoy (pagos de días anteriores)
            total_paid_before_today = db.session.query(func.sum(Payment.amount)).filter(
                Payment.installment_id == installment.id,
                func.date(Payment.payment_date) != current_date
            ).scalar() or Decimal('0')
            
            # Calcular el monto pendiente real (fixed_amount - pagos previos)
            amount_due = installment.fixed_amount - total_paid_before_today
            
            if amount_due > 0:
                # Aún hay monto pendiente, restaurar a PENDIENTE o ABONADA según corresponda
                installment.amount = amount_due
                if total_paid_before_today > 0:
                    installment.status = InstallmentStatus.ABONADA
                else:
                    installment.status = InstallmentStatus.PENDIENTE
                installment.payment_date = None
            else:
                # Ya estaba completamente pagada antes de hoy, mantener como PAGADA
                installment.status = InstallmentStatus.PAGADA
                installment.amount = Decimal('0')
        
        # Verificar el estado final del préstamo
        remaining_outstanding = sum(
            inst.amount for inst in loan.installments
            if inst.status in [InstallmentStatus.PENDIENTE, InstallmentStatus.ABONADA, InstallmentStatus.MORA]
            and inst.amount > 0
        )
        
        if remaining_outstanding > 0:
            loan.status = True
            loan.up_to_date = False
        else:
            loan.status = False
            loan.up_to_date = True
        
        loan.modification_date = datetime.now()
        db.session.commit()
        
        # Redirigir sin hacer más cambios
        return redirect(url_for('routes.box_detail', employee_id=employee_id))

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

    # 🔄 **Restaurar cuotas a su estado correcto considerando pagos previos**
    for installment in installments_paid_today:
        # Calcular cuánto se había pagado antes de hoy (pagos de días anteriores)
        total_paid_before_today = db.session.query(func.sum(Payment.amount)).filter(
            Payment.installment_id == installment.id,
            func.date(Payment.payment_date) != current_date
        ).scalar() or Decimal('0')
        
        # Calcular el monto pendiente real (fixed_amount - pagos previos)
        amount_due = installment.fixed_amount - total_paid_before_today
        
        if amount_due > 0:
            # Aún hay monto pendiente, restaurar a PENDIENTE o ABONADA según corresponda
            installment.amount = amount_due
            if total_paid_before_today > 0:
                # Ya tenía pagos previos, está abonada
                installment.status = InstallmentStatus.ABONADA
            else:
                # No tenía pagos previos, está pendiente
                installment.status = InstallmentStatus.PENDIENTE
            installment.payment_date = None  # Resetear fecha de pago
        else:
            # Ya estaba completamente pagada antes de hoy, mantener como PAGADA
            installment.status = InstallmentStatus.PAGADA
            installment.amount = Decimal('0')

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
    # Recalcular el estado de TODAS las cuotas para asegurar consistencia
    total_amount_due = 0
    
    for installment in loan.installments:
        # Calcular cuánto se debe realmente de esta cuota
        # Sumar todos los pagos previos (excluyendo los del día actual que ya fueron eliminados)
        total_paid_for_installment = db.session.query(func.sum(Payment.amount)).filter(
            Payment.installment_id == installment.id,
            func.date(Payment.payment_date) != current_date
        ).scalar() or Decimal('0')
        
        # El monto adeudado es el monto fijo menos lo ya pagado
        amount_due_for_installment = installment.fixed_amount - total_paid_for_installment
        
        # Actualizar el estado y monto de la cuota según lo realmente pagado
        if amount_due_for_installment > 0:
            # Aún hay monto pendiente
            total_amount_due += amount_due_for_installment
            installment.amount = amount_due_for_installment
            
            # Actualizar el estado según si tiene pagos parciales
            if total_paid_for_installment > 0:
                installment.status = InstallmentStatus.ABONADA
            else:
                # Verificar si está en mora
                if installment.due_date and installment.due_date < current_date:
                    installment.status = InstallmentStatus.MORA
                else:
                    installment.status = InstallmentStatus.PENDIENTE
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
        
        # Verificar si realmente todas las cuotas están pagadas
        remaining_outstanding = sum(
            inst.amount for inst in loan.installments
            if inst.status in [InstallmentStatus.PENDIENTE, InstallmentStatus.ABONADA, InstallmentStatus.MORA]
            and inst.amount > 0
        )
        
        # Actualizar el estado del préstamo y el campo up_to_date
        if remaining_outstanding == 0:
            loan.status = False  # 0 indica que el préstamo está pagado en su totalidad
            loan.up_to_date = True
        else:
            # Aún hay cuotas pendientes, reactivar el préstamo
            loan.status = True
            loan.up_to_date = False
        
        loan.modification_date = datetime.now()
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
        
        # Verificar el estado final del préstamo después del pago parcial
        remaining_outstanding = sum(
            inst.amount for inst in loan.installments
            if inst.status in [InstallmentStatus.PENDIENTE, InstallmentStatus.ABONADA, InstallmentStatus.MORA]
            and inst.amount > 0
        )
        
        # Actualizar el estado del préstamo según si quedan cuotas pendientes
        if remaining_outstanding == 0:
            # Todas las cuotas están pagadas
            loan.status = False
            loan.up_to_date = True
        else:
            # Aún hay cuotas pendientes, asegurar que el préstamo esté activo
            loan.status = True
            loan.up_to_date = False
        
        loan.modification_date = datetime.now()
        client.debtor = False
        db.session.commit()

    # Redirigir a la vista de detalles de caja del empleado
    return redirect(url_for('routes.box_detail', employee_id=employee_id))



