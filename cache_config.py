# =====================================================
# CONFIGURACIÓN DE CACHÉ PARA FLASK-PRESTAMOS
# =====================================================

import os
from datetime import timedelta

class CacheConfig:
    """Configuración del sistema de caché"""
    
    # Configuración base
    CACHE_TYPE = 'redis'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutos por defecto
    CACHE_KEY_PREFIX = 'flask_prestamos_'
    
    # Configuración de Redis
    CACHE_REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    CACHE_REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    CACHE_REDIS_DB = int(os.getenv('REDIS_DB', 0))
    CACHE_REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    
    # URL de conexión a Redis
    CACHE_REDIS_URL = f"redis://{CACHE_REDIS_HOST}:{CACHE_REDIS_PORT}/{CACHE_REDIS_DB}"
    
    # Timeouts específicos por función
    CACHE_TIMEOUTS = {
        'coordinator_data': 600,        # 10 minutos
        'salesmen_data': 300,           # 5 minutos
        'customers_data': 900,          # 15 minutos
        'pending_installments': 300,    # 5 minutos
        'loans_paid_today': 300,        # 5 minutos
        'collected_clients': 300,       # 5 minutos
        'transaction_details': 180,     # 3 minutos
        'coordinator_expenses': 300,    # 5 minutos
        'box_endpoint': 300,            # 5 minutos
    }
    
    # Configuración de invalidación
    CACHE_INVALIDATION = {
        'auto_invalidate': True,        # Invalidación automática
        'invalidate_on_update': True,   # Invalidar al actualizar datos
        'invalidate_patterns': True,    # Usar patrones para invalidación
    }
    
    # Configuración de monitoreo
    CACHE_MONITORING = {
        'enable_stats': True,           # Habilitar estadísticas
        'log_hits': True,              # Registrar hits del caché
        'log_misses': True,            # Registrar misses del caché
        'performance_tracking': True,   # Seguimiento de rendimiento
    }

# Configuración para desarrollo
class DevelopmentCacheConfig(CacheConfig):
    """Configuración de caché para desarrollo"""
    CACHE_DEFAULT_TIMEOUT = 60  # 1 minuto en desarrollo
    CACHE_REDIS_HOST = 'localhost'
    CACHE_REDIS_PORT = 6379
    CACHE_REDIS_DB = 1  # Base de datos diferente para desarrollo

# Configuración para producción
class ProductionCacheConfig(CacheConfig):
    """Configuración de caché para producción"""
    CACHE_DEFAULT_TIMEOUT = 600  # 10 minutos en producción
    CACHE_REDIS_HOST = os.getenv('REDIS_HOST', 'redis-server')
    CACHE_REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    CACHE_REDIS_DB = 0
    CACHE_REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
    
    # Configuración optimizada para producción
    CACHE_REDIS_SOCKET_KEEPALIVE = True
    CACHE_REDIS_SOCKET_KEEPALIVE_OPTIONS = {
        1: 1,  # TCP_KEEPIDLE
        2: 3,  # TCP_KEEPINTVL
        3: 5,  # TCP_KEEPCNT
    }

# Configuración para testing
class TestingCacheConfig(CacheConfig):
    """Configuración de caché para testing"""
    CACHE_TYPE = 'simple'  # Caché en memoria para testing
    CACHE_DEFAULT_TIMEOUT = 1  # 1 segundo para testing
    CACHE_REDIS_DB = 15  # Base de datos de testing

# Función para obtener configuración según el entorno
def get_cache_config(environment='development'):
    """Obtiene la configuración de caché según el entorno"""
    configs = {
        'development': DevelopmentCacheConfig(),
        'production': ProductionCacheConfig(),
        'testing': TestingCacheConfig(),
    }
    
    return configs.get(environment, DevelopmentCacheConfig())

# =====================================================
# CONFIGURACIÓN DE VARIABLES DE ENTORNO
# =====================================================
# Crear archivo .env con:
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REDIS_DB=0
# REDIS_PASSWORD=your_password_here
# CACHE_ENVIRONMENT=development

# =====================================================
# USO EN LA APLICACIÓN
# =====================================================
# from cache_config import get_cache_config
# cache_config = get_cache_config(os.getenv('CACHE_ENVIRONMENT', 'development'))
# cache.init_app(app, config=cache_config.__dict__)
