Create user

open console python

from app import create_app
app = create_app()
app.app_context().push()
from sqlalchemy import text
from app import db
import datetime

stmt = text('''
    INSERT INTO User (username, password, role, first_name, last_name, cellphone, creation_date, modification_date)
    VALUES (:username, :password, :role, :first_name, :last_name, :cellphone, :creation_date, :modification_date)
''')

db.session.execute(stmt, {
    'username': 'admin',
    'password': '123456',
    'role': 'ADMINISTRADOR',
    'first_name': 'Andres',
    'last_name': 'Ramirez',
    'cellphone': '1234567890',
    'creation_date': datetime.datetime.utcnow(),
    'modification_date': datetime.datetime.utcnow()
})
db.session.commit()

