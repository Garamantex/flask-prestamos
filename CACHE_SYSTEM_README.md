# 🚀 Sistema de Caché para Flask-Prestamos

## 📋 Descripción
Sistema de caché implementado con Redis para optimizar el rendimiento del endpoint `/box` y otras funciones críticas.

## 🏗️ Arquitectura

### **Backend de Caché**
- **Redis**: Base de datos en memoria para almacenamiento de caché
- **Flask-Caching**: Framework de caché para Flask
- **hiredis**: Driver optimizado de Redis

### **Estrategias de Caché**
- **Memoización**: Caché automático de funciones
- **Invalidación inteligente**: Limpieza selectiva del caché
- **Timeouts diferenciados**: Tiempos de expiración específicos por función

## ⚙️ Configuración

### **1. Instalación de Dependencias**
```bash
pip install -r cache_requirements.txt
```

### **2. Instalación de Redis**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# CentOS/RHEL
sudo yum install redis

# Docker
docker run -d -p 6379:6379 redis:alpine
```

### **3. Inicialización en la Aplicación**
```python
# En app/__init__.py
from app.routes import init_cache
cache = init_cache(app)
```

## 🎯 Funciones con Caché

### **Funciones Principales**
| Función | Timeout | Descripción |
|---------|---------|-------------|
| `get_coordinator_data()` | 10 min | Datos del coordinador y vendedores |
| `get_all_salesmen_data_optimized()` | 5 min | Datos optimizados de vendedores |
| `get_salesman_customers_data()` | 15 min | Datos de clientes |
| `get_salesman_pending_installments()` | 5 min | Cuotas pendientes |
| `check_all_loans_paid_today()` | 5 min | Préstamos pagados hoy |
| `get_salesman_collected_clients()` | 5 min | Clientes recaudados |
| `get_salesman_transaction_details()` | 3 min | Detalles de transacciones |
| `get_coordinator_expenses()` | 5 min | Gastos del coordinador |

### **Endpoint Principal**
- **`/box`**: 5 minutos de caché completo

## 🔧 Gestión del Caché

### **Endpoints de Administración**
```bash
# Limpiar todo el caché (solo administradores)
POST /cache/clear

# Limpiar caché de coordinador específico
POST /cache/clear/coordinator/{coordinator_id}

# Limpiar caché de vendedor específico
POST /cache/clear/salesman/{employee_id}

# Ver estadísticas del caché
GET /cache/stats
```

### **Invalidación Automática**
```python
# Invalidar caché de coordinador
invalidate_coordinator_cache(coordinator_id)

# Invalidar caché de vendedor
invalidate_salesman_cache(employee_id)
```

## 📊 Beneficios de Rendimiento

### **Mejoras Esperadas**
- **60-80% reducción** en tiempo de respuesta
- **85% menos consultas** a la base de datos
- **Escalabilidad mejorada** para múltiples usuarios
- **Reducción de carga** en el servidor de base de datos

### **Métricas de Caché**
- **Hit Rate**: Porcentaje de consultas servidas desde caché
- **Miss Rate**: Porcentaje de consultas que requieren base de datos
- **Response Time**: Tiempo de respuesta promedio
- **Memory Usage**: Uso de memoria de Redis

## 🔍 Monitoreo

### **Comandos de Redis**
```bash
# Ver información general
redis-cli info

# Ver claves del caché
redis-cli keys "flask_prestamos_*"

# Ver memoria usada
redis-cli info memory

# Limpiar caché manualmente
redis-cli flushdb
```

### **Logs de Caché**
```python
# Habilitar logs de caché
import logging
logging.getLogger('flask_caching').setLevel(logging.DEBUG)
```

## 🚨 Consideraciones de Producción

### **Configuración de Redis**
```conf
# redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### **Monitoreo de Salud**
- **Redis Health Check**: Verificar que Redis esté funcionando
- **Memory Usage**: Monitorear uso de memoria
- **Connection Pool**: Gestionar conexiones a Redis
- **Error Handling**: Manejo de errores de conexión

### **Backup y Recuperación**
```bash
# Backup de Redis
redis-cli --rdb /backup/redis-backup.rdb

# Restaurar desde backup
redis-cli --rdb /backup/redis-backup.rdb
```

## 🔧 Troubleshooting

### **Problemas Comunes**

#### **1. Redis no disponible**
```bash
# Verificar estado
redis-cli ping

# Iniciar Redis
sudo systemctl start redis
```

#### **2. Caché no funciona**
```python
# Verificar configuración
print(cache.config)

# Limpiar caché
cache.clear()
```

#### **3. Memoria insuficiente**
```bash
# Ver uso de memoria
redis-cli info memory

# Limpiar caché
redis-cli flushdb
```

## 📈 Optimizaciones Futuras

### **Caché Distribuido**
- **Redis Cluster**: Para múltiples servidores
- **Memcached**: Alternativa a Redis
- **CDN**: Caché de contenido estático

### **Caché Inteligente**
- **Machine Learning**: Predicción de patrones de acceso
- **Adaptive Timeouts**: Timeouts dinámicos
- **Cache Warming**: Pre-carga de datos frecuentes

### **Monitoreo Avanzado**
- **APM Integration**: Integración con herramientas de monitoreo
- **Alertas**: Notificaciones de problemas de caché
- **Dashboards**: Visualización de métricas

## 📚 Referencias

- [Flask-Caching Documentation](https://flask-caching.readthedocs.io/)
- [Redis Documentation](https://redis.io/documentation)
- [Redis Best Practices](https://redis.io/docs/manual/patterns/)
- [Caching Strategies](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/Strategies.html)
