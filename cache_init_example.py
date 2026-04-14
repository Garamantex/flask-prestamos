# =====================================================
# EJEMPLO DE INICIALIZACIÓN DEL CACHÉ
# =====================================================

# Archivo: app/__init__.py
# Agregar estas líneas para inicializar el caché

from flask import Flask
from app.routes import init_cache

def create_app():
    app = Flask(__name__)
    
    # Configuración de la aplicación
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'your-database-uri'
    
    # Inicializar extensiones
    from app.models import db
    db.init_app(app)
    
    # =====================================================
    # INICIALIZAR CACHÉ
    # =====================================================
    try:
        cache = init_cache(app)
        print("✅ Caché inicializado correctamente")
    except Exception as e:
        print(f"⚠️ Error al inicializar caché: {e}")
        print("La aplicación funcionará sin caché")
    
    # Registrar blueprints
    from app.routes import routes
    app.register_blueprint(routes)
    
    return app

# =====================================================
# ALTERNATIVA: INICIALIZACIÓN MANUAL
# =====================================================

# Si prefieres inicializar manualmente:
def init_cache_manually(app):
    """Inicialización manual del caché"""
    from flask_caching import Cache
    
    # Configuración del caché
    cache_config = {
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_HOST': 'localhost',
        'CACHE_REDIS_PORT': 6379,
        'CACHE_REDIS_DB': 0,
        'CACHE_DEFAULT_TIMEOUT': 300,
        'CACHE_KEY_PREFIX': 'flask_prestamos_',
        'CACHE_REDIS_URL': 'redis://localhost:6379/0'
    }
    
    # Inicializar caché
    cache = Cache()
    cache.init_app(app, config=cache_config)
    
    return cache

# =====================================================
# VERIFICACIÓN DEL CACHÉ
# =====================================================

def check_cache_status():
    """Verifica el estado del caché"""
    try:
        from flask import current_app
        if current_app and 'cache' in current_app.extensions:
            cache = current_app.extensions['cache']
            print(f"✅ Caché disponible: {type(cache)}")
            print(f"✅ Configuración: {cache.config}")
            return True
        else:
            print("❌ Caché no disponible")
            return False
    except Exception as e:
        print(f"❌ Error al verificar caché: {e}")
        return False

# =====================================================
# USO EN RUTAS
# =====================================================

# Para usar el caché en otras rutas:
def example_cached_function():
    """Ejemplo de función con caché"""
    from app.routes import safe_cache
    
    @safe_cache(timeout=300)
    def my_function(param1, param2):
        # Tu lógica aquí
        return f"Resultado para {param1} y {param2}"
    
    return my_function

# =====================================================
# COMANDOS DE VERIFICACIÓN
# =====================================================

# Verificar que Redis esté funcionando:
# redis-cli ping
# Debe responder: PONG

# Ver claves del caché:
# redis-cli keys "flask_prestamos_*"

# Limpiar caché manualmente:
# redis-cli flushdb
