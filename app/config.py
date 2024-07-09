# app/config.py

# Configuración de la base de datos
SQLALCHEMY_DATABASE_URI = 'mysql://root:123456@localhost/rutzchile'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Configuración de la base de datos de hosting
SQLALCHEMY_DATABASE_URI_HOSTING = 'mysql://prestchile13:3AHV4D0PS1s-@148.72.27.147/rutzchile'

# Configuración avanzada de SQLAlchemy
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 3600
}

# Otras configuraciones
DEBUG = True
SECRET_KEY = 'Lieberm0rder' 
UPLOAD_FOLDER = '/static/images'