from flask import Flask

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('config.py')

    # Inicializar la instancia de SQLAlchemy
    db.init_app(app)

    # Configurar la migración de la base de datos
    from flask_migrate import Migrate
    migrate = Migrate(app, db)

    # Importar y registrar las rutas
    from app.routes import routes
    app.register_blueprint(routes)

    # Importar y registrar los modelos
    from app.models import User, Client, Loan

    # Crear las tablas en la base de datos
    with app.app_context():
        db.create_all()

    return app
