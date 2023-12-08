**Create user**

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

**Delete database**

delete folder 
    - instance
    - migrations

open console python

from app import create_app
app = create_app()
app.app_context().push()
from sqlalchemy import text
from app import db
stmt = text('DROP TABLE client')
db.session.execute(stmt)
tmt = text('DROP TABLE loan')
db.session.execute(stmt)
tmt = text('DROP TABLE loan_installment')
db.session.execute(stmt)
db.session.commit()

// Fuera de la consola de python

flask db init
flask db migrate
flask db upgrade
