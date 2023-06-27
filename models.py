from enum import Enum

from app import db
import datetime


# Definición de enumeración para el campo 'role' en User
# roles = db.Enum('Administrador', 'Coordinador', 'Vendedor')
class Role(Enum):
    ADMINISTRATOR = 1
    COORDINATOR = 2
    SELLER = 3


class User(db.Model):
    """Modelo de Usuario"""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Enum(Role), nullable=False, doc='Rol')
    first_name = db.Column(db.String(30), nullable=False, doc='Nombre')
    last_name = db.Column(db.String(30), nullable=False, doc='Apellido')
    cellphone = db.Column(db.String(20), nullable=False, doc='Celular')
    creation_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    modification_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow,
                                  onupdate=datetime.datetime.utcnow)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Employee(db.Model):
    """ Modelo de Empleado """

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True, doc='Usuario')
    maximum_cash = db.Column(db.Numeric(10, 2), nullable=False, doc='Máxima caja')
    maximum_sale = db.Column(db.Numeric(10, 2), nullable=False, doc='Máxima venta')
    maximum_expense = db.Column(db.Numeric(10, 2), nullable=False, doc='Límite gasto')
    maximum_payment = db.Column(db.Numeric(10, 2), nullable=False, doc='Máximo pago')
    minimum_interest = db.Column(db.Numeric(10, 2), nullable=False, doc='Mínimo interés')
    percentage_interest = db.Column(db.Numeric(10, 2), nullable=False, doc='Porcentaje interés')
    fix_value = db.Column(db.Numeric(10, 2), nullable=False, doc='Valor fijo')
    creation_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    modification_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow,
                                  onupdate=datetime.datetime.utcnow)

    user = db.relationship('User', backref='employee', uselist=False)
    manager = db.relationship('Manager', uselist=False, back_populates='employee')
    salesman = db.relationship('Salesman', uselist=False, back_populates='employee')

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class Manager(db.Model):
    """ Modelo de Coordinador """

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), unique=True)

    employee = db.relationship('Employee', back_populates='manager')

    def __str__(self):
        return f"{self.employee.user.first_name} {self.employee.user.last_name}"


class Salesman(db.Model):
    """ Modelo de Vendedor """

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), unique=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('manager.id'), nullable=False, doc='Coordinador')

    employee = db.relationship('Employee', back_populates='salesman')
    manager = db.relationship('Manager', backref='salesmen')

    def __str__(self):
        return f"{self.employee.user.first_name} {self.employee.user.last_name}"


genders = db.Enum('Hombre', 'Mujer')


class Client(db.Model):
    """ Modelo de Cliente """

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(30), nullable=False, doc='Nombre')
    last_name = db.Column(db.String(30), nullable=False, doc='Apellido')
    alias = db.Column(db.String(100), nullable=False, doc='Alias')
    document = db.Column(db.String(20), unique=True, nullable=False, doc='Documento')
    gender = db.Column(genders, nullable=False, doc='Género')
    cellphone = db.Column(db.String(20), nullable=False, doc='Celular')
    address = db.Column(db.String(100), nullable=False, doc='Dirección')
    neighborhood = db.Column(db.String(100), nullable=False, doc='Barrio')
    status = db.bollean(default=True, nullable=False, doc='Estado')
    debtor = db.bollean(default=False, nullable=False, doc='Deudor')
    black_list = db.bollean(default=False, nullable=False, doc='Lista Negra')
    creation_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    modification_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow,
                                  onupdate=datetime.datetime.utcnow)

    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class Loan(db.Model):
    """ Modelo de Prestamo """

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False, doc='Monto')
    dues = db.Column(db.Numeric(10, 2), nullable=False, doc='Cuotas')
    interest = db.Column(db.Numeric(10, 2), nullable=False, doc='Interés')
    payment = db.Column(db.Numeric(10, 2), nullable=False, doc='Pago')
    status = db.bollean(default=True, nullable=False, doc='Estado')
    up_to_date = db.bollean(default=False, nullable=False, doc='Al día')
    creation_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    modification_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow,
                                  onupdate=datetime.datetime.utcnow)

    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)

    def __str__(self):
        return f"{self.client.user.first_name} {self.client.user.last_name}"


class TransactionType(Enum):
    GASTO = 1,
    INGRESO = 2,
    RETIRO = 3


class Concept(db.Model):
    """ Modelo de Concepto """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, doc='Nombre')
    transaction_types = db.Column(db.Enum(TransactionType), nullable=False, doc='Tipo')


class Transaction(db.Model):
    """ Modelo de Transacción  """

    id = db.Column(db.Integer, primary_key=True)
    transaction_types = db.Column(db.Enum(TransactionType), nullable=False, doc='Tipo')
    concept_id = db.Column(db.Integer, db.ForeignKey('concept.id'), nullable=False)
    description = db.Column(db.String(100), nullable=False, doc='Descripción')
    mount = db.Column(db.Numeric(10, 2), nullable=False, doc='Monto')
    attachment = db.Column(db.String(100), nullable=True, doc='Adjunto')
    status = db.bollean(default=False, nullable=False, doc='Estado')

    concept = db.relationship('Concept', backref='transaction', uselist=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)

    creation_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    modification_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow,
                                  onupdate=datetime.datetime.utcnow)
