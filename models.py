from enum import Enum

from app import db
import datetime
import json


# Definición de enumeración para el campo 'role' en User

class Role(Enum):
    ADMINISTRADOR = 1
    COORDINADOR = 2
    VENDEDOR = 3

    def to_json(self):
        return self.name


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
        return json.dumps(self.toJSON(), indent=4)


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

    def to_json(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'maximum_cash': str(self.maximum_cash),
            'maximum_sale': str(self.maximum_sale),
            'maximum_expense': str(self.maximum_expense),
            'maximum_payment': str(self.maximum_payment),
            'minimum_interest': str(self.minimum_interest),
            'percentage_interest': str(self.percentage_interest),
            'fix_value': str(self.fix_value),
            'creation_date': self.creation_date.isoformat(),
            'modification_date': self.modification_date.isoformat()
        }

    def __str__(self):
        return json.dumps(self.toJSON(), indent=4)


class Manager(db.Model):
    """ Modelo de Coordinador """

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), unique=True)

    employee = db.relationship('Employee', back_populates='manager')

    def to_json(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id
        }

    def __str__(self):
        return json.dumps(self.toJSON(), indent=4)


class Salesman(db.Model):
    """ Modelo de Vendedor """

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), unique=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('manager.id'), nullable=False, doc='Coordinador')

    employee = db.relationship('Employee', back_populates='salesman')
    manager = db.relationship('Manager', backref='salesmen')

    def to_json(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'manager_id': self.manager_id
        }

    def __str__(self):
        return json.dumps(self.toJSON(), indent=4)


class Gender(Enum):
    HOMBRE = 1
    MUJER = 2

    def to_json(self):
        return self.name


class Client(db.Model):
    """ Modelo de Cliente """

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(30), nullable=False, doc='Nombre')
    last_name = db.Column(db.String(30), nullable=False, doc='Apellido')
    alias = db.Column(db.String(100), nullable=False, doc='Alias')
    document = db.Column(db.String(20), unique=True, nullable=False, doc='Documento')
    gender = db.Column(db.Enum(Gender), nullable=False, doc='Genero')
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

    def to_json(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'alias': self.alias,
            'document': self.document,
            'gender': self.gender.toJSON(),
            'cellphone': self.cellphone,
            'address': self.address,
            'neighborhood': self.neighborhood,
            'status': self.status,
            'debtor': self.debtor,
            'black_list': self.black_list,
            'creation_date': self.creation_date.isoformat(),
            'modification_date': self.modification_date.isoformat()
        }

    def __str__(self):
        return json.dumps(self.toJSON(), indent=4)


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

    def to_json(self):
        return {
            'id': self.id,
            'amount': str(self.amount),
            'dues': str(self.dues),
            'interest': str(self.interest),
            'payment': str(self.payment),
            'status': self.status,
            'up_to_date': self.up_to_date,
            'creation_date': self.creation_date.isoformat(),
            'modification_date': self.modification_date.isoformat(),
            'client_id': self.client_id,
            'employee_id': self.employee_id
        }

    def __str__(self):
        return json.dumps(self.toJSON(), indent=4)


class TransactionType(Enum):
    GASTO = 1,
    INGRESO = 2,
    RETIRO = 3

    def to_json(self):
        return self.name


class Concept(db.Model):
    """ Modelo de Concepto """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, doc='Nombre')
    transaction_types = db.Column(db.Enum(TransactionType), nullable=False, doc='Tipo')

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'transaction_types': self.transaction_types.toJSON()
        }

    def __str__(self):
        return json.dumps(self.toJSON(), indent=4)


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

    def to_json(self):
        return {
            'id': self.id,
            'transaction_types': self.transaction_types.toJSON(),
            'concept_id': self.concept_id,
            'description': self.description,
            'mount': str(self.mount),
            'attachment': self.attachment,
            'status': self.status,
            'creation_date': self.creation_date.isoformat(),
            'modification_date': self.modification_date.isoformat(),
            'employee_id': self.employee_id
        }

    def __str__(self):
        return json.dumps(self.toJSON(), indent=4)