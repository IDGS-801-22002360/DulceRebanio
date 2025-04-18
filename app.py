from PIL import Image
from io import BytesIO
import base64
import os
import json
import time
import secrets
import string
import pyotp
import ntplib
import datetime
from datetime import datetime, timedelta, date
from decimal import Decimal
from functools import wraps

from flask import Flask, render_template, request, jsonify, redirect, session, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from flask_wtf import FlaskForm, CSRFProtect, RecaptchaField
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import text
from fpdf import FPDF

from config import DevelopmentConfig
from logger import action_logger, error_logger

# Modelos
from models import (
    db, Usuarios, Ventas, DetallesVenta, ComprasInsumos, Proveedores, 
    ProductosTerminados, MateriasPrimas, Receta, RecetaDetalle, VentasCliente
)

# Formularios
from forms import (
    CompraInsumoForm, LoteForm, InsumoForm, MermaForm, ProveedorForm, PaqueteForm, 
    RecuperarContrasenaForm, EmpleadoForm, HiddenField, SubmitField, LoginForm, RegisterForm
)


app = Flask(__name__)
app.secret_key = "dongalleto" 
app.config.from_object(DevelopmentConfig)
csrf = CSRFProtect()

app.config["RECAPTCHA_PUBLIC_KEY"] = "6Lcb1f0qAAAAAMLjkyE44X40_nQq_FZns9Sj8CVs"
app.config["RECAPTCHA_PRIVATE_KEY"] = "6Lcb1f0qAAAAADFk-w_f5-Da5MyzdN2E8HdY-Vcs"
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'fabian.anrey@gmail.com'
app.config['MAIL_PASSWORD'] = 'pksh vgjq rbur axnc'
app.config['MAIL_DEFAULT_SENDER'] = 'fabian.anrey@gmail.com'

mail = Mail(app)
# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=200)

def sync_time():
    try:
        c = ntplib.NTPClient()
        response = c.request('pool.ntp.org')
        time.time = lambda: response.tx_time
    except:
        pass

sync_time()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuarios.query.get(int(user_id))

failed_attempts = {}

def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.rol not in roles:
                flash('No tienes permiso para acceder a esta página.', 'danger')
                

                if current_user.rol == 'Admin':
                    return redirect(url_for('usuarios'))
                elif current_user.rol == 'Ventas':
                    return redirect(url_for('puntoVenta'))
                elif current_user.rol == 'Produccion':
                    return redirect(url_for('galletas'))
                elif current_user.rol == 'Cliente':
                    return redirect(url_for('clientes'))
                else:
                    return redirect(url_for('index')) 
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator


#!============================== Clientes Index ==============================#

@app.route("/", methods=["GET", "POST"])
@app.route("/index")
def index():
    login_form = LoginForm()
    register_form = RegisterForm()
    recuperar_contrasena_form = RecuperarContrasenaForm()
    show_recuperar_modal = request.args.get('show_recuperar_modal', False)

    # Obtener todas las recetas desde la base de datos
    recetas = Receta.query.filter_by(estatus=1).all()  # Filtrar solo recetas activas
    print(f"Recetas cargadas: {recetas}")  # Depuración

    return render_template(
        "client/mainClientes.html", 
        login_form=login_form, 
        register_form=register_form,
        recuperar_contrasena_form=recuperar_contrasena_form,
        show_recuperar_modal=show_recuperar_modal,
        recetas=recetas  # Pasar las recetas al contexto de la plantilla
    )

@app.route("/verDetalles/<int:receta_id>")
def ver_detalles(receta_id):
    # Verificar si el usuario está autenticado
    if "user_id" not in session:  # Cambia "user_id" según tu implementación de sesión
        flash("Por favor, inicia sesión para ver los detalles del producto.", "warning")
        return redirect(url_for("index"))  # Redirigir a la página de inicio o login

    # Si el usuario está autenticado, redirigir al módulo de clientes
    return redirect(url_for("modulo_clientes", receta_id=receta_id))

@app.context_processor
def inject_notifications():
    # Definir los mínimos para considerar bajo stock
    min_galletas = 30  # Para productos de tipo "Granel"
    min_paquetes = 3   # Para paquetes de tipo "Kilo" o "700 gr"

    # Contar productos con bajo stock
    productos_bajo_stock = ProductosTerminados.query.filter(
        ProductosTerminados.estatus == 1
    ).filter(
        ((ProductosTerminados.tipoProducto == "Granel") & (ProductosTerminados.cantidadDisponible < min_galletas)) |
        ((ProductosTerminados.tipoProducto.in_(["Kilo", "700 gr"])) & (ProductosTerminados.cantidadDisponible < min_paquetes))
    ).count()

    # Contar pedidos pendientes
    pedidos_pendientes = VentasCliente.query.filter_by(estatus=1).count()

    return dict(productos_bajo_stock=productos_bajo_stock, pedidos_pendientes=pedidos_pendientes)

#!============================== Modulo Carrito que no es carrito ==============================#

@app.route("/clientes", methods=["GET", "POST"])
@login_required
@role_required(["Cliente", "Admin"])
def clientes():
    recetas = Receta.query.distinct().all()
    tipos_productos = ["Granel", "700 gr", "Kilo"]

    detalles_recetas = RecetaDetalle.query.distinct().all()
    if "carrito" not in session:
        session["carrito"] = []

    return render_template(
        "client/clientes.html",
        recetas=recetas,
        detalles_recetas=detalles_recetas,
        tipos_productos=tipos_productos,
        carrito=session["carrito"],
        ultimo_login=current_user.ultimo_login
    )


@app.route("/agregar_carrito", methods=["POST"])
@login_required
@role_required(["Cliente", "Admin"])
def agregar_carrito():
    receta_id = request.form.get("receta_id")
    tipo = request.form.get("tipo-producto")
    cantidad = int(request.form.get("cantidad"))
    precio = float(request.form.get("precio"))

    receta = Receta.query.get(receta_id)
    if not receta:
        flash("Receta no encontrada", "error")
        return redirect(url_for("clientes"))
    
    # Redimensionar y recodificar la imagen si existe
    imagen_url = None
    if receta.imagen:
        try:
            # Decodificar la imagen Base64
            imagen_bytes = base64.b64decode(receta.imagen)
            imagen = Image.open(BytesIO(imagen_bytes))

            # Redimensionar la imagen (por ejemplo, 200x200 píxeles)
            imagen = imagen.resize((200, 200), Image.ANTIALIAS)

            # Recodificar la imagen a JPEG con calidad reducida
            buffer = BytesIO()
            imagen.save(buffer, format="JPEG", quality=50)  # Calidad reducida al 50%
            buffer.seek(0)

            # Codificar nuevamente en Base64
            imagen_url = f"data:image/jpeg;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"
        except Exception as e:
            app.logger.error(f"Error al procesar la imagen: {str(e)}")
            imagen_url = None

    subtotal = round(precio * cantidad, 2)
    nuevo_item = {
        "id": int(receta_id),
        "nombre": receta.nombreReceta,
        "tipo": tipo,
        "cantidad": cantidad,
        "precio": precio,
        "subtotal": subtotal,
        "imagen": imagen_url  # Usar la imagen redimensionada y recodificada
    }
    if "carrito" not in session:
        session["carrito"] = []
    session["carrito"].append(nuevo_item)
    total_general = sum(item["subtotal"] for item in session["carrito"])
    session["total_general"] = round(total_general, 2)

    session.modified = True
    flash(f"{receta.nombreReceta} ({tipo}) agregado al carrito.", "success")
    
    return redirect(url_for("clientes"))


@app.route("/eliminar_carrito/<int:item_id>", methods=["POST"])
def eliminar_carrito(item_id):
    tipo = request.form.get("tipo")  
    session["carrito"] = [
        item for item in session["carrito"]
        if not (int(item["id"]) == item_id and item["tipo"] == tipo)
    ]
    total_general = sum(
        item.get("subtotal", item.get("precio", 0) * item.get("cantidad", 1))
        for item in session["carrito"]
    )
    session["total_general"] = round(total_general, 2)

    session.modified = True
    return redirect(url_for("clientes"))


@app.route("/procesar_compra", methods=["POST"])
def procesar_compra():
    carrito = session.get("carrito", [])

    if not carrito:
        flash("Carrito vacío o falta nombre del cliente", "warning")
        return redirect(url_for("clientes"))

    if not current_user.is_authenticated:
        flash("Debes iniciar sesión para realizar la compra", "warning")
        return redirect(url_for("login"))
    
    fecha_entrega = request.form.get("fecha_entrega")
    fecha_entrega = datetime.strptime(fecha_entrega, '%Y-%m-%d')

    for item in carrito:
        cantidad = item["cantidad"]

        # Crear un nuevo pedido para cada elemento del carrito
        nueva_venta = VentasCliente(
            nombreCliente=current_user.nombre,
            nombreSabor=item["nombre"],
            cantidad=cantidad,
            tipoProducto=item["tipo"],
            total=cantidad * item["precio"],
            estatus=1,
            fechaEntrega=fecha_entrega.strftime('%Y-%m-%d')
        )
        db.session.add(nueva_venta)

    db.session.commit()
    session["carrito"] = []
    flash("¡Pedido realizado con éxito!", "success")
    return redirect(url_for("clientes"))


@app.route("/pedidos", methods=["GET"])
@login_required
@role_required(["Admin", "Ventas"])
def pedidos():
    # Obtener todos los pedidos pendientes (estatus 1)
    pedidos = db.session.query(VentasCliente).filter_by(estatus=1).all()

    # Agrupar pedidos por cliente y calcular el total
    clientes = {}
    for pedido in pedidos:
        if pedido.nombreCliente not in clientes:
            clientes[pedido.nombreCliente] = {
                "productos": [],
                "total_cliente": 0,
            }
        # Agregar el pedido al cliente
        clientes[pedido.nombreCliente]["productos"].append(pedido)
        clientes[pedido.nombreCliente]["total_cliente"] += pedido.total

    return render_template("admin/pedidos.html", ultimo_login=current_user.ultimo_login, clientes=clientes)



@app.route("/realizar_pedido/<int:pedido_id>", methods=["POST"])
@login_required
@role_required(["Admin"])
def realizar_pedido(pedido_id):
    # Obtener el pedido de la base de datos
    pedido = VentasCliente.query.get_or_404(pedido_id)
    
    # Verificar que el pedido esté pendiente
    if pedido.estatus != 1:
        flash('Este pedido no está pendiente o ya ha sido realizado.', 'danger')
        return redirect(url_for('pedidos'))
    
    # Buscar todos los lotes disponibles para la receta, tipo de producto y con estatus 1
    lotes = ProductosTerminados.query.join(Receta).filter(
        Receta.nombreReceta == pedido.nombreSabor,  # Relacionar con el nombre del sabor
        ProductosTerminados.tipoProducto == pedido.tipoProducto,  # Verificar que coincida el tipo de producto
        ProductosTerminados.estatus == 1  # Solo lotes activos
    ).order_by(ProductosTerminados.fechaCaducidad.asc()).all()

    cantidad_pendiente = pedido.cantidad  # Cantidad que falta surtir

    for lote in lotes:
        if cantidad_pendiente <= 0:
            break  # Si ya se surtió todo el pedido, salir del bucle

        if lote.cantidadDisponible >= cantidad_pendiente:
            # Si el lote actual puede surtir todo lo pendiente
            lote.cantidadDisponible -= cantidad_pendiente
            cantidad_pendiente = 0
        else:
            # Si el lote actual no es suficiente, usar todo lo disponible y continuar con el siguiente lote
            cantidad_pendiente -= lote.cantidadDisponible
            lote.cantidadDisponible = 0
            lote.estatus = 0  # Marcar el lote como inactivo si se agotó

    if cantidad_pendiente > 0:
        # Si no se pudo surtir todo el pedido, mostrar un mensaje de error
        flash('No hay suficiente inventario para completar el pedido.', 'danger')
        db.session.rollback()  # Revertir cualquier cambio en los lotes
        return redirect(url_for('pedidos'))

    # Si se surtió todo el pedido, actualizar el estado del pedido
    pedido.estatus = 2
    db.session.commit()
    flash('El pedido ha sido marcado como realizado y el inventario ha sido actualizado.', 'success')

    return redirect(url_for('pedidos'))


@app.route("/historial", methods=["GET"])
@login_required
@role_required(["Cliente", "Admin"])
def historialCompras():
    if not current_user.is_authenticated:
        flash("Debes iniciar sesión para ver tu historial de compras", "warning")
        return redirect(url_for("login"))
    
    ventas = VentasCliente.query.filter_by(nombreCliente=current_user.nombre).all()
    hoy = date.today()
    
    # Convertir fechaEntrega a date antes de comparar
    pedidos_hoy = [v for v in ventas if v.fechaEntrega and v.fechaEntrega.date() == hoy]
    pedidos_anteriores = [v for v in ventas if v.fechaEntrega and v.fechaEntrega.date() < hoy]
    
    return render_template(
        "client/historial.html", 
        pedidos_hoy=pedidos_hoy, 
        pedidos_anteriores=pedidos_anteriores,
        ultimo_login=current_user.ultimo_login
    )
    

@app.route("/cancelar_pedido/<int:idVentasCliente>", methods=["POST"])
def cancelar_pedido(idVentasCliente):
    pedido = VentasCliente.query.get_or_404(idVentasCliente)
    hoy = date.today()

    # Convertir fechaEntrega a date antes de comparar
    if pedido.fechaEntrega.date() < hoy:
        flash("No se puede cancelar este pedido, ya ha sido entregado", "warning")
        return redirect(url_for("historialCompras"))

    if pedido.estatus == 1:
        pedido.estatus = 0
        db.session.commit()
        flash("Pedido cancelado correctamente", "success")
    else:
        flash("No se puede cancelar este pedido", "warning")

    return redirect(url_for("historialCompras"))


@app.route("/ventasClientes", methods=["GET", "POST"])
@login_required
@role_required(['Admin'])
def ventasClientes():
    ventas_estatus_1 = db.session.query(
        Usuarios.nombre,
        Usuarios.apaterno,
        Usuarios.amaterno,
        VentasCliente.nombreCliente,
        VentasCliente.nombreSabor,
        VentasCliente.cantidad,
        VentasCliente.total,
        VentasCliente.tipoProducto 
    ).join(VentasCliente, VentasCliente.nombreCliente == Usuarios.nombre) \
    .filter(Usuarios.rol == 'Cliente') \
    .all()

    clientes_compras = {}
    for venta in ventas_estatus_1:
        if venta.nombreCliente not in clientes_compras:
            clientes_compras[venta.nombreCliente] = {'nombreCliente': venta.nombreCliente, 'productos': []}

        producto_existente = None
        for producto in clientes_compras[venta.nombreCliente]['productos']:
            if producto['nombreSabor'] == venta.nombreSabor and producto['tipoProducto'] == venta.tipoProducto:
                producto_existente = producto
                break

        if producto_existente:
            producto_existente['cantidad'] += venta.cantidad
            producto_existente['total'] += venta.total 
        else:
            clientes_compras[venta.nombreCliente]['productos'].append({
                'nombreSabor': venta.nombreSabor,
                'cantidad': venta.cantidad,
                'total': venta.total,
                'tipoProducto': venta.tipoProducto 
            })

    return render_template("admin/usuariosClientes.html", clientes_compras=clientes_compras, ultimo_login=current_user.ultimo_login)


#!============================== Modulo dashboard ==============================#

@app.route("/dashboard", methods=["GET"])
@login_required
@role_required(['Admin'])
def dashboard():
    carrito = session.get("carrito", [])
    ventas_clientes = db.session.query(
        VentasCliente.nombreCliente,
        VentasCliente.nombreSabor,
        VentasCliente.tipoProducto,
        VentasCliente.cantidad,
        VentasCliente.total
    ).filter(VentasCliente.estatus == 2).all()

    todas_las_ventas = []
    for item in carrito:
        todas_las_ventas.append({
            "nombreCliente": current_user.nombre,
            "nombreSabor": item["nombre"],
            "tipoProducto": item["tipo"],
            "cantidad": item["cantidad"],
            "total": item["cantidad"] * item["precio"],
            "metodo": "Carrito"
        })
    for venta in ventas_clientes:
        todas_las_ventas.append({
            "nombreCliente": venta.nombreCliente,
            "nombreSabor": venta.nombreSabor,
            "tipoProducto": venta.tipoProducto,
            "cantidad": venta.cantidad,
            "total": venta.total,
        })

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

    pedidos_totales = {}
    punto_venta_totales = {}

    for venta in todas_las_ventas:
        if venta["nombreSabor"] in punto_venta_totales:
            punto_venta_totales[venta["nombreSabor"]] += venta["cantidad"]
        else:
            punto_venta_totales[venta["nombreSabor"]] = venta["cantidad"]

    for producto in productos_vendidos:
        if producto[0] in pedidos_totales:
            pedidos_totales[producto[0]] += producto[1]
        else:
            pedidos_totales[producto[0]] = producto[1]

    pedidos_labels = [item[0] for item in productos_vendidos]
    pedidos_data = [item[1] for item in productos_vendidos]

    punto_venta_labels = [item[0] for item in punto_venta_totales.items()]
    punto_venta_data = [item[1] for item in punto_venta_totales.items()]

    total_ventas_realizadas = len(todas_las_ventas)  
    ganancias_estimadas = sum(venta["total"] for venta in todas_las_ventas) * 0.3  

    clv = (sum(venta["total"] for venta in todas_las_ventas) / 
    (len(set(venta["nombreCliente"] for venta in todas_las_ventas)) or 1))

    return render_template(
        "admin/dashboard.html",
        ventas_combinadas=todas_las_ventas,
        productos_labels=productos_labels,
        productos_data=productos_data,
        presentaciones_labels=presentaciones_labels,
        presentaciones_data=presentaciones_data,
        ultimo_login=current_user.ultimo_login,
        pedidos_labels=pedidos_labels,
        pedidos_data=pedidos_data,
        punto_venta_labels=punto_venta_labels,
        punto_venta_data=punto_venta_data,
        roi=total_ventas_realizadas,  # Ahora muestra solo el número de ventas
        clv=clv
    )


#!============================== Modulo de Productos ==============================#  

@app.route("/galletas", methods=["GET", "POST"])
@login_required  
@role_required(['Admin', 'Produccion', "Ventas"])
def galletas():
    form = LoteForm()
    paquete_form = PaqueteForm()

    form.sabor.choices = [(receta.idReceta, receta.nombreReceta) 
                        for receta in Receta.query.filter_by(estatus=1).all()]

    productos = db.session.query(
        ProductosTerminados,
        Receta
    ).join(
        Receta,
        ProductosTerminados.idReceta == Receta.idReceta
    ).filter(
        ProductosTerminados.estatus == 1
    ).all()

    today = date.today()
    is_christmas_season = today.month == 12
    min_galletas = 60 if is_christmas_season else 30
    min_paquetes = 6 if is_christmas_season else 3

    productos_data = []
    for pt, receta in productos:
        bajo_stock = (
            (pt.tipoProducto == "Granel" and pt.cantidadDisponible < min_galletas) or
            (pt.tipoProducto in ["Kilo", "Med. Kilo"] and pt.cantidadDisponible < min_paquetes)
        )
        productos_data.append({
            'id_producto': pt.idProducto,
            'nombre_receta': receta.nombreReceta,
            'tipo_producto': pt.tipoProducto,
            'cantidad': pt.cantidadDisponible,
            'fecha_caducidad': pt.fechaCaducidad.strftime('%Y-%m-%d') if pt.fechaCaducidad else 'N/A',
            'precio': float(receta.precio),
            'bajo_stock': bajo_stock
        })

    for producto in productos_data:
        if producto['bajo_stock']:
            flash(f"¡Alerta! Bajo stock: {producto['nombre_receta']} ({producto['tipo_producto']}) - Cantidad: {producto['cantidad']}", "warning")

    productos_granel = [p for p in productos_data if p['tipo_producto'] == "Granel"]

    return render_template(
        'admin/galletas.html',
        productos=productos_data,
        productos_granel=productos_granel,
        form=form,
        paquete_form=paquete_form,
        ultimo_login=current_user.ultimo_login
    )


@app.route("/guardarLote", methods=["POST"])
def guardarLote():
    form = LoteForm()
    form.sabor.choices = [(receta.idReceta, receta.nombreReceta) 
                        for receta in Receta.query.filter_by(estatus=1).all()]
    
    if form.validate_on_submit():
        try:
            print("Formulario validado correctamente")
            idReceta = form.sabor.data
            id_detalle = "Granel"
            print(f"Receta seleccionada: {idReceta}")

            # Crear el nuevo producto terminado
            nuevo_producto = ProductosTerminados(
                idReceta=idReceta,
                cantidadDisponible=200,
                fechaCaducidad=date.today() + timedelta(days=7),
                tipoProducto=id_detalle,
                estatus=1
            )
            db.session.add(nuevo_producto)
            print("Producto terminado agregado a la sesión")

            # Obtener los detalles de la receta (insumos necesarios)
            detalles_receta = RecetaDetalle.query.filter_by(idReceta=idReceta).all()
            if not detalles_receta:
                raise Exception("La receta seleccionada no tiene insumos asignados.")

            # Restar los insumos necesarios de la tabla MateriasPrimas
            for detalle in detalles_receta:
                materia_prima = MateriasPrimas.query.get(detalle.idMateriaPrima)
                if not materia_prima:
                    raise Exception(f"La materia prima con ID {detalle.idMateriaPrima} no existe.")

                # Verificar si hay suficiente cantidad disponible
                if materia_prima.cantidadDisponible < detalle.cantidad:
                    raise Exception(f"No hay suficiente {materia_prima.materiaPrima} para producir el lote.")

                # Restar la cantidad necesaria
                materia_prima.cantidadDisponible -= detalle.cantidad
                print(f"Se descontaron {detalle.cantidad} de {materia_prima.materiaPrima}. Cantidad restante: {materia_prima.cantidadDisponible}")

            # Confirmar la transacción
            db.session.commit()
            print("Transacción confirmada y datos guardados correctamente")

            # Log de la acción
            action_logger.info(f"Usuario: {current_user.correo} - Acción: Guardar lote - Receta: {nuevo_producto.idReceta} - Cantidad: {nuevo_producto.cantidadDisponible} - Fecha: {datetime.now()}")

            flash('Lote guardado y materias primas descontadas correctamente', 'success')
        except Exception as e:
            db.session.rollback()
            print(f"Error en guardarLote: {str(e)}")
            flash(f'Error al guardar el lote: {str(e)}', 'danger')
        return redirect(url_for('galletas'))

    print("Error: El formulario no pasó la validación")
    flash('Error al guardar el lote. Verifica los datos ingresados.', 'danger')
    return redirect(url_for('galletas'))


@app.route("/mermar", methods=["POST"])
def mermar():
    form = MermaForm()
    app.logger.info("Iniciando proceso de merma...")  # Registro inicial

    if form.validate_on_submit():
        try:
            # Obtener datos del formulario
            id_producto = form.idProducto.data
            cantidad = form.cantidad.data
            mermar_todo = form.mermar_todo.data

            app.logger.info(f"Datos recibidos - ID Producto: {id_producto}, Cantidad: {cantidad}, Mermar Todo: {mermar_todo}")

            # Validar si se seleccionó "mermar todo"
            if mermar_todo:
                cantidad = None
                app.logger.info("Se seleccionó 'mermar todo'")
            elif not cantidad or cantidad == '':
                app.logger.warning("Cantidad no válida ingresada")
                flash('Debe ingresar una cantidad válida', 'danger')
                return redirect(url_for('galletas'))

            # Validar cantidad
            if cantidad is not None:
                cantidad = int(cantidad)
                if cantidad <= 0:
                    app.logger.warning("Cantidad ingresada menor o igual a 0")
                    flash('La cantidad debe ser mayor a 0', 'danger')
                    return redirect(url_for('galletas'))

            # Buscar el producto
            producto = ProductosTerminados.query.get(id_producto)
            if not producto:
                app.logger.warning(f"Producto con ID {id_producto} no encontrado")
                flash('Producto no encontrado', 'danger')
                return redirect(url_for('galletas'))

            app.logger.info(f"Producto encontrado - ID: {producto.idProducto}, Cantidad Disponible: {producto.cantidadDisponible}")

            # Aplicar la merma
            if cantidad is None or cantidad >= producto.cantidadDisponible:
                cantidad_mermada = producto.cantidadDisponible
                producto.cantidadDisponible = 0
                producto.estatus = 0
                app.logger.info(f"Merma total aplicada - Cantidad Mermada: {cantidad_mermada}")
            else:
                cantidad_mermada = cantidad
                producto.cantidadDisponible -= cantidad
                app.logger.info(f"Merma parcial aplicada - Cantidad Mermada: {cantidad_mermada}, Cantidad Restante: {producto.cantidadDisponible}")

            # Guardar cambios en la base de datos
            db.session.commit()
            app.logger.info(f"Merma completada exitosamente para el producto ID {producto.idProducto}")

            # Log de la acción
            action_logger.info(f"Usuario: {current_user.correo} - Acción: Mermar producto - Producto ID: {producto.idProducto} - Cantidad mermada: {cantidad_mermada} - Fecha: {datetime.now()}")

            flash('Producto mermado correctamente', 'success')
            return redirect(url_for('galletas'))

        except Exception as e:
            app.logger.error(f"Error al mermar producto: {str(e)}")
            flash('Ocurrió un error al procesar la merma', 'danger')
            return redirect(url_for('galletas'))

    # Depurar errores del formulario
    app.logger.warning("El formulario no pasó la validación")
    for field, errors in form.errors.items():
        for error in errors:
            app.logger.error(f"Error en el campo {field}: {error}")

    flash('Error al mermar el producto. Verifica los datos ingresados.', 'danger')
    return redirect(url_for('galletas'))


@app.route("/guardar_paquete", methods=["POST"])
def guardar_paquete():
    paquete_form = PaqueteForm()
    app.logger.info(f"Datos enviados: {request.form}")  # Depuración de datos enviados

    if paquete_form.validate_on_submit():
        # Obtener datos del formulario
        tipo_producto = paquete_form.tipo_producto.data  # 2 = Kilo, 3 = 700 gr
        cantidad_paquetes = paquete_form.cantidad.data
        id_producto = request.form.get("txtIdGalletaGranel")  # ID del lote seleccionado

        app.logger.info(f"ID Producto: {id_producto}, Tipo Producto: {tipo_producto}, Cantidad: {cantidad_paquetes}")

        # Buscar el producto seleccionado
        producto = ProductosTerminados.query.get(id_producto)
        if not producto:
            flash("El lote seleccionado no existe.", "danger")
            return redirect(url_for("galletas"))

        # Determinar la cantidad de galletas necesarias por paquete
        galletas_por_paquete = 20 if tipo_producto == 2 else 14
        galletas_necesarias = galletas_por_paquete * cantidad_paquetes

        # Validar si hay suficientes galletas disponibles
        if producto.cantidadDisponible < galletas_necesarias:
            flash("No hay suficientes galletas en el lote seleccionado.", "danger")
            return redirect(url_for("galletas"))

        # Reducir la cantidad disponible en el lote original
        producto.cantidadDisponible -= galletas_necesarias
        if producto.cantidadDisponible == 0:
            producto.estatus = 0

        # Crear el nuevo paquete
        nuevo_paquete = ProductosTerminados(
            idReceta=producto.idReceta,  # Mantener la receta del producto original
            tipoProducto="Kilo" if tipo_producto == 2 else "700 gr",  # Guardar el tipo de producto como texto
            cantidadDisponible=cantidad_paquetes,
            fechaCaducidad=producto.fechaCaducidad,  # Mantener la fecha de caducidad del lote original
            estatus=1  # El nuevo paquete estará activo
        )
        db.session.add(nuevo_paquete)
        db.session.commit()

        # Log de la acción
        action_logger.info(f"Usuario: {current_user.correo} - Acción: Guardar paquete - Receta: {nuevo_paquete.idReceta} - Tipo: {nuevo_paquete.tipoProducto} - Cantidad: {cantidad_paquetes} - Fecha: {datetime.now()}")

        flash(f"Paquete creado correctamente: {cantidad_paquetes} paquetes de tipo {nuevo_paquete.tipoProducto}.", "success")
        return redirect(url_for("galletas"))

    # Si el formulario no es válido
    app.logger.warning("El formulario no pasó la validación")
    for field, errors in paquete_form.errors.items():
        for error in errors:
            app.logger.error(f"Error en el campo {field}: {error}")

    flash("Error al guardar el paquete. Verifica los datos ingresados.", "danger")
    return redirect(url_for("galletas"))



#!============================== Modulo de Recetas ==============================#  

@app.route('/recetas', methods=['GET', 'POST'])
@login_required
@role_required(['Admin', 'Produccion'])
def recetas():
    
    if request.method == 'POST':
        
        if 'action' in request.form and request.form['action'] == 'renombrar':
            receta_id = request.form.get('id_receta')
            nuevo_nombre = request.form.get('nombre_receta')
            
            if receta_id and nuevo_nombre:
                receta = Receta.query.get(receta_id)
                if receta:
                    try:
                        receta.nombreReceta = nuevo_nombre
                        db.session.commit()
                        flash('Receta renombrada exitosamente', 'success')
                    except Exception as e:
                        db.session.rollback()
                        flash('Error al renombrar la receta: el nombre ya existe', 'danger')
                        
    receta_seleccionada = None
    detalles = []
    
    if request.method == 'POST' and 'receta_id' in request.form:
        receta_id = request.form['receta_id']
        receta_seleccionada = Receta.query.get(receta_id)
        if receta_seleccionada:
            detalles = db.session.query(RecetaDetalle, MateriasPrimas)\
                .join(MateriasPrimas)\
                .filter(RecetaDetalle.idReceta == receta_id)\
                .all()

    return render_template(
        'admin/recetas.html',
        recetas=Receta.query.all(),
        receta_seleccionada=receta_seleccionada,
        receta_actual=receta_seleccionada,
        detalles=detalles,
        materias_primas=MateriasPrimas.query.all(),
        ultimo_login=current_user.ultimo_login
    )

@app.route('/receta/<int:id>/detalles', methods=['GET'])
@login_required
def get_receta_detalles(id):
    try:
        receta = Receta.query.get_or_404(id)
        detalles = db.session.query(
            RecetaDetalle,
            MateriasPrimas
        ).join(
            MateriasPrimas, 
            RecetaDetalle.idMateriaPrima == MateriasPrimas.idMateriaPrima.order
        ).filter(
            RecetaDetalle.idReceta == id
        ).order_by(  # Ordenar solo por ID de Materias Primas
            MateriasPrimas.idMateriaPrima.asc()
        ).all()

        return jsonify([{
            'idRecetaDetalle': d.RecetaDetalle.idRecetaDetalle,
            'materiaPrima': d.MateriasPrimas.materiaPrima,
            'cantidad': float(d.RecetaDetalle.cantidad),
            'unidadMedida': d.MateriasPrimas.unidadMedida
        } for d in detalles])
    
    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify({'error': 'Error al cargar detalles'}), 500


@app.route('/actualizar_receta', methods=['POST'])
@login_required
def actualizar_receta():
    receta_id = request.form.get('receta_id')
    if not receta_id:
        flash('Receta ID no encontrado en la solicitud', 'danger')
        return redirect(url_for('recetas'))

    detalles_actualizados = []
    for key, value in request.form.items():
        if key.startswith('cantidad_'):
            detalle_id = key.split('_')[1]
            detalle = RecetaDetalle.query.get(detalle_id)
            if detalle:
                try:
                    detalle.cantidad = float(value)
                    detalles_actualizados.append(detalle_id)
                except ValueError:
                    flash(f'Valor inválido para cantidad en detalle ID {detalle_id}', 'danger')
                    return redirect(url_for('recetas'))

    if detalles_actualizados:
        db.session.commit()
        flash('Cambios guardados correctamente', 'success')
    else:
        flash('No se actualizaron detalles', 'warning')

    return redirect(url_for('recetas'))


@app.route('/eliminar_detalle/<int:id>', methods=['POST'])
@login_required
def eliminar_detalle(id):
    detalle = RecetaDetalle.query.get_or_404(id)
    db.session.delete(detalle)
    db.session.commit()
    flash('Insumo eliminado de la receta', 'info')
    return redirect(url_for('recetas'))


@app.route('/agregar_receta', methods=['POST'])
@login_required
@role_required(['Admin', 'Produccion'])
def agregar_receta():
    nombre_receta = request.form.get('nombreReceta')
    if not nombre_receta:
        flash('El nombre de la receta es obligatorio', 'danger')
        return redirect(url_for('recetas'))

    nueva_receta = Receta(nombreReceta=nombre_receta, precio=7)
    db.session.add(nueva_receta)
    db.session.commit()
    flash('Receta agregada correctamente', 'success')
    return redirect(url_for('recetas'))

@app.route('/agregar_insumo_receta', methods=['POST'])
@login_required
@role_required(['Admin', 'Produccion'])
def agregar_insumo_receta():
    receta_id = request.form.get('receta_id')
    insumo_id = request.form.get('insumo_id')
    cantidad = request.form.get('cantidad', 0.00)
    unidad_medida = request.form.get('unidad_medida')

    if not receta_id or not insumo_id or not unidad_medida:
        flash('Todos los campos son obligatorios', 'danger')
        return redirect(url_for('recetas'))

    insumo_existente = RecetaDetalle.query.filter_by(idReceta=receta_id, idMateriaPrima=insumo_id).first()
    if insumo_existente:
        flash('El insumo ya está agregado a la receta', 'danger')
        return redirect(url_for('recetas'))

    nuevo_detalle = RecetaDetalle(
        idReceta=receta_id,
        idMateriaPrima=insumo_id,
        cantidad=cantidad,
        unidadMedida=unidad_medida
    )
    db.session.add(nuevo_detalle)
    db.session.commit()
    flash('Insumo agregado a la receta correctamente', 'success')
    return redirect(url_for('recetas'))

@app.route('/editar_receta', methods=['POST'])
@login_required
@role_required(['Admin', 'Produccion'])
def editar_receta():
    receta_id = request.form.get('receta_id')
    nombre_receta = request.form.get('nombre_receta')
    precio_receta = request.form.get('precio_receta')

    if not receta_id or not nombre_receta or not precio_receta:
        flash('Todos los campos son obligatorios', 'danger')
        return redirect(url_for('recetas'))

    try:
        receta = Receta.query.get(receta_id)
        receta.nombreReceta = nombre_receta
        receta.precio = precio_receta
        db.session.commit()
        flash('Receta actualizada correctamente', 'success')
    except Exception as e:
        app.logger.error(f"Error al actualizar receta: {str(e)}")
        flash('Error al actualizar la receta', 'danger')

    return redirect(url_for('recetas'))


@app.route('/seleccionar_receta', methods=['POST'])
@login_required
@role_required(['Admin', 'Produccion'])
def seleccionar_receta():
    receta_id = request.form.get('receta_id')

    if not receta_id:
        flash('ID de receta es requerido', 'danger')
        return redirect(url_for('recetas'))

    receta = Receta.query.get(receta_id)
    if not receta:
        flash('Receta no encontrada', 'danger')
        return redirect(url_for('recetas'))

    detalles = db.session.query(RecetaDetalle, MateriasPrimas)\
        .join(MateriasPrimas)\
        .filter(RecetaDetalle.idReceta == receta_id)\
        .all()

    return render_template(
        'admin/recetas.html',
        recetas=Receta.query.all(),
        receta_seleccionada=receta,
        receta_actual=receta,
        detalles=detalles,
        materias_primas=MateriasPrimas.query.all(),
        ultimo_login=current_user.ultimo_login
    )

@app.route('/asignar_imagen', methods=['POST'])
@login_required
@role_required(['Admin', 'Produccion'])
def asignar_imagen():
    receta_id = request.form.get('receta_id')
    imagen = request.files.get('imagen_receta')

    if not receta_id or not imagen:
        flash('Todos los campos son obligatorios', 'danger')
        return redirect(url_for('recetas'))

    receta = Receta.query.get(receta_id)
    if not receta:
        flash('Receta no encontrada', 'danger')
        return redirect(url_for('recetas'))

    try:
        imagen_b64 = base64.b64encode(imagen.read()).decode('utf-8')
        receta.imagen = imagen_b64
        db.session.commit()
        flash('Imagen asignada correctamente', 'success')
    except Exception as e:
        app.logger.error(f"Error al asignar imagen: {str(e)}")
        flash('Error al asignar la imagen', 'danger')

    return redirect(url_for('recetas'))



#!============================== Modulo Errores ==============================#

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(Exception)
def handle_general_error(e):
    status_code = getattr(e, 'code', 500)
    
    if current_user.is_authenticated:
        error_logger.info(f"Usuario: {current_user.correo} - Fecha: {datetime.now()}")
    else:
        error_logger.info(f"Usuario: Anónimo - Fecha: {datetime.now()}")
    
    return render_template('codeError.html', error_message=str(e), status_code=status_code), status_code

#!============================== Modulo de Insumos ==============================#
#INSERCIÓN INSUMOS
@app.route("/insumos", methods=["GET", "POST"])
@login_required
@role_required(['Admin'])
def insumos():
    form = InsumoForm(request.form)
    # Cargar lista de proveedores para el formulario
    proveedores_lista = Proveedores.query.filter(Proveedores.estatus == 1).all()
    form.idProveedor.choices = [(p.idProveedor, p.nombreProveedor) for p in proveedores_lista]
    
    if request.method == "POST" and form.validate():
        id_insumo = request.form.get("idMateriaPrima")
        if id_insumo:
            return redirect(url_for("editar_insumo"))
        else:
            nuevo_insumo = MateriasPrimas(
                materiaPrima=form.materiaPrima.data,
                cantidadDisponible=0,  # Se asigna 0 al crear
                unidadMedida=form.unidadMedida.data,
                idProveedor=form.idProveedor.data,
                precioUnitario=form.precioUnitario.data
            )
            db.session.add(nuevo_insumo)
            db.session.commit()
            flash("Insumo creado correctamente", "success")
            return redirect(url_for("insumos"))
    
    insumos_lista = MateriasPrimas.query.filter(MateriasPrimas.estatus != 0).all()
    return render_template("admin/insumos.html", insumos=insumos_lista, form=form, proveedores=proveedores_lista, ultimo_login=current_user.ultimo_login)

# Endpoint para editar un insumo
# EDITAR INSUMO
@app.route("/editar_insumo", methods=["POST"])
@login_required
@role_required(['Admin'])
def editar_insumo():
    form = InsumoForm(request.form)
    # Cargar lista de proveedores para el formulario
    proveedores_lista = Proveedores.query.filter(Proveedores.estatus == 1).all()
    form.idProveedor.choices = [(p.idProveedor, p.nombreProveedor) for p in proveedores_lista]
    
    if request.method == "POST" and form.validate():
        # Recuperamos el ID del insumo que se desea editar (campo oculto en el formulario)
        id_insumo = request.form.get("idMateriaPrima")
        if id_insumo:
            insumo = MateriasPrimas.query.get(id_insumo)
            if insumo:
                # Actualizamos los campos
                insumo.materiaPrima = form.materiaPrima.data
                insumo.unidadMedida = form.unidadMedida.data
                insumo.idProveedor = form.idProveedor.data
                insumo.precioUnitario = form.precioUnitario.data
                # Se pueden actualizar otros campos como cantidad o fechaCaducidad si se requiere
                db.session.commit()
                flash("Insumo editado correctamente", "success")
            else:
                flash("Insumo no encontrado", "danger")
        else:
            flash("ID de insumo no proporcionado", "danger")
    else:
        flash("Error en la validación del formulario", "danger")
    
    return redirect(url_for("insumos"))

@app.route("/mermar_insumo/<int:id>/<merma>", methods=["GET"])
def mermar_insumo(id, merma):
    try:
        merma_val = Decimal(merma)  # Convertir a Decimal en lugar de float
    except ValueError:
        flash("Valor de merma no válido", "danger")
        return redirect(url_for("insumos"))
    
    insumo = MateriasPrimas.query.get(id)
    if insumo:
        nueva_cantidad = insumo.cantidadDisponible - merma_val
        insumo.cantidadDisponible = max(nueva_cantidad, 0)  # Evitar valores negativos
        db.session.commit()
        flash("Merma aplicada correctamente", "success")
    else:
        flash("Insumo no encontrado", "danger")
    return redirect(url_for("insumos"))


# COMPRAS INSUMOS
from decimal import Decimal

# INSERCIÓN DE COMPRAS DE INSUMOS
from decimal import Decimal

# INSERCIÓN DE COMPRAS DE INSUMOS
@app.route("/comprasInsumos", methods=["GET", "POST"])
@login_required
@role_required(['Admin'])
def comprasInsumos():
    form = CompraInsumoForm(request.form)
    # Cargar lista de insumos para el select
    insumos_lista = MateriasPrimas.query.filter(MateriasPrimas.estatus != 0).all()
    proveedores = Proveedores.query.all()
    form.idMateriaPrima.choices = [(insumo.idMateriaPrima, insumo.materiaPrima) for insumo in insumos_lista]

    if request.method == "POST" and form.validate():
        id_materia = form.idMateriaPrima.data
        insumo = MateriasPrimas.query.get(id_materia)
        
        if insumo:
            id_proveedor = insumo.idProveedor
            precio_unitario = insumo.precioUnitario
            unidad = insumo.unidadMedida.strip().lower()
            cantidad_ingresada = Decimal(form.cantidad.data)

            # Ajustar la cantidad según la unidad
            if unidad in ["gr", "ml"]:
                cantidad_ajustada = cantidad_ingresada * Decimal(1000)
            elif unidad == "pzs":
                cantidad_ajustada = cantidad_ingresada
            else:
                flash("Unidad de medida no válida para este insumo", "danger")
                return redirect(url_for("comprasInsumos"))

            # Calcular total
            total_compra = cantidad_ingresada * precio_unitario


            # INSERTAR la compra en la tabla de compras
            nueva_compra = ComprasInsumos(
            idProveedor=id_proveedor,
            idMateriaPrima=id_materia,
            cantidad=cantidad_ajustada,
            fecha=form.fecha.data,
            totalCompra=total_compra
            )
            db.session.add(nueva_compra)

            # ACTUALIZAR el insumo
            insumo.cantidadDisponible += cantidad_ajustada
            insumo.fechaCaducidad = form.fechaCaducidad.data

            db.session.commit()
            flash("Compra registrada y stock actualizado correctamente", "success")
            return redirect(url_for("comprasInsumos"))

        else:
            flash("Insumo no encontrado", "danger")

    compras_lista = db.session.execute(text("SELECT * FROM vista_compras_insumos")).fetchall()
    return render_template("admin/comprasInsumos.html", compras=compras_lista, form=form, ultimo_login=current_user.ultimo_login)

@app.route("/editar_compraInsumo", methods=["POST"])
def editar_compraInsumo():
    form = CompraInsumoForm(request.form)
    # Cargar los insumos activos para rellenar el select
    insumos = MateriasPrimas.query.filter(MateriasPrimas.estatus != 0).all()
    form.idMateriaPrima.choices = [(insumo.idMateriaPrima, insumo.materiaPrima) for insumo in insumos]
    
    # Obtener el id de la compra desde el campo oculto del formulario
    id_compra = request.form.get("idCompra")
    if not id_compra:
        flash("ID de compra no proporcionado", "danger")
        return redirect(url_for("comprasInsumos"))
    
    compra = ComprasInsumos.query.get(id_compra)
    if not compra:
        flash("Compra no encontrada", "danger")
        return redirect(url_for("comprasInsumos"))
    
    try:
        # Log de los valores originales
        print(f"[DEBUG] Compra original: idMateriaPrima={compra.idMateriaPrima}, cantidad={compra.cantidad}")
        
        # Revertir la cantidad añadida anteriormente al stock del insumo anterior
        insumo_anterior = MateriasPrimas.query.get(compra.idMateriaPrima)
        if insumo_anterior:
            insumo_anterior.cantidadDisponible = Decimal(insumo_anterior.cantidadDisponible) - Decimal(compra.cantidad)
        
        # Obtener el nuevo insumo seleccionado
        insumo_nuevo = MateriasPrimas.query.get(form.idMateriaPrima.data)
        if not insumo_nuevo:
            flash("Insumo seleccionado no encontrado", "danger")
            return redirect(url_for("comprasInsumos"))
        
        precio_unitario = insumo_nuevo.precioUnitario
        
        # Calcular el total de la compra con la nueva cantidad
        total_compra = Decimal(form.cantidad.data) * Decimal(precio_unitario)
        
        # Actualizar los datos de la compra
        compra.idMateriaPrima = int(form.idMateriaPrima.data)
        compra.cantidad = Decimal(form.cantidad.data)
        compra.fecha = form.fecha.data
        compra.fechaCaducidad = form.fechaCaducidad.data
        compra.totalCompra = total_compra
        
        # Actualizar la cantidad disponible del nuevo insumo
        insumo_nuevo.cantidadDisponible = Decimal(insumo_nuevo.cantidadDisponible) + Decimal(form.cantidad.data)
        
        # Log de los nuevos valores
        print(f"[DEBUG] Compra nueva: idMateriaPrima={compra.idMateriaPrima}, cantidad={compra.cantidad}, totalCompra={compra.totalCompra}")
        print(f"[DEBUG] Insumo nuevo stock: {insumo_nuevo.cantidadDisponible}")
        
        db.session.commit()
        flash("¡Compra actualizada con éxito!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Error al actualizar la compra: " + str(e), "danger")
    
    return redirect(url_for("comprasInsumos"))


#!============================== Modulo de Proveedores ==============================#

#Endpoint para proveedores
@app.route("/proveedores", methods=["GET", "POST"])
@login_required
@role_required(['Admin'])
def proveedores():
    form = ProveedorForm(request.form)
    if request.method == "POST" and form.validate():
        # Si existe un id en el formulario, se trata de una edición
        id_prov = request.form.get("idProveedor")
        if id_prov:
            # Redirige al endpoint de edición
            return redirect(url_for("editar_proveedor"))
        else:
            # Inserción de un nuevo proveedor
            nuevo_proveedor = Proveedores(
                nombreProveedor=form.nombreProveedor.data,
                correo=form.correo.data,
                telefono=form.telefono.data,
                estatus=1  # Activo
            )
            db.session.add(nuevo_proveedor)
            db.session.commit()
            flash("Proveedor creado correctamente", "success")
            return redirect(url_for("proveedores"))
    # Consulta de proveedores activos (estatus distinto de 0)
    proveedores_lista = Proveedores.query.filter(Proveedores.estatus != 0).all()
    return render_template("admin/proveedores.html", proveedores=proveedores_lista, form=form, ultimo_login=current_user.ultimo_login)

@app.route("/editar_proveedor", methods=["POST"])
def editar_proveedor():
    form = ProveedorForm(request.form)
    id_prov = request.form.get("idProveedor")
    if id_prov and form.validate():
        proveedor = Proveedores.query.get(id_prov)
        if proveedor:
            proveedor.nombreProveedor = form.nombreProveedor.data
            proveedor.correo = form.correo.data
            proveedor.telefono = form.telefono.data
            db.session.commit()
            flash("Proveedor actualizado correctamente", "success")
        else:
            flash("Proveedor no encontrado", "danger")
    else:
        flash("Error en la validación del formulario", "danger")
    return redirect(url_for("proveedores"))

@app.route("/eliminar_proveedor/<int:id>", methods=["GET"])
def eliminar_proveedor(id):
    proveedor = Proveedores.query.get(id)
    if proveedor:
        proveedor.estatus = 0  # Eliminación lógica
        db.session.commit()
        flash("Proveedor eliminado correctamente", "success")
    else:
        flash("Proveedor no encontrado", "danger")
    return redirect(url_for("proveedores"))


#!============================== Modulo de Ventas ==============================#
# Venta actual (lista de productos en la venta)
venta_actual = []

@app.route("/puntoVenta", methods=["GET", "POST"])
@login_required
@role_required(['Admin', 'Ventas'])
def puntoVenta():
    # Consulta de productos disponibles: obtenemos el id, nombre de receta, tipo, cantidad y precio.
    productos_disponibles = db.session.query(
        ProductosTerminados.idProducto,
        Receta.nombreReceta,
        ProductosTerminados.tipoProducto,
        ProductosTerminados.cantidadDisponible,
        Receta.precio
    ).join(Receta, ProductosTerminados.idReceta == Receta.idReceta)\
    .filter(ProductosTerminados.estatus == 1, ProductosTerminados.cantidadDisponible > 0)\
    .order_by(ProductosTerminados.idProducto.asc()).all()

    ventas_estatus_1 = VentasCliente.query.filter_by(estatus=1).all()

    # Se pueden usar los mismos productos para el select, pues contienen nombre y tipo
    # Si lo prefieres, también puedes pasar la lista completa de recetas:
    # recetas = Receta.query.all()
    
    if request.method == "POST":
        accion = request.form.get("accion")
        
        if accion == "agregar":
            try:
                idProducto = int(request.form.get("idProducto"))
                cantidad = int(request.form.get("cantidad"))
            except (ValueError, TypeError):
                flash("Datos inválidos para agregar producto.", "danger")
                return redirect(url_for("puntoVenta"))
            
            if cantidad <= 0:
                flash("La cantidad debe ser mayor a cero.", "danger")
                return redirect(url_for("puntoVenta"))
            
            productoTerminado = ProductosTerminados.query.filter_by(
                idProducto=idProducto,
                estatus=1
            ).filter(ProductosTerminados.cantidadDisponible > 0).first()
            
            if not productoTerminado:
                flash("Producto terminado no encontrado o no disponible.", "danger")
                return redirect(url_for("puntoVenta"))
            
            receta = Receta.query.get(productoTerminado.idReceta)
            if not receta:
                flash("Receta asociada no encontrada.", "danger")
                return redirect(url_for("puntoVenta"))
            
            # Evitar duplicados en la venta
            for prod in venta_actual:
                if prod["idProducto"] == idProducto:
                    flash("El producto ya está en la venta.", "warning")
                    return redirect(url_for("puntoVenta"))
            
            if productoTerminado.tipoProducto.lower() == "medio kilo":
                factor = 12
            elif productoTerminado.tipoProducto.lower() == "kilo":
                factor = 24
            else:
                factor = 1 

            precio_unitario = float(receta.precio) * factor
            precio_total = precio_unitario * cantidad

            producto = {
                "idProducto": idProducto,
                "nombreReceta": receta.nombreReceta,
                "tipoProducto": productoTerminado.tipoProducto,
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
                "precio_total": precio_total
            }
            
            venta_actual.append(producto)
            flash("Producto agregado correctamente.", "success")
            return redirect(url_for("puntoVenta"))
        
        elif accion == "actualizar":
            try:
                idProducto = int(request.form.get("idProducto"))
            except (ValueError, TypeError):
                flash("Datos inválidos para actualizar producto.", "danger")
                return redirect(url_for("puntoVenta"))
            
            operacion = request.form.get("operacion")
            for prod in venta_actual:
                if prod["idProducto"] == idProducto:
                    if operacion == "subir":
                        prod["cantidad"] += 1
                    elif operacion == "bajar":
                        prod["cantidad"] -= 1
                        if prod["cantidad"] <= 0:
                            venta_actual.remove(prod)
                            flash("Producto eliminado.", "warning")
                            break
                    if prod in venta_actual:
                        prod["precio_total"] = prod["cantidad"] * prod["precio_unitario"]
                    flash("Producto actualizado.", "success")
                    break
            else:
                flash("Producto no encontrado.", "danger")
            return redirect(url_for("puntoVenta"))
        
        elif accion == "confirmar":
            try:
                descuento = float(request.form.get("descuento", 0))
                dinero_recibido = float(request.form.get("dinero_recibido"))
            except (ValueError, TypeError):
                flash("Datos de confirmación inválidos.", "danger")
                return redirect(url_for("puntoVenta"))

            total = sum(prod["precio_total"] for prod in venta_actual)
            total_con_descuento = total - (total * (descuento / 100))

            if dinero_recibido < total_con_descuento:
                flash("El dinero recibido no es suficiente.", "danger")
                return redirect(url_for("puntoVenta"))

            # Verifica y descuenta del inventario
            for prod in venta_actual:
                productoTerminado = ProductosTerminados.query.filter_by(
                    idProducto=prod["idProducto"],
                    estatus=1
                ).filter(ProductosTerminados.cantidadDisponible >= prod["cantidad"]).first()
                if productoTerminado is None:
                    flash(f"Inventario insuficiente o producto no encontrado para {prod['nombreReceta']}.", "danger")
                    return redirect(url_for("puntoVenta"))
                productoTerminado.cantidadDisponible -= prod["cantidad"]
            db.session.commit()

            nueva_venta = Ventas(total=total_con_descuento)
            db.session.add(nueva_venta)
            db.session.flush()

            for prod in venta_actual:
                detalle = DetallesVenta(
                    idVenta=nueva_venta.idVenta,
                    idProducto=prod["idProducto"],
                    cantidad=prod["cantidad"],
                    subtotal=prod["precio_total"]
                )
                db.session.add(detalle)

                # === Aquí guardamos en la tabla VentasCliente ===
                venta_cliente = VentasCliente(
                    nombreCliente="Público en general", 
                    nombreSabor=prod["nombreReceta"],
                    cantidad=prod["cantidad"],
                    tipoProducto=prod["tipoProducto"],
                    total=prod["precio_total"],
                    estatus=2
                )
                db.session.add(venta_cliente)

            db.session.commit()

            pdf_path = generar_pdf(venta_actual, descuento, dinero_recibido, total_con_descuento)
            flash("Venta confirmada. Ticket generado en: " + pdf_path, "success")
            venta_actual.clear()
            return redirect(url_for("puntoVenta"))
    
    productos = ProductosTerminados.query.filter(
        ProductosTerminados.estatus == 1,
        ProductosTerminados.cantidadDisponible > 0
    ).all()
    inventario = {producto.idProducto: producto.cantidadDisponible for producto in productos}

    total = sum(prod["precio_total"] for prod in venta_actual)

    return render_template("admin/ventas.html",
                        productos_disponibles=productos_disponibles,
                        venta=venta_actual,
                        total=total,
                        inventario=inventario,
                        ventas_estatus_1=ventas_estatus_1,
                        ultimo_login=current_user.ultimo_login)


def generar_pdf(venta, descuento, dinero_recibido, total_con_descuento):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Dulce Rebaño", ln=True, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, "Ticket de Compra", ln=True, align="C")
    pdf.line(10, 30, 200, 30)
    now = date.today()
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 10, f"Fecha: {now.strftime('%d/%m/%Y')}", ln=True)
    pdf.cell(0, 10, f"Hora: {now.strftime('%H:%M:%S')}", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(50, 10, "Receta", border=1)
    pdf.cell(50, 10, "Tipo", border=1)
    pdf.cell(30, 10, "Cant.", border=1, align="R")
    pdf.cell(30, 10, "Precio", border=1, align="R")
    pdf.ln()
    pdf.set_font("Helvetica", "", 12)
    for prod in venta:
        pdf.cell(50, 10, prod["nombreReceta"], border=1)
        pdf.cell(50, 10, prod["tipoProducto"], border=1)
        pdf.cell(30, 10, str(prod["cantidad"]), border=1, align="R")
        pdf.cell(30, 10, f"${prod['precio_total']:.2f}", border=1, align="R")
        pdf.ln()
    pdf.ln(5)
    if descuento > 0:
        pdf.cell(0, 10, f"Descuento aplicado: {descuento}%", ln=True)
    pdf.cell(0, 10, f"Total con descuento: ${total_con_descuento:.2f}", ln=True, align="R")
    pdf.cell(0, 10, f"Dinero recibido: ${dinero_recibido:.2f}", ln=True, align="R")
    cambio = dinero_recibido - total_con_descuento
    pdf.cell(0, 10, f"Cambio: ${cambio:.2f}", ln=True, align="R")
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 10, "¡Gracias por su compra!", ln=True, align="C")

    path = "ticket.pdf"
    pdf.output(path)
    return path

#!============================== Login ==============================#

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        correo = form.correo.data
        contrasena = form.contrasena.data
        now = datetime.now()

        # Verificar intentos fallidos previos
        if correo in failed_attempts:
            last_attempt_time, attempts = failed_attempts[correo]
            
            # Si han pasado más de 1 minuto desde el último intento, reiniciar el contador
            if now - last_attempt_time > timedelta(minutes=1):
                failed_attempts[correo] = (now, 1)
            # Si hay 3 o más intentos en menos de 1 minuto
            elif attempts >= 3:
                flash('Demasiados intentos fallidos. Por favor, espera un minuto antes de intentar nuevamente.', 'danger')
                return render_template("client/mainClientes.html", 
                                    login_form=form, 
                                    register_form=RegisterForm(),
                                    recuperar_contrasena_form=RecuperarContrasenaForm(),
                                    show_modal=True)
        else:
            # Primer intento fallido para este correo
            failed_attempts[correo] = (now, 0)

        usuario = Usuarios.query.filter_by(correo=correo).first()

        if usuario:
            if usuario.activo != 1:
                flash('Tu cuenta ha sido desactivada. Por favor, contacta al administrador.', 'danger')
                return render_template("client/mainClientes.html", login_form=form, register_form=RegisterForm())

        if usuario and usuario.check_contrasena(contrasena):
            # Login exitoso - resetear intentos fallidos
            if correo in failed_attempts:
                del failed_attempts[correo]
            
            login_user(usuario) 
            usuario.ultimo_login = now
            db.session.commit()
                
            if usuario.rol == 'Cliente':
                return redirect(url_for('clientes'))
            elif usuario.rol == 'Ventas':
                return redirect(url_for('puntoVenta', _anchor='login-success'))
            elif usuario.rol == 'Admin':
                return redirect(url_for('miembros', _anchor='login-success'))
            elif usuario.rol == 'Produccion':
                return redirect(url_for('galletas', _anchor='login-success'))
        else:
            # Login fallido - incrementar contador
            if correo in failed_attempts:
                last_time, attempts = failed_attempts[correo]
                failed_attempts[correo] = (now, attempts + 1)
            else:
                failed_attempts[correo] = (now, 1)
            
            flash('Correo o contraseña incorrectos. Por favor, intenta de nuevo.', 'danger')
            return render_template("client/mainClientes.html", 
                                login_form=form, 
                                register_form=RegisterForm(),
                                recuperar_contrasena_form=RecuperarContrasenaForm(),
                                show_modal=True)
    
    if form.errors:
        return render_template("client/mainClientes.html", 
                            login_form=form, 
                            register_form=RegisterForm(),
                            recuperar_contrasena_form=RecuperarContrasenaForm(),
                            show_modal=True)
    
    return render_template("client/mainClientes.html", 
                        login_form=form, 
                        register_form=RegisterForm(),
                        recuperar_contrasena_form=RecuperarContrasenaForm())

@app.route("/logout")
@login_required 
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('login'))


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    login_form = LoginForm()
    recuperar_contrasena_form = RecuperarContrasenaForm()
    
    if form.validate_on_submit():
        nombre = form.nombre.data
        apaterno = form.apaterno.data
        amaterno = form.amaterno.data
        correo = form.correo.data
        contrasena = form.contrasena.data

        if is_password_insecure(contrasena):
            flash('La contraseña es insegura. Por favor, elige una contraseña más segura.', 'danger')
            return render_template("client/mainClientes.html", 
                                login_form=login_form, 
                                register_form=form,
                                recuperar_contrasena_form=recuperar_contrasena_form,
                                show_modal=True,
                                active_tab='register')

        usuario_existente = Usuarios.query.filter_by(correo=correo).first()
        if usuario_existente:
            flash('El correo ya está registrado. Por favor, utiliza otro correo.', 'danger')
            return render_template("client/mainClientes.html", 
                                login_form=login_form, 
                                register_form=form,
                                recuperar_contrasena_form=recuperar_contrasena_form,
                                show_modal=True,
                                active_tab='register')
        
        # Generar secreto OTP
        otp_secret = pyotp.random_base32()
        
        # Crear usuario temporal con datos de registro
        temp_user = Usuarios(
            nombre=form.nombre.data,
            apaterno=form.apaterno.data,
            amaterno=form.amaterno.data,
            correo=form.correo.data,
            otp_secret=otp_secret,
            registration_data=json.dumps({
                'contrasena': form.contrasena.data,
                'rol': 'Cliente',
                'activo': 1
            }),
            activo=0  # Inactivo hasta verificación OTP
        )
        
        try:
            db.session.add(temp_user)
            db.session.commit()
            
            # Generar y enviar código OTP
            totp = pyotp.TOTP(temp_user.otp_secret, interval=600)
            otp_code = totp.now()
            
            # Enviar correo con el código OTP
            msg = Message(
                subject="Código de verificación para tu registro en Dulce Rebaño",
                recipients=[temp_user.correo],
                html=f"""
                <h2>Verificación de correo electrónico</h2>
                <p>Gracias por registrarte en Dulce Rebaño. Tu código de verificación es:</p>
                <h3 style="background: #f0f0f0; padding: 10px; display: inline-block; border-radius: 5px;">
                    {otp_code}
                </h3>
                <p>Este código expirará en 10 minutos.</p>
                """
            )
            mail.send(msg)
            
            flash('Se ha enviado un código de verificación a tu correo electrónico.', 'success')
            return redirect(url_for('verify_otp', user_id=temp_user.idUsuario))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar: {str(e)}', 'danger')
            return render_template("client/mainClientes.html", 
                                login_form=login_form, 
                                register_form=form,
                                recuperar_contrasena_form=recuperar_contrasena_form,
                                show_modal=True,
                                active_tab='register')
    
    if form.errors:
        return render_template("client/mainClientes.html", 
                            login_form=login_form, 
                            register_form=form,
                            recuperar_contrasena_form=recuperar_contrasena_form,
                            show_modal=True,
                            active_tab='register')
    
    return render_template("client/mainClientes.html", 
                        login_form=login_form, 
                        register_form=form,
                        recuperar_contrasena_form=recuperar_contrasena_form,
                        show_modal=True,
                        active_tab='register')

@app.route("/verify-otp/<int:user_id>", methods=["GET", "POST"])
def verify_otp(user_id):
    form = OTPVerificationForm()
    user = Usuarios.query.get_or_404(user_id)
    
    if form.validate_on_submit():
        # Usar el mismo intervalo (600 segundos) que en el registro
        totp = pyotp.TOTP(user.otp_secret, interval=600)
        
        # Verificar con un margen de 1 código (10 minutos en total)
        if totp.verify(form.otp_code.data, valid_window=1):
            # OTP válido, activar la cuenta
            try:
                reg_data = json.loads(user.registration_data)
                user.set_contrasena(reg_data['contrasena'])
                user.rol = reg_data['rol']
                user.activo = 1
                user.otp_verified = True
                user.registration_data = None  # Limpiar datos temporales
                
                db.session.commit()
                
                flash('¡Registro completado con éxito! Ahora puedes iniciar sesión.', 'success')
                return redirect(url_for('index'))
                
            except Exception as e:
                db.session.rollback()
                flash('Error al completar el registro. Por favor intenta nuevamente.', 'danger')
                return redirect(url_for('verify_otp', user_id=user_id))
        else:
            flash('Código OTP inválido o expirado. Por favor, intenta de nuevo.', 'danger')
    
    return render_template("client/verify_otp.html", form=form, user_id=user_id)


@app.route("/miembros", methods=["GET", "POST"])
@login_required
@role_required(['Admin'])
def miembros():
    form = EmpleadoForm()
    usuarios = Usuarios.query.filter_by(activo=1)\
                .filter(Usuarios.rol != 'Cliente')\
                .order_by(Usuarios.rol.desc())\
                .all()

    if form.validate_on_submit():
        nombre = form.nombre.data
        apaterno = form.apaterno.data
        amaterno = form.amaterno.data
        correo = form.correo.data
        contrasena = form.contrasena.data
        rol = form.rol.data

        if is_password_insecure(contrasena):
            flash('La contraseña es insegura. Por favor, elige una contraseña más segura.', 'danger')
            return render_template("admin/usuarios.html", form=form, usuarios=usuarios, ultimo_login=current_user.ultimo_login)

        usuario_existente = Usuarios.query.filter_by(correo=correo).first()
        if usuario_existente:
            flash('El correo ya está registrado. Por favor, utiliza otro correo.', 'danger')
        else:
            nuevo_usuario = Usuarios(nombre=nombre, apaterno=apaterno, amaterno=amaterno, correo=correo, rol=rol)
            nuevo_usuario.set_contrasena(contrasena)
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash('Usuario registrado exitosamente.', 'success')
        return redirect(url_for('miembros'))

    return render_template("admin/usuarios.html", form=form, usuarios=usuarios, ultimo_login=current_user.ultimo_login)

@app.route("/eliminar_usuario/<int:id_usuario>", methods=["POST"])
@login_required
def eliminar_usuario(id_usuario):
    usuario = Usuarios.query.get(id_usuario)
    if usuario:
        usuario.activo = 0 
        db.session.commit()
        flash('Usuario eliminado correctamente.', 'success')
    else:
        flash('Usuario no encontrado.', 'danger')
    return redirect(url_for('miembros'))


@app.route("/editar_usuario/<int:id_usuario>", methods=["POST"])
@login_required
@role_required(['Admin'])
def editar_usuario(id_usuario):
    usuario = Usuarios.query.get_or_404(id_usuario)
    
    usuario.nombre = request.form.get('nombre')
    usuario.apaterno = request.form.get('apaterno')
    usuario.amaterno = request.form.get('amaterno')
    usuario.correo = request.form.get('correo')

    if usuario.rol != 'Admin':
        usuario.rol = request.form.get('rol')
        usuario.activo = int(request.form.get('activo', 1))  # Default: Activo
    
    db.session.commit()
    flash('Usuario actualizado correctamente.', 'success')
    return redirect(url_for('miembros'))


@app.route("/recuperar_contrasena", methods=["POST"])
def recuperar_contrasena():
    form = RecuperarContrasenaForm()
    login_form = LoginForm()
    register_form = RegisterForm()
    
    if form.validate_on_submit():
        correo = form.correo.data
        nueva_contrasena = form.nueva_contrasena.data
        confirmar_contrasena = form.confirmar_contrasena.data

        usuario = Usuarios.query.filter_by(correo=correo).first()
        if not usuario:
            flash('El correo no está registrado.', 'recuperar_error')
            return redirect(url_for('index', show_recuperar_modal=True))

        if nueva_contrasena != confirmar_contrasena:
            flash('Las contraseñas no coinciden.', 'recuperar_error')
            return redirect(url_for('index', show_recuperar_modal=True))

        if is_password_insecure(nueva_contrasena):
            flash('La contraseña es insegura. Por favor, elige una contraseña más segura.', 'recuperar_error')
            return redirect(url_for('index', show_recuperar_modal=True))

        usuario.set_contrasena(nueva_contrasena)
        db.session.commit()
        flash('Contraseña actualizada correctamente. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('index'))

    # Si hay errores de validación del formulario
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{error}', 'recuperar_error')
    
    return redirect(url_for('index', show_recuperar_modal=True))


def is_password_insecure(contrasena):
    with open('insecure_passwords.txt', 'r') as file:
        insecure_passwords = [line.strip() for line in file]
    return contrasena in insecure_passwords


@app.before_request
def before_request():
    if current_user.is_authenticated:
        if current_user.rol == 'Cliente':
            session.permanent = True
            app.permanent_session_lifetime = timedelta(minutes=60)
        else:
            session.permanent = True
            app.permanent_session_lifetime = timedelta(days=100)  
        session.modified = True

if __name__ == '__main__':
    csrf.init_app(app)
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    app.run()