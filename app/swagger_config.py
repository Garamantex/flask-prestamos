# app/swagger_config.py
# Configuración de Swagger/OpenAPI para la documentación de la API

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Flask Préstamos API",
        "description": "API para la gestión de préstamos, clientes, transacciones y cajas.",
        "version": "1.0.0",
        "contact": {
            "name": "Soporte"
        }
    },
    "basePath": "/",
    "schemes": ["http", "https"],
    "tags": [
        {
            "name": "Clientes",
            "description": "Operaciones relacionadas con clientes y préstamos"
        },
        {
            "name": "Usuarios",
            "description": "Gestión de usuarios y valores máximos"
        },
        {
            "name": "Transacciones",
            "description": "Gestión de transacciones, conceptos y morosos"
        },
        {
            "name": "Caja",
            "description": "Operaciones de cierre y registros de caja"
        }
    ]
}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: rule.endpoint.startswith('routes.'),
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}
