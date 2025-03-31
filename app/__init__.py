from flask import Flask
from app.extensions import db, csrf, login_manager
from app.routes.clientes import clientes_bp
from app.routes.dashboard import dashboard_bp
from app.routes.insumos import insumos_bp
from app.routes.produccion import produccion_bp
from app.routes.proveedores import proveedores_bp
from app.routes.recetas import recetas_bp
from app.routes.usuarios import usuarios_bp
from app.routes.ventas import ventas_bp
from app.auth.auth import auth_bp
from app.models import Usuarios  # Importa el modelo Usuarios


def create_app():
    app = Flask(__name__)
    app.config.from_object('config.DevelopmentConfig')
    app.secret_key = app.config.get('dongalleto', 'clave_secreta_por_defecto')

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    # Configurar LoginManager
    login_manager.login_view = 'auth.login'  # Ruta para la página de inicio de sesión
    login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'

    # Registrar la función user_loader
    @login_manager.user_loader
    def load_user(user_id):
        return Usuarios.query.get(int(user_id))

    # Diccionario para intentos fallidos de inicio de sesión
    failed_attempts = {}

    app.register_blueprint(clientes_bp, url_prefix='/clientes')
    app.register_blueprint(dashboard_bp, url_prefix='/admin/dashboard')
    app.register_blueprint(insumos_bp, url_prefix='/admin/insumos')
    app.register_blueprint(produccion_bp, url_prefix='/admin/produccion')
    app.register_blueprint(proveedores_bp, url_prefix='/admin/proveedores')
    app.register_blueprint(recetas_bp, url_prefix='/admin/recetas')
    app.register_blueprint(usuarios_bp, url_prefix='/admin/usuarios')
    app.register_blueprint(ventas_bp, url_prefix='/admin/ventas')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    print(app.url_map)

    return app