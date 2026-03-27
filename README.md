# Flask Prestamos - Ejecucion con Docker

Este proyecto ahora puede ejecutarse completamente con Docker (`Flask + MySQL`) sin XAMPP.

## 1) Requisitos

- Docker Desktop (o Docker Engine + Docker Compose plugin)

## 2) Levantar el entorno

Desde la raiz del proyecto:

```bash
docker compose up --build
```

Servicios:

- `web`: app Flask en modo desarrollo (`flask run --host=0.0.0.0 --port=5000`)
- `db`: MySQL 8 con volumen persistente `mysql_data`
- `phpmyadmin`: administrador web para MySQL

Acceso web:

- [http://localhost:5000](http://localhost:5000)
- [http://localhost:8080](http://localhost:8080) (`phpMyAdmin`)

## 3) Variables de entorno (opcional)

Si quieres personalizar credenciales/puertos, crea un archivo `.env` en la raiz:

```env
MYSQL_DATABASE=wwrutz_chile
MYSQL_USER=prestamos_user
MYSQL_PASSWORD=prestamos_pass
MYSQL_ROOT_PASSWORD=root
DB_PORT_HOST=3307
FLASK_PORT=5000
PHPMYADMIN_PORT=8080
SECRET_KEY=dev-secret-key
FLASK_DEBUG=1
```

Si no existe `.env`, Docker usa defaults definidos en `docker-compose.yml`.

## 4) Migraciones

Con los contenedores arriba, ejecuta:

```bash
docker compose exec web flask db upgrade
```

Si es la primera vez y no existe carpeta `migrations/`:

```bash
docker compose exec web flask db init
docker compose exec web flask db migrate
docker compose exec web flask db upgrade
```

## 5) Crear usuario administrador

Abre shell Python dentro del contenedor:

```bash
docker compose exec web python
```

Luego ejecuta:

```python
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
```

## 6) Comandos utiles

Ver logs:

```bash
docker compose logs -f web
docker compose logs -f db
docker compose logs -f phpmyadmin
```

Parar servicios:

```bash
docker compose down
```

Parar y borrar volumen (reinicio total de BD):

```bash
docker compose down -v
```

## 7) Troubleshooting rapido

- Si `5000` esta ocupado, cambia `FLASK_PORT` en `.env`.
- Si `3307` esta ocupado, cambia `DB_PORT_HOST` en `.env`.
- Si `8080` esta ocupado, cambia `PHPMYADMIN_PORT` en `.env`.
- Si Flask no conecta a MySQL al iniciar, revisa:
  - `docker compose ps`
  - `docker compose logs -f db`
  - que las variables `MYSQL_*` y `DB_*` coincidan.
- Login de `phpMyAdmin`:
  - Servidor: `db`
  - Usuario: valor de `MYSQL_USER` (default `prestamos_user`) o `root`
  - Password: `MYSQL_PASSWORD` o `MYSQL_ROOT_PASSWORD`
