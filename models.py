from app import db
import datetime

# Definición de enumeración para el campo 'role' en User
roles = db.Enum('administrador', 'coordinador', 'vendedor', 'cliente')


class User(db.Model):
    """Modelo de Usuario"""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(roles, nullable=False)
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


class Client(db.Model):
    """ Modelo de Cliente """

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, doc='Correo electrónico')
    document = db.Column(db.String(20), unique=True, nullable=False, doc='Documento')
    address = db.Column(db.String(100), nullable=False, doc='Dirección')
    reference = db.Column(db.String(100), nullable=False, doc='Referencia')
    creation_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    modification_date = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow,
                                  onupdate=datetime.datetime.utcnow)

    user = db.relationship('User', backref='client', uselist=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
