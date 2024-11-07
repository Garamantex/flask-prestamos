from enum import Enum
import datetime
import json
from app import db

# Definición de enumeración para el campo 'role' en User


class Role(Enum):
    ADMINISTRADOR = "ADMINISTRADOR"
    COORDINADOR = "COORDINADOR"
    VENDEDOR = "VENDEDOR"

    def to_json(self):
        return self.name


class User(db.Model):
    """Modelo de Usuario"""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Enum(Role), nullable=False, doc='Role')
    first_name = db.Column(db.String(30), nullable=False, doc='Nombre')
    last_name = db.Column(db.String(30), nullable=False, doc='Apellido')
    cellphone = db.Column(db.String(20), nullable=False, doc='Celular')
    creation_date = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.now)
    modification_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now,
                                  onupdate=datetime.datetime.now)

    def to_json(self):
        return {
            'id': self.id,
            'username': self.username,
            'password': self.password,
            'role': self.role.toJSON(),
            'first_name': self.first_name,
            'last_name': self.last_name,
            'cellphone': self.cellphone,
            'creation_date': self.creation_date.isoformat(),
            'modification_date': self.modification_date.isoformat()
        }

    def __str__(self):
        return json.dumps(self.to_json(), indent=4)


class Employee(db.Model):
    """ Modelo de Empleado """

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.id'), nullable=False, unique=True, doc='Usuario')
    maximum_cash = db.Column(db.Numeric(
        10, 2), nullable=False, doc='Máxima caja')
    maximum_sale = db.Column(db.Numeric(
        10, 2), nullable=False, doc='Máxima venta')
    box_value = db.Column(db.Numeric(10, 2), nullable=False, doc='Valor caja')
    maximum_expense = db.Column(db.Numeric(
        10, 2), nullable=False, doc='Límite gasto')
    maximum_installments = db.Column(db.Numeric(
        10, 2), nullable=False, doc='Máximo de cuotas')
    minimum_interest = db.Column(db.Numeric(
        10, 2), nullable=False, doc='Mínimo interés')
    status = db.Column(db.Boolean, default=True, nullable=False, doc='Estado')
    percentage_interest = db.Column(db.Numeric(
        10, 2), nullable=False, doc='Porcentaje interés')
    fix_value = db.Column(db.Numeric(10, 2), nullable=True, doc='Valor fijo')
    creation_date = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.now)
    modification_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now,
                                  onupdate=datetime.datetime.now)

    user = db.relationship('User', backref='employee', uselist=False)
    manager = db.relationship('Manager', uselist=False,
                              back_populates='employee')
    salesman = db.relationship(
        'Salesman', uselist=False, back_populates='employee')

    # Definir la relación inversa para acceder a los clientes de un empleado
    clients = db.relationship('Client', backref='employee', lazy=True)

    def to_json(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'maximum_cash': str(self.maximum_cash),
            'maximum_sale': str(self.maximum_sale),
            'maximum_expense': str(self.maximum_expense),
            'maximum_installments': str(self.maximum_installments),
            'minimum_interest': str(self.minimum_interest),
            'percentage_interest': str(self.percentage_interest),
            'fix_value': str(self.fix_value),
            'creation_date': self.creation_date.isoformat(),
            'modification_date': self.modification_date.isoformat()
        }

    def __str__(self):
        return json.dumps(self.to_json(), indent=4)


class Manager(db.Model):
    """ Modelo de Coordinador """

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(
        db.Integer, db.ForeignKey('employee.id'), unique=True)

    employee = db.relationship('Employee', back_populates='manager')

    def to_json(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id
        }

    def __str__(self):
        return json.dumps(self.to_json(), indent=4)


class Salesman(db.Model):
    """ Modelo de Vendedor """

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(
        db.Integer, db.ForeignKey('employee.id'), unique=True)
    manager_id = db.Column(db.Integer, db.ForeignKey(
        'manager.id'), nullable=False, doc='Coordinador')

    employee = db.relationship('Employee', back_populates='salesman')
    manager = db.relationship('Manager', backref='salesmen')

    def to_json(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'manager_id': self.manager_id
        }

    def __str__(self):
        return json.dumps(self.to_json(), indent=4)


class Client(db.Model):
    """ Modelo de Cliente """

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(30), nullable=False, doc='Nombre')
    last_name = db.Column(db.String(30), nullable=False, doc='Apellido')
    alias = db.Column(db.String(100), nullable=False, doc='Alias')
    document = db.Column(db.String(20), unique=True,
                         nullable=False, doc='Documento')
    cellphone = db.Column(db.String(20), nullable=False, doc='Celular')
    address = db.Column(db.String(100), nullable=False, doc='Dirección')
    neighborhood = db.Column(db.String(100), nullable=False, doc='Barrio')
    status = db.Column(db.Boolean, default=True, nullable=False, doc='Estado')
    debtor = db.Column(db.Boolean, default=False, nullable=False, doc='Deudor')
    black_list = db.Column(db.Boolean, default=False,
                           nullable=False, doc='Lista Negra')
    creation_date = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.now)
    modification_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now,
                                  onupdate=datetime.datetime.now)
    first_modification_date = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.now)

    employee_id = db.Column(
        db.Integer, db.ForeignKey('employee.id'), nullable=True)

    loans = db.relationship('Loan', backref='client', lazy=True)

    def to_json(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'alias': self.alias,
            'document': self.document,
            'cellphone': self.cellphone,
            'address': self.address,
            'neighborhood': self.neighborhood,
            'status': self.status,
            'debtor': self.debtor,
            'black_list': self.black_list,
            'creation_date': self.creation_date.isoformat(),
            'modification_date': self.modification_date.isoformat(),
            'first_modification_date': self.first_modification_date.isoformat() if self.first_modification_date else None
        }

    def __str__(self):
        return json.dumps(self.to_json(), indent=4)


class Loan(db.Model):
    """ Modelo de Prestamo """

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False, doc='Monto')
    dues = db.Column(db.Numeric(10, 2), nullable=False, doc='Cuotas')
    interest = db.Column(db.Numeric(10, 2), nullable=False, doc='Interés')
    payment = db.Column(db.Numeric(10, 2), nullable=False, doc='Pago')
    status = db.Column(db.Boolean, default=True, nullable=False, doc='Estado')
    approved = db.Column(db.Boolean, default=True,
                         nullable=False, doc='Aprobado')
    up_to_date = db.Column(db.Boolean, default=False,
                           nullable=False, doc='Al día')
    is_renewal = db.Column(db.Boolean, default=False,
                           nullable=False, doc='Renovación')
    creation_date = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.now)
    modification_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now,
                                  onupdate=datetime.datetime.now)

    client_id = db.Column(db.Integer, db.ForeignKey(
        'client.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey(
        'employee.id'), nullable=False)

    installments = db.relationship(
        'LoanInstallment', backref='loan', cascade='all, delete-orphan')

    def to_json(self):
        return {
            'id': self.id,
            'amount': str(self.amount),
            'dues': str(self.dues),
            'interest': str(self.interest),
            'payment': str(self.payment),
            'status': self.status,
            'approved': self.approved,
            'up_to_date': self.up_to_date,
            'creation_date': self.creation_date.isoformat(),
            'modification_date': self.modification_date.isoformat(),
            'client_id': self.client_id,
            'employee_id': self.employee_id
        }

    def __str__(self):
        return json.dumps(self.to_json(), indent=4)


class InstallmentStatus(Enum):
    PENDIENTE = "PENDIENTE"
    PAGADA = "PAGADA"
    ABONADA = "ABONADA"
    MORA = "MORA"

    def to_json(self):
        return self.name


class Payment(db.Model):
    """ Modelo de Pago """

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False, doc='Monto del pago')
    payment_date = db.Column(db.DateTime, nullable=False,
                             default=datetime.datetime.now, doc='Fecha de pago')
    installment_id = db.Column(db.Integer, db.ForeignKey(
        'loan_installment.id'), nullable=False)

    def to_json(self):
        return {
            'id': self.id,
            'amount': str(self.amount),
            'payment_date': self.payment_date.isoformat(),
            'installment_id': self.installment_id
        }

    def __str__(self):
        return json.dumps(self.to_json(), indent=4)


class LoanInstallment(db.Model):
    """ Modelo de Cuota de Préstamo """

    id = db.Column(db.Integer, primary_key=True)
    installment_number = db.Column(
        db.Integer, nullable=False, doc='Número de cuota')
    due_date = db.Column(db.Date, nullable=False, doc='Fecha de vencimiento')
    amount = db.Column(db.Numeric(10, 2), nullable=False,
                       doc='Monto de la cuota')
    fixed_amount = db.Column(db.Numeric(
        10, 2), nullable=False, doc='Cuota Fija')
    status = db.Column(db.Enum(InstallmentStatus),
                       default=InstallmentStatus.PENDIENTE, nullable=False, doc='status')
    payment_date = db.Column(db.Date, nullable=True, doc='Fecha de pago')
    loan_id = db.Column(db.Integer, db.ForeignKey('loan.id'), nullable=False)

    payments = db.relationship(
        'Payment', backref='installment', cascade='all, delete-orphan')

    def to_json(self):
        return {
            'id': self.id,
            'installment_number': self.installment_number,
            'due_date': self.due_date.isoformat(),
            'amount': str(self.amount),
            'status': self.status.value,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'loan_id': self.loan_id,
            'payments': [payment.to_json() for payment in self.payments]
        }

    def __str__(self):
        return json.dumps(self.to_json(), indent=4)

    def is_in_arrears(self):
        # and self.due_date <= datetime.date.today()
        return self.status == InstallmentStatus.MORA


class TransactionType(Enum):
    GASTO = "GASTO"
    INGRESO = "INGRESO"
    RETIRO = "RETIRO"

    def to_json(self):
        return self.name


# Enumeración para representar los estados de aprobación
class ApprovalStatus(Enum):
    PENDIENTE = "PENDIENTE"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"


class Concept(db.Model):
    """ Modelo de Concepto """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, doc='Nombre')
    transaction_types = db.Column(
        db.Enum(TransactionType), nullable=False, doc='Tipo')

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'transaction_types': self.transaction_types.name
        }

    def __str__(self):
        return json.dumps(self.to_json(), indent=4)


# Clase que representa el modelo de Transacción
class Transaction(db.Model):
    """ Modelo de Transacción """

    id = db.Column(db.Integer, primary_key=True)
    transaction_types = db.Column(
        db.Enum(TransactionType), nullable=False, doc='Tipo')
    concept_id = db.Column(db.Integer, db.ForeignKey(
        'concept.id'), nullable=False)
    description = db.Column(db.String(100), nullable=False, doc='Descripción')
    amount = db.Column(db.Numeric(10, 2), nullable=False, doc='Monto')
    attachment = db.Column(db.String(100), nullable=True, doc='Adjunto')
    loan_id = db.Column(db.Integer, db.ForeignKey(
        'loan.id'), nullable=True, doc='Préstamo')
    approval_status = db.Column(db.Enum(ApprovalStatus), default=ApprovalStatus.PENDIENTE, nullable=False,
                                doc='Estado de Aprobación')

    concept = db.relationship('Concept', backref='transaction', uselist=False)
    employee_id = db.Column(db.Integer, db.ForeignKey(
        'employee.id'), nullable=False)

    creation_date = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.now)
    modification_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.now,
                                  onupdate=datetime.datetime.now)

    def to_json(self):
        return {
            'id': self.id,
            'transaction_types': self.transaction_types.name,
            'concept_id': self.concept_id,
            'description': self.description,
            'amount': str(self.amount),
            'attachment': self.attachment,
            # Corregido para reflejar el nombre del campo
            'approval_status': self.approval_status.name,
            'creation_date': self.creation_date.isoformat(),
            'modification_date': self.modification_date.isoformat(),
            'employee_id': self.employee_id
        }

    def __str__(self):
        return json.dumps(self.to_json(), indent=4)


class EmployeeRecord(db.Model):
    """Modelo para registrar la información de caja y préstamos de un empleado"""

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey(
        'employee.id'), nullable=False)
    initial_state = db.Column(db.Float, nullable=False)
    loans_to_collect = db.Column(db.Integer, nullable=False)
    paid_installments = db.Column(db.Integer, nullable=False)
    partial_installments = db.Column(db.Integer, nullable=False)
    due_to_collect_tomorrow = db.Column(db.Float, nullable=False)
    overdue_installments = db.Column(db.Integer, nullable=False)
    total_collected = db.Column(db.Float, nullable=False)
    sales = db.Column(db.Float, nullable=False)
    renewals = db.Column(db.Float, nullable=False)
    incomings = db.Column(db.Float, nullable=False)
    withdrawals = db.Column(db.Float, nullable=False)
    expenses = db.Column(db.Float, nullable=False)
    closing_total = db.Column(db.Float, nullable=False)
    creation_date = db.Column(db.DateTime, default=datetime.datetime.now)

    # Relación con el modelo Employee
    employee = db.relationship(
        'Employee', backref=db.backref('employee_records', lazy=True))

    def to_json(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'initial_state': self.initial_state,
            'loans_to_collect': self.loans_to_collect,
            'paid_installments': self.paid_installments,
            'partial_installments': self.partial_installments,
            'overdue_installments': self.overdue_installments,
            'due_to_collect_tomorrow': self.due_to_collect_tomorrow,
            'total_collected': self.total_collected,
            'sales': self.sales,
            'renewals': self.renewals,
            'incomings': self.incomings,
            'withdrawals': self.withdrawals,
            'expenses': self.expenses,
            'closing_total': self.closing_total,
            'creation_date': self.creation_date.isoformat()
        }

    def __str__(self):
        return json.dumps(self.to_json(), indent=4)
