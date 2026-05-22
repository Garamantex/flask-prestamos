# app/routes/__init__.py
# Paquete de rutas - punto central de registro del blueprint

from flask import Blueprint

# Crear el blueprint principal (compartido por todos los módulos)
routes = Blueprint('routes', __name__)

# Importar todos los módulos de rutas para registrar sus endpoints
# (debe ir DESPUÉS de crear el blueprint para evitar imports circulares)
from app.routes import auth  # noqa: E402, F401
from app.routes import users  # noqa: E402, F401
from app.routes import clients  # noqa: E402, F401
from app.routes import payments  # noqa: E402, F401
from app.routes import box  # noqa: E402, F401
from app.routes import box_history  # noqa: E402, F401
from app.routes import transactions_routes  # noqa: E402, F401
from app.routes import wallet  # noqa: E402, F401
