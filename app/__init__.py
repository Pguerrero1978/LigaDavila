from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import config
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Debes iniciar sesión para acceder.'
login_manager.login_message_category = 'warning'


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # Crear carpeta de uploads si no existe
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Registrar blueprints
    from app.routes.public import public_bp
    from app.routes.noticias import noticias_bp
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.jugadores import jugadores_bp
    from app.routes.series import series_bp
    from app.routes.equipos import equipos_bp
    from app.routes.partidos import partidos_bp
    from app.routes.actividad import actividad_bp
    from app.routes.goleadores import goleadores_bp
    from app.routes.tabla import tabla_bp
    from app.routes.carga_masiva import carga_masiva_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(noticias_bp, url_prefix='/admin/noticias')
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp, url_prefix='/admin')
    app.register_blueprint(jugadores_bp, url_prefix='/admin/jugadores')
    app.register_blueprint(series_bp, url_prefix='/admin/series')
    app.register_blueprint(equipos_bp, url_prefix='/admin/equipos')
    app.register_blueprint(partidos_bp, url_prefix='/admin/partidos')
    app.register_blueprint(actividad_bp, url_prefix='/admin/actividad')
    app.register_blueprint(goleadores_bp, url_prefix='/admin/goleadores')
    app.register_blueprint(tabla_bp, url_prefix='/admin/tabla')
    app.register_blueprint(carga_masiva_bp, url_prefix='/admin/carga')

    # Filtros Jinja2 personalizados
    from datetime import date

    @app.template_filter('edad')
    def edad_filter(fecha_nac):
        if not fecha_nac:
            return '-'
        hoy = date.today()
        edad = hoy.year - fecha_nac.year
        if (hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day):
            edad -= 1
        return edad

    @app.template_filter('initials')
    def initials_filter(nombre):
        if not nombre:
            return '?'
        parts = nombre.strip().split()
        return (parts[0][0] + (parts[1][0] if len(parts) > 1 else '')).upper()

    return app
