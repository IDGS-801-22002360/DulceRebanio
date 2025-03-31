from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app.forms import LoginForm, RegisterForm, RecuperarContrasenaForm
from app.models import Sabores, DetallesProducto, ProductosTerminados, VentasCliente, Usuarios
from decimal import Decimal
from app.utils import role_required
from app.extensions import db

clientes_bp = Blueprint('clientes', __name__, template_folder='../templates/client')

@clientes_bp.route("/", methods=["GET", "POST"])
def index():
    login_form = LoginForm()
    register_form = RegisterForm()
    recuperar_contrasena_form = RecuperarContrasenaForm()
    return render_template(
        "client/mainClientes.html",
        login_form=login_form,
        register_form=register_form,
        recuperar_contrasena_form=recuperar_contrasena_form
    )

# Ruta para la página de clientes
@clientes_bp.route("/clientes", methods=["GET", "POST"])
@login_required
@role_required(["Cliente", "Admin"])
def clientes():
    tipo_seleccionado = request.args.get("tipo", "todos")  
    
    sabores = Sabores.query.join(ProductosTerminados).filter(ProductosTerminados.cantidadDisponible > 0).distinct().all()

    tipos_productos = [producto.tipoProducto for producto in DetallesProducto.query.distinct(DetallesProducto.tipoProducto)]
    if tipo_seleccionado == "todos":
        detalles_productos = DetallesProducto.query.join(ProductosTerminados).filter(ProductosTerminados.cantidadDisponible > 0).distinct().all()
    else:
        detalles_productos = DetallesProducto.query.join(ProductosTerminados).filter(DetallesProducto.tipoProducto == tipo_seleccionado, ProductosTerminados.cantidadDisponible > 0).distinct().all()

    if "carrito" not in session:
        session["carrito"] = []

    return render_template("client/clientes.html", sabores=sabores, detalles_productos=detalles_productos, tipos_productos=tipos_productos, carrito=session["carrito"], ultimo_login=current_user.ultimo_login)

# Ruta para agregar productos al carrito
@clientes_bp.route("/agregar_carrito", methods=["POST"])
def agregar_carrito():
    sabor_id = request.form.get("sabor_id")
    tipo_producto = request.form.get("tipo_producto")
    cantidad = int(request.form.get("cantidad", 1))

    sabor = Sabores.query.get(sabor_id)
    tipo = DetallesProducto.query.get(tipo_producto)

    if sabor and tipo:
        precio = Decimal(tipo.precio)  
        subtotal = precio * cantidad 

        if "carrito" not in session:
            session["carrito"] = []

        carrito = session["carrito"]
        producto_existente = next((item for item in carrito if item["id"] == sabor.idSabor and item["tipo"] == tipo.tipoProducto), None)

        if producto_existente:
            producto_existente["cantidad"] += cantidad
            producto_existente["subtotal"] = float(Decimal(producto_existente["precio"]) * producto_existente["cantidad"])
        else:
            item = {
                "id": sabor.idSabor,
                "nombre": sabor.nombreSabor,
                "tipo": tipo.tipoProducto,
                "cantidad": cantidad,
                "precio": float(precio),
                "subtotal": float(subtotal)
            }
            carrito.append(item)

        total_general = sum(item["subtotal"] for item in carrito)
        session["total_general"] = float(total_general)  

        session["carrito"] = carrito  
        session.modified = True  
    return redirect(url_for("clientes.clientes"))

# Ruta para eliminar productos del carrito
@clientes_bp.route("/eliminar_carrito/<int:item_id>", methods=["POST"])
def eliminar_carrito(item_id):
    session["carrito"] = [item for item in session["carrito"] if item["id"] != item_id]
    total_general = sum(item["subtotal"] for item in session["carrito"])
    session["total_general"] = float(total_general)  

    session.modified = True  
    return redirect(url_for("clientes.clientes"))

# Ruta para procesar la compra
@clientes_bp.route("/procesar_compra", methods=["POST"])
def procesar_compra():
    carrito = session.get("carrito", [])

    if not carrito:
        flash("Carrito vacío o falta nombre del cliente", "warning")
        return redirect(url_for("clientes.clientes"))

    if not current_user.is_authenticated:
        flash("Debes iniciar sesión para realizar la compra", "warning")
        return redirect(url_for("clientes.index"))

    for item in carrito:
        venta_existente = VentasCliente.query.filter_by(
            nombreCliente=current_user.nombre,
            nombreSabor=item["nombre"],
            tipoProducto=item["tipo"]
        ).first()

        if venta_existente:
            venta_existente.cantidad += item["cantidad"]
            venta_existente.total = venta_existente.cantidad * item["precio"]
            venta_existente.estatus = 1 
        else:
            nueva_venta = VentasCliente(
                nombreCliente=current_user.nombre,
                nombreSabor=item["nombre"],
                cantidad=item["cantidad"],
                tipoProducto=item["tipo"],
                total=item["cantidad"] * item["precio"],
                estatus=1  
            )
            db.session.add(nueva_venta)

        producto = ProductosTerminados.query.join(DetallesProducto).filter(
            ProductosTerminados.idSabor == item["id"],
            DetallesProducto.tipoProducto == item["tipo"]
        ).first()

        if producto:
            if producto.cantidadDisponible >= item["cantidad"]:
                producto.cantidadDisponible -= item["cantidad"]
            else:
                flash(f"No hay suficiente stock para {item['nombre']} ({item['tipo']})", "danger")
                return redirect(url_for("clientes.clientes"))
        else:
            flash(f"Producto no encontrado: {item['nombre']} ({item['tipo']})", "danger")
            return redirect(url_for("clientes.clientes"))

    db.session.commit()
    session["carrito"] = []
    flash("¡Compra realizada con éxito!", "success")
    return redirect(url_for("clientes.clientes"))

# Ruta para el historial de compras
@clientes_bp.route("/historial", methods=["GET"])
def historialCompras():
    if not current_user.is_authenticated:
        flash("Debes iniciar sesión para ver tu historial de compras", "warning")
        return redirect(url_for("clientes.index"))  

    ventas = VentasCliente.query.filter_by(nombreCliente=current_user.nombre).all()  

    return render_template("client/historial.html", ventas=ventas)