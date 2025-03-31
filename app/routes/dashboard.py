from flask import Blueprint, render_template, session
from flask_login import login_required, current_user
from app.models import VentasCliente
from app.utils import role_required
from app.extensions import csrf, db
#from app import db

# Definir el Blueprint
dashboard_bp = Blueprint('dashboard', __name__, template_folder='../templates/admin')

# Ruta para el dashboard
@dashboard_bp.route("/dashboard", methods=["GET"])
@login_required
@role_required(['Admin', 'Ventas'])
def dashboard():
    carrito = session.get("carrito", [])
    ventas_clientes = db.session.query(
        VentasCliente.nombreCliente,
        VentasCliente.nombreSabor,
        VentasCliente.tipoProducto,
        VentasCliente.cantidad,
        VentasCliente.total
    ).filter(VentasCliente.estatus == 1).all()

    todas_las_ventas = []

    # Agregar las ventas del carrito
    for item in carrito:
        todas_las_ventas.append({
            "nombreCliente": current_user.nombre,
            "nombreSabor": item["nombre"],
            "tipoProducto": item["tipo"],
            "cantidad": item["cantidad"],
            "total": item["cantidad"] * item["precio"],
            "metodo": "Carrito"
        })

    # Agregar las ventas de la base de datos
    for venta in ventas_clientes:
        todas_las_ventas.append({
            "nombreCliente": venta.nombreCliente,
            "nombreSabor": venta.nombreSabor,
            "tipoProducto": venta.tipoProducto,
            "cantidad": venta.cantidad,
            "total": venta.total,
        })

    # Procesar datos para gráficos
    productos_vendidos = {}
    presentaciones_vendidas = {}

    for venta in todas_las_ventas:
        if venta["nombreSabor"] in productos_vendidos:
            productos_vendidos[venta["nombreSabor"]] += venta["cantidad"]
        else:
            productos_vendidos[venta["nombreSabor"]] = venta["cantidad"]
        if venta["tipoProducto"] in presentaciones_vendidas:
            presentaciones_vendidas[venta["tipoProducto"]] += venta["cantidad"]
        else:
            presentaciones_vendidas[venta["tipoProducto"]] = venta["cantidad"]

    productos_vendidos = sorted(productos_vendidos.items(), key=lambda x: x[1], reverse=True)
    presentaciones_vendidas = sorted(presentaciones_vendidas.items(), key=lambda x: x[1], reverse=True)

    productos_labels = [producto[0] for producto in productos_vendidos]
    productos_data = [producto[1] for producto in productos_vendidos]

    presentaciones_labels = [presentacion[0] for presentacion in presentaciones_vendidas]
    presentaciones_data = [presentacion[1] for presentacion in presentaciones_vendidas]

    return render_template("admin/dashboard.html", 
                        ventas_combinadas=todas_las_ventas,
                        productos_labels=productos_labels, 
                        productos_data=productos_data,
                        presentaciones_labels=presentaciones_labels, 
                        presentaciones_data=presentaciones_data,
                        ultimo_login=current_user.ultimo_login)