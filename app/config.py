# app/config.py
import os
from urllib.parse import quote_plus


def _as_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y", "on"}


# Permite usar URI completa desde entorno o construirla por piezas.
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
else:
    db_driver = os.getenv("DB_DRIVER", "mysql+pymysql")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "wwrutz_chile")
    db_user = os.getenv("DB_USER", "root")
    db_password = quote_plus(os.getenv("DB_PASSWORD", ""))
    SQLALCHEMY_DATABASE_URI = (
        f"{db_driver}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )

SQLALCHEMY_TRACK_MODIFICATIONS = False

SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,
    "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "3600")),
}

DEBUG = _as_bool(os.getenv("DEBUG"), default=True)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
UPLOAD_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "static",
    "images",
)
