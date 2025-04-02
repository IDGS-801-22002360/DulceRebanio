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
from logger import action_logger

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
    return render_template("client/mainClientes.html", 
                        login_form=login_form, 
                        register_form=register_form,
                        recuperar_contrasena_form=recuperar_contrasena_form,
                        show_recuperar_modal=show_recuperar_modal)

#!============================== Modulo Carrito que no es carrito ==============================#

@app.route("/clientes", methods=["GET", "POST"])
@login_required
@role_required(["Cliente", "Admin"])
def clientes():
    tipo_seleccionado = request.args.get("tipo", "todos")  
    
    #sabores = Sabores.query.join(ProductosTerminados).filter(ProductosTerminados.cantidadDisponible > 0).distinct().all()

    tipos_productos = [producto.tipoProducto for producto in DetallesProducto.query.distinct(DetallesProducto.tipoProducto)]
    if tipo_seleccionado == "todos":
        detalles_productos = DetallesProducto.query.join(ProductosTerminados).filter(ProductosTerminados.cantidadDisponible > 0).distinct().all()
    else:
        detalles_productos = DetallesProducto.query.join(ProductosTerminados).filter(DetallesProducto.tipoProducto == tipo_seleccionado, ProductosTerminados.cantidadDisponible > 0).distinct().all()

    if "carrito" not in session:
        session["carrito"] = []

    return render_template("client/clientes.html", detalles_productos=detalles_productos, tipos_productos=tipos_productos, carrito=session["carrito"], ultimo_login=current_user.ultimo_login)

@app.route("/agregar_carrito", methods=["POST"])
def agregar_carrito():
    sabor_id = request.form.get("sabor_id")
    tipo_producto = request.form.get("tipo_producto")
    cantidad = int(request.form.get("cantidad", 1))

    #sabor = Sabores.query.get(sabor_id)
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
    return redirect(url_for("clientes"))

@app.route("/eliminar_carrito/<int:item_id>", methods=["POST"])
def eliminar_carrito(item_id):
    session["carrito"] = [item for item in session["carrito"] if item["id"] != item_id]
    total_general = sum(item["subtotal"] for item in session["carrito"])
    session["total_general"] = float(total_general)  

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

        # Obtener los lotes disponibles en orden de inserción
        lotes = ProductosTerminados.query.filter_by(idSabor=item["id"]).order_by("idSabor").all()

        cantidad_restante = item["cantidad"]
        for lote in lotes:
            if cantidad_restante <= 0:
                break  # Ya se descontó toda la cantidad necesaria

            if lote.cantidadDisponible >= cantidad_restante:
                lote.cantidadDisponible -= cantidad_restante
                cantidad_restante = 0
            else:
                cantidad_restante -= lote.cantidadDisponible
                lote.cantidadDisponible = 0

            db.session.commit()

        if cantidad_restante > 0:
            flash(f"No hay suficiente stock para {item['nombre']} ({item['tipo']})", "danger")
            return redirect(url_for("clientes"))

    db.session.commit()
    print("Compra procesada correctamente con estatus 1")  

    session["carrito"] = []
    flash("¡Compra realizada con éxito!", "success")
    return redirect(url_for("clientes"))


@app.route("/historial", methods=["GET"])
def historialCompras():
    if not current_user.is_authenticated:
        flash("Debes iniciar sesión para ver tu historial de compras", "warning")
        return redirect(url_for("login"))  

    ventas = VentasCliente.query.filter_by(nombreCliente=current_user.nombre).all()  

    return render_template("client/historial.html", ventas=ventas)

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

    return render_template("admin/dashboard.html", 
                        ventas_combinadas=todas_las_ventas,
                        productos_labels=productos_labels, 
                        productos_data=productos_data,
                        presentaciones_labels=presentaciones_labels, 
                        presentaciones_data=presentaciones_data,
                        ultimo_login=current_user.ultimo_login)


#!============================== Modulo de Productos ==============================#  

@app.route("/galletas", methods=["GET", "POST"])
@login_required  
@role_required(['Admin', 'Ventas', 'Produccion'])
def galletas():
    #form = LoteForm()
    #paquete_form = PaqueteForm()
    #form.sabor.choices = [(sabor.idSabor, sabor.nombreSabor) for sabor in Sabores.query.all()]
    #
    ##* Estas son unicamente las galletas a granel
    #productos_granel = db.session.query(
    #    ProductosTerminados.idProducto,
    #    #Sabores.nombreSabor,
    #    DetallesProducto.tipoProducto,
    #    ProductosTerminados.cantidadDisponible
    #).join(ProductosTerminados.idSabor == Sabores.idSabor)\
    #.join(DetallesProducto, ProductosTerminados.idDetalle == DetallesProducto.idDetalle)\
    #.filter(ProductosTerminados.idDetalle == 1, ProductosTerminados.estatus == 1).all()
    #
    #today = date.today()
    #is_christmas_season = today.month == 12
    #
    #min_galletas = 60 if is_christmas_season else 30
    #min_paquetes = 6 if is_christmas_season else 3
#
    ##* Obtener todos los productos y marcar los de bajo stock
    #productos = db.session.query(
    #    ProductosTerminados.idProducto,
    #    Sabores.nombreSabor,
    #    DetallesProducto.tipoProducto,
    #    ProductosTerminados.fechaCaducidad,
    #    ProductosTerminados.cantidadDisponible,
    #    ProductosTerminados.estatus
    #).join(Sabores, ProductosTerminados.idSabor == Sabores.idSabor)\
    #.join(DetallesProducto, ProductosTerminados.idDetalle == DetallesProducto.idDetalle)\
    #.filter(ProductosTerminados.estatus == 1)\
    #.order_by(ProductosTerminados.idDetalle.asc()).all()
    #
    ##* Verificar productos con bajo stock
    #productos_bajo_stock = db.session.query(
    #    ProductosTerminados.idProducto,
    #    Sabores.nombreSabor,
    #    DetallesProducto.tipoProducto,
    #    ProductosTerminados.cantidadDisponible
    #).join(Sabores, ProductosTerminados.idSabor == Sabores.idSabor)\
    #.join(DetallesProducto, ProductosTerminados.idDetalle == DetallesProducto.idDetalle)\
    #.filter(
    #    ProductosTerminados.estatus == 1,
    #    (ProductosTerminados.idDetalle == 1) & (ProductosTerminados.cantidadDisponible < min_galletas) |
    #    (ProductosTerminados.idDetalle.in_([2, 3]) & (ProductosTerminados.cantidadDisponible < min_paquetes))
    #).all()
#
    #for producto in productos_bajo_stock:
    #    flash(f"¡Alerta! Bajo stock: {producto.nombreSabor} ({producto.tipoProducto}) - Cantidad: {producto.cantidadDisponible}", "warning")
#
    #productos_marcados = []
    #for producto in productos:
    #    bajo_stock = (
    #        (producto.tipoProducto == "Granel" and producto.cantidadDisponible < min_galletas) or
    #        (producto.tipoProducto in ["Kilo", "Med. Kilo"] and producto.cantidadDisponible < min_paquetes)
    #    )
    #    productos_marcados.append({
    #        "idProducto": producto.idProducto,
    #        "nombreSabor": producto.nombreSabor,
    #        "tipoProducto": producto.tipoProducto,
    #        "fechaCaducidad": producto.fechaCaducidad,
    #        "cantidadDisponible": producto.cantidadDisponible,
    #        "estatus": producto.estatus,
    #        "bajo_stock": bajo_stock
    #    })
#
    return render_template(
        "admin/galletas.html",
        #productos=productos_marcados,
        #productos_granel=productos_granel,
        #form=form,
        #paquete_form=paquete_form, ultimo_login=current_user.ultimo_login
    )

@app.route("/guardarLote", methods=["POST"])
def guardarLote():
    #form = LoteForm()
    #form.sabor.choices = [(sabor.idSabor, sabor.nombreSabor) for sabor in Sabores.query.all()]
    #
    #if form.validate_on_submit():
    #    try:
    #        print("Formulario validado correctamente")
    #        sabor_id = form.sabor.data
    #        id_detalle = 1
    #        print(f"Sabor seleccionado: {sabor_id}")
#
    #        nuevo_producto = ProductosTerminados(
    #            idSabor=sabor_id,
    #            cantidadDisponible=150,
    #            fechaCaducidad=date.today() + timedelta(days=7),
    #            idDetalle=id_detalle,
    #            estatus=1
    #        )
    #        db.session.add(nuevo_producto)
    #        print("Producto terminado agregado a la sesión")
    #        
    #        insumos = {
    #            2: Decimal("0.9"),  # Harina (kg)
    #            3: Decimal("3"),    # Huevos (pzs)
    #            4: Decimal("0.3"),  # Azúcar (kg)
    #            7: Decimal("0.45"), # Mantequilla (kg)
    #            5: Decimal("0.015") # Sal (kg)
    #        }
    #        
    #        for id_materia, cantidad_usada in insumos.items():
    #            materia_prima = MateriasPrimas.query.get(id_materia)
    #            print(f"Procesando materia prima ID {id_materia}, Cantidad disponible: {materia_prima.cantidadDisponible}")
    #            if materia_prima and materia_prima.cantidadDisponible >= cantidad_usada:
    #                materia_prima.cantidadDisponible -= cantidad_usada
    #                print(f"Nueva cantidad disponible para ID {id_materia}: {materia_prima.cantidadDisponible}")
    #            else:
    #                print(f"Error: No hay suficiente {materia_prima.materiaPrima} en inventario o ID no encontrado")
    #                flash(f'No hay suficiente {materia_prima.materiaPrima} en inventario.', 'danger')
    #                return redirect(url_for('galletas'))
    #        
    #        db.session.commit()
    #        print("Transacción confirmada y datos guardados correctamente")
#
    #        action_logger.info(f"Usuario: {current_user.correo} - Acción: Guardar lote - Sabor: {nuevo_producto.idSabor} - Cantidad: {nuevo_producto.cantidadDisponible} - Fecha: {datetime.now()}")
    #        
    #        flash('Lote guardado y materias primas descontadas correctamente', 'success')
    #    except Exception as e:
    #        db.session.rollback()
    #        print(f"Error en guardarLote: {str(e)}")
    #        flash(f'Error al guardar el lote: {str(e)}', 'danger')
    #    return redirect(url_for('galletas'))
#
    #print("Error: El formulario no pasó la validación")
    #flash('Error al guardar el lote. Verifica los datos ingresados.', 'danger')
    return redirect(url_for('galletas'))


@app.route("/mermar", methods=["POST"])
def mermar():
    form = MermaForm()
    if form.validate_on_submit():
        id_producto = form.idProducto.data
        cantidad = form.cantidad.data
        mermar_todo = form.mermar_todo.data
        
        if mermar_todo:
            cantidad = None
        elif cantidad is None or cantidad == '':
            flash('Debe ingresar una cantidad válida', 'danger')
            return redirect(url_for('galletas'))
        
        if cantidad is not None:
            cantidad = int(cantidad)
            if cantidad <= 0:
                flash('La cantidad debe ser mayor a 0', 'danger')
                return redirect(url_for('galletas'))
        
        producto = ProductosTerminados.query.get(id_producto)
        if not producto:
            flash('Producto no encontrado', 'danger')
            return redirect(url_for('galletas'))
        
        if cantidad is None or cantidad >= producto.cantidadDisponible:
            cantidad_mermada = producto.cantidadDisponible
            producto.cantidadDisponible = 0
            producto.estatus = 0
        else:
            cantidad_mermada = cantidad
            producto.cantidadDisponible -= cantidad

        db.session.commit()

        #! Log de la acción para mermar cualquier producto
        action_logger.info(f"Usuario: {current_user.correo} - Acción: Mermar producto - Producto ID: {producto.idProducto} - Cantidad mermada: {cantidad_mermada} - Fecha: {datetime.now()}")

        flash('Producto mermado correctamente', 'success')
        return redirect(url_for('galletas'))

    flash('Error al mermar el producto', 'danger')
    return redirect(url_for('galletas'))

@app.route("/guardar_paquete", methods=["POST"])
def guardar_paquete():
    paquete_form = PaqueteForm()
    if paquete_form.validate_on_submit():
        tipo_producto = paquete_form.tipo_producto.data  # 2 = Kilo, 3 = Medio Kilo
        cantidad_paquetes = paquete_form.cantidad.data
        id_producto = request.form.get("txtIdGalletaGranel")  # ID del lote seleccionado

        producto = ProductosTerminados.query.get(id_producto)
        if not producto:
            flash("El lote seleccionado no existe.", "danger")
            return redirect(url_for("galletas"))

        galletas_por_paquete = 24 if tipo_producto == 2 else 12
        galletas_necesarias = galletas_por_paquete * cantidad_paquetes

        if producto.cantidadDisponible < galletas_necesarias:
            flash("No hay suficientes galletas en el lote seleccionado.", "danger")
            return redirect(url_for("galletas"))

        producto.cantidadDisponible -= galletas_necesarias
        if producto.cantidadDisponible == 0:
            producto.estatus = 0

        nuevo_paquete = ProductosTerminados(
            idSabor=producto.idSabor,
            cantidadDisponible=cantidad_paquetes,
            fechaCaducidad=producto.fechaCaducidad,
            idDetalle=tipo_producto,
            estatus=1
        )
        db.session.add(nuevo_paquete)
        db.session.commit()

        #! Log de la acción para crear paquetes 
        action_logger.info(f"Usuario: {current_user.correo} - Acción: Guardar paquete - Sabor: {nuevo_paquete.idSabor} - Tipo: {tipo_producto} - Cantidad: {cantidad_paquetes} - Fecha: {datetime.now()}")

        flash(f"Paquete creado correctamente: {cantidad_paquetes} paquetes de tipo {tipo_producto}.", "success")
        return redirect(url_for("galletas"))

    flash("Error al guardar el paquete. Verifica los datos ingresados.", "danger")
    return redirect(url_for("galletas"))



#!============================== Modulo de Recetas ==============================#  

@app.route('/recetas', methods=['GET', 'POST'])
@login_required
def recetas():
    if request.method == 'POST':
        # Manejar renombrado
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
    
    # Resto de tu lógica actual...
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
            RecetaDetalle.idMateriaPrima == MateriasPrimas.idMateriaPrima
        ).filter(
            RecetaDetalle.idReceta == id
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
    for key, value in request.form.items():
        if key.startswith('cantidad_'):
            detalle_id = key.split('_')[1]
            detalle = RecetaDetalle.query.get(detalle_id)
            if detalle:
                detalle.cantidad = float(value)
    db.session.commit()
    flash('Cambios guardados correctamente', 'success')
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

    nueva_receta = Receta(nombreReceta=nombre_receta, precio=7)  # Puedes ajustar el precio según sea necesario
    db.session.add(nueva_receta)
    db.session.commit()
    flash('Receta agregada correctamente', 'success')
    return redirect(url_for('recetas'))










@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#!============================== Modulo de Insumos ==============================#
#INSERCIÓN INSUMOS
@app.route("/insumos", methods=["GET", "POST"])
@login_required
@role_required(['Admin', 'Produccion'])
def insumos():
    form = InsumoForm(request.form)
    if request.method == "POST" and form.validate():
        
        id_insumo = request.form.get("idMateriaPrima")
        if id_insumo:
        
            return redirect(url_for("editar_insumo"))
        else:
            nuevo_insumo = MateriasPrimas(
                materiaPrima=form.materiaPrima.data,
                cantidadDisponible=0,  # Se asigna 0 al crear
                unidadMedida=form.unidadMedida.data,
                fechaCaducidad=form.fechaCaducidad.data
            )
            db.session.add(nuevo_insumo)
            db.session.commit()
            flash("Insumo creado correctamente", "success")
            return redirect(url_for("insumos"))
    
    insumos_lista = MateriasPrimas.query.filter(MateriasPrimas.estatus != 0).all()
    return render_template("admin/insumos.html", insumos=insumos_lista, form=form, ultimo_login=current_user.ultimo_login)

# Endpoint para editar un insumo
@app.route("/editar_insumo", methods=["POST"])
def editar_insumo():
    form = InsumoForm(request.form)
    id_insumo = request.form.get("idMateriaPrima")
    if id_insumo and form.validate():
        insumo = MateriasPrimas.query.get(id_insumo)
        if insumo:
            insumo.materiaPrima = form.materiaPrima.data
            nueva_unidad = form.unidadMedida.data
            insumo.fechaCaducidad = form.fechaCaducidad.data
            
            # Conversión automática entre unidades
            conversiones = {
                ("Kilogramos", "Gramos"): 1000,
                ("Gramos", "Kilogramos"): 0.001,
                ("Litros", "Mililitros"): 1000,
                ("Mililitros", "Litros"): 0.001
            }
            
            if (insumo.unidadMedida, nueva_unidad) in conversiones:
                from decimal import Decimal  # Asegúrate de importar Decimal
                factor = Decimal(str(conversiones[(insumo.unidadMedida, nueva_unidad)]))
                insumo.cantidadDisponible *= factor
            
            insumo.unidadMedida = nueva_unidad
            db.session.commit()
            flash("Insumo actualizado correctamente", "success")
        else:
            flash("Insumo no encontrado", "danger")
    else:
        flash("Error en la validación del formulario", "danger")
    return redirect(url_for("insumos"))


# Endpoint para eliminar un insumo
@app.route("/eliminar_insumo/<int:id>", methods=["GET"])
def eliminar_insumo(id):
    insumo = MateriasPrimas.query.get(id)
    if insumo:
        insumo.estatus = 0  # Cambio lógico
        db.session.commit()
        flash("Insumo eliminado correctamente", "success")
    else:
        flash("Insumo no encontrado", "danger")
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


#COMPRAS INSUMOS
#COMPRAS INSUMOS
@app.route("/comprasInsumos", methods=["GET", "POST"])
@login_required
@role_required(['Admin'])
def comprasInsumos():
    form = CompraInsumoForm(request.form)
    proveedores = Proveedores.query.all()
    insumos = MateriasPrimas.query.all()
    form.idProveedor.choices = [(prov.idProveedor, prov.nombreProveedor) for prov in proveedores]
    form.idMateriaPrima.choices = [(insumo.idMateriaPrima, insumo.materiaPrima) for insumo in insumos]
    # Asignar choices y valor por defecto para el campo 'sabor'
    form.sabor.choices = [('default', 'Default')]
    if not form.sabor.data:
        form.sabor.data = 'default'

    if request.method == "POST" and form.validate():
        # Inserción: si no hay idCompra se usa el SP
        if not request.form.get("idCompra"):
            sql = text("CALL guardarCompraInsumo(:idProveedor, :idMateriaPrima, :cantidad, :fecha, :totalCompra)")
            params = {
                "idProveedor": form.idProveedor.data,
                "idMateriaPrima": form.idMateriaPrima.data,
                "cantidad": form.cantidad.data,
                "fecha": form.fecha.data,
                "totalCompra": form.totalCompra.data
            }
            db.session.execute(sql, params)
            db.session.commit()
            flash("Compra registrada correctamente", "success")
        else:
            # Edición: se actualiza el registro existente
            id_compra = request.form.get("idCompra")
            compra = ComprasInsumos.query.get(id_compra)
            if compra:
                compra.idProveedor = form.idProveedor.data
                compra.idMateriaPrima = form.idMateriaPrima.data
                compra.cantidad = Decimal(form.cantidad.data)
                compra.fecha = form.fecha.data
                compra.totalCompra = Decimal(form.totalCompra.data)
                db.session.commit()
                flash("Compra actualizada correctamente", "success")
            else:
                flash("Compra no encontrada", "danger")
        return redirect(url_for("comprasInsumos"))
    else:
        compras = db.session.execute(text("SELECT * FROM vista_comprasInsumos")).fetchall()
        return render_template("admin/comprasInsumos.html", form=form, compras=compras, proveedores=proveedores, insumos=insumos, ultimo_login=current_user.ultimo_login)

@app.route("/editar_compraInsumo", methods=["POST"])
def editar_compraInsumo():
    form = CompraInsumoForm(request.form)
    proveedores = Proveedores.query.all()
    insumos = MateriasPrimas.query.all()
    form.idProveedor.choices = [(prov.idProveedor, prov.nombreProveedor) for prov in proveedores]
    form.idMateriaPrima.choices = [(insumo.idMateriaPrima, insumo.materiaPrima) for insumo in insumos]
    # Asigna choices para 'sabor'
    form.sabor.choices = [('default', 'Default')]
    if not form.sabor.data:
        form.sabor.data = 'default'

    id_compra = request.form.get("idCompra")
    if id_compra:
        compra = ComprasInsumos.query.get(id_compra)
        if compra:
            try:
                compra.idProveedor = int(form.idProveedor.data)
                compra.idMateriaPrima = int(form.idMateriaPrima.data)
                compra.cantidad = Decimal(form.cantidad.data)
                compra.fecha = form.fecha.data
                compra.totalCompra = Decimal(form.totalCompra.data)
                db.session.commit()
                flash("¡Compra actualizada!", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Error: {str(e)}", "danger")
        else:
            flash("Compra no encontrada", "danger")
    else:
        flash("ID no proporcionado", "danger")
    
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
def puntoVenta():
    # Consulta optimizada para obtener solo productos disponibles
    productos_disponibles = db.session.query(
        ProductosTerminados.idProducto,
        Sabores.nombreSabor,
        DetallesProducto.tipoProducto,
        ProductosTerminados.cantidadDisponible,
        DetallesProducto.precio
    ).join(Sabores, ProductosTerminados.idSabor == Sabores.idSabor)\
    .join(DetallesProducto, ProductosTerminados.idDetalle == DetallesProducto.idDetalle)\
    .filter(ProductosTerminados.estatus == 1, ProductosTerminados.cantidadDisponible > 0)\
    .order_by(ProductosTerminados.idDetalle.asc()).all()

    ventas_estatus_1 = VentasCliente.query.filter_by(estatus=1).all()

    sabores = Sabores.query.all()
    tiposVenta = DetallesProducto.query.all()
    
    if request.method == "POST":
        accion = request.form.get("accion")
        
        if accion == "agregar":
            try:
                idSabor = int(request.form.get("idSabor"))
                idTipoVenta = int(request.form.get("idTipoVenta"))
                cantidad = int(request.form.get("cantidad"))
            except (ValueError, TypeError):
                flash("Datos inválidos para agregar producto.", "danger")
                return redirect(url_for("puntoVenta"))
            
            sabor = Sabores.query.get(idSabor)
            tipo_venta = DetallesProducto.query.get(idTipoVenta)
            if not sabor or not tipo_venta or cantidad <= 0:
                flash("Producto o cantidad inválida.", "danger")
                return redirect(url_for("puntoVenta"))
            
            # Evitar duplicados
            for prod in venta_actual:
                if prod["idSabor"] == idSabor and prod["idTipoVenta"] == idTipoVenta:
                    flash("El producto ya está en la venta.", "warning")
                    return redirect(url_for("puntoVenta"))
            
            precio_total = float(tipo_venta.precio) * cantidad
            producto = {
                "idSabor": sabor.idSabor,
                "sabor": sabor.nombreSabor,
                "idTipoVenta": tipo_venta.idDetalle,
                "tipo": tipo_venta.tipoProducto,
                "cantidad": cantidad,
                "precio_unitario": float(tipo_venta.precio),
                "precio_total": precio_total
            }
            venta_actual.append(producto)
            flash("Producto agregado correctamente.", "success")
            return redirect(url_for("puntoVenta"))
        
        # Actualizar cantidad del producto en la venta
        elif accion == "actualizar":
            try:
                idSabor = int(request.form.get("idSabor"))
                idTipoVenta = int(request.form.get("idTipoVenta"))
            except (ValueError, TypeError):
                flash("Datos inválidos para actualizar producto.", "danger")
                return redirect(url_for("puntoVenta"))
            
            operacion = request.form.get("operacion") 
            for prod in venta_actual:
                if prod["idSabor"] == idSabor and prod["idTipoVenta"] == idTipoVenta:
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
            
            for prod in venta_actual:
                productoTerminado = ProductosTerminados.query.filter_by(
                    idSabor=prod["idSabor"],
                    idDetalle=prod["idTipoVenta"],
                    estatus=1
                ).filter(ProductosTerminados.cantidadDisponible > 0).first()
                if productoTerminado is None:
                    flash(f"Producto terminado no encontrado o no disponible para {prod['sabor']}.", "danger")
                    return redirect(url_for("puntoVenta"))
                if productoTerminado.cantidadDisponible < prod["cantidad"]:
                    flash(f"Inventario insuficiente para {prod['sabor']}.", "danger")
                    return redirect(url_for("puntoVenta"))
                productoTerminado.cantidadDisponible -= prod["cantidad"]
            db.session.commit()
            
            nueva_venta = Ventas(total=total_con_descuento)
            db.session.add(nueva_venta)
            db.session.flush() 
            
            for prod in venta_actual:
                productoTerminado = ProductosTerminados.query.filter_by(
                    idSabor=prod["idSabor"],
                    idDetalle=prod["idTipoVenta"],
                    estatus=1
                ).filter(ProductosTerminados.cantidadDisponible >= 0).first()
                detalle = DetallesVenta(
                    idVenta=nueva_venta.idVenta,
                    idProducto=productoTerminado.idProducto,
                    cantidad=prod["cantidad"],
                    subtotal=prod["precio_total"]
                )
                db.session.add(detalle)
            db.session.commit() 
            
            pdf_path = generar_pdf(venta_actual, descuento, dinero_recibido, total_con_descuento)
            flash("Venta confirmada. Ticket generado en: " + pdf_path, "success")
            venta_actual.clear()
            return redirect(url_for("puntoVenta"))
    
    productos = ProductosTerminados.query.filter(
        ProductosTerminados.estatus == 1,
        ProductosTerminados.cantidadDisponible > 0
    ).all()
    inventario = {}
    for producto in productos:
        inventario[(producto.idSabor, producto.idDetalle)] = producto.cantidadDisponible

    total = sum(prod["precio_total"] for prod in venta_actual)

    return render_template("admin/ventas.html",
                            sabores=sabores,
                            tiposVenta=tiposVenta,
                            venta=venta_actual,
                            total=total,
                            inventario=inventario,
                            ventas_estatus_1=ventas_estatus_1, 
                            ultimo_login=current_user.ultimo_login)


def generar_pdf(venta, descuento, dinero_recibido, total_con_descuento):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Don Galleto", ln=True, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, "Ticket de Compra", ln=True, align="C")
    pdf.line(10, 30, 200, 30)
    now = date.today()
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 10, f"Fecha: {now.strftime('%d/%m/%Y')}", ln=True)
    pdf.cell(0, 10, f"Hora: {now.strftime('%H:%M:%S')}", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(50, 10, "Sabor", border=1)
    pdf.cell(50, 10, "Tipo", border=1)
    pdf.cell(30, 10, "Cant.", border=1, align="R")
    pdf.cell(30, 10, "Precio", border=1, align="R")
    pdf.ln()
    pdf.set_font("Helvetica", "", 12)
    for prod in venta:
        pdf.cell(50, 10, prod["sabor"], border=1)
        pdf.cell(50, 10, prod["tipo"], border=1)
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


#!============================== Error 404 ==============================#

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

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
    usuario.rol = request.form.get('rol')
    usuario.activo = int(request.form.get('activo'))  # Convertir a entero
    
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