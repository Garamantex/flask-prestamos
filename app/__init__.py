# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app(use_hosting_db=False):
    app = Flask(__name__)
    app.config.from_pyfile('config.py')
    
    # Elegir la base de datos a usar
    if use_hosting_db:
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI_HOSTING']
    
    # Aplicar opciones avanzadas del motor
    engine_options = app.config.get('SQLALCHEMY_ENGINE_OPTIONS', {})
    for key, value in engine_options.items():
        app.config['SQLALCHEMY_' + key.upper()] = value
    
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

    return app