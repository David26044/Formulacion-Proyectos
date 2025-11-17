# backend/app/__init__.py

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from .config import Config

# Declaración de extensiones (global)
# No se inicializan todavía, solo se “crean”
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app():
    # Crear instancia de Flask
    app = Flask(__name__)
    app.config.from_object(Config)

    # Habilitar CORS (permite que el frontend haga peticiones)
    CORS(app)

    # Inicializar extensiones con la app Flask
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # Importar modelos para que SQLAlchemy registre las tablas
    from . import models

    # Registrar Blueprints (rutas agrupadas por módulos)
    from .routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp)

    from .routes.weather_routes import weather_bp
    app.register_blueprint(weather_bp)

    from .routes.alerts_routes import alerts_bp
    app.register_blueprint(alerts_bp)

    # Ruta de prueba (opcional)
    @app.route("/")
    def home():
        return "✅ Flask conectado correctamente"

    print("📌 Rutas registradas en Flask:")
    for rule in app.url_map.iter_rules():
        print(f"👉 {rule}")

    return app
