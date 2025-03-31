from app.routes.clientes import clientes_bp
from app.routes.insumos import insumos_bp
from app.routes.produccion import produccion_bp
from app.routes.recetas import recetas_bp
from app.routes.usuarios import usuarios_bp
from app.routes.ventas import ventas_bp

blueprints = [
    (clientes_bp, '/clientes'),
    (insumos_bp, '/insumos'),
    (produccion_bp, '/produccion'),
    (recetas_bp, '/recetas'),
    (usuarios_bp, '/usuarios'),
    (ventas_bp, '/ventas'),
]