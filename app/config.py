# app/config.py

# Configuración de la base de datos
# SQLALCHEMY_DATABASE_URI = 'mysql://prestchile13:gpx5YvsLYj2#Pv@148.72.27.147/rutzchile'
SQLALCHEMY_DATABASE_URI = 'mysql://root:123456@localhost/wwrutz_chile'
SQLALCHEMY_TRACK_MODIFICATIONS = False


# Configuración avanzada de SQLAlchemy
SQLALCHEMY_ENGINE_OPTIONS = {
    
    'pool_pre_ping': True,
    'pool_recycle': 3600
}

# Otras configuraciones
DEBUG = True
SECRET_KEY = 'Lieberm0rder'
UPLOAD_FOLDER = '/static/images'
