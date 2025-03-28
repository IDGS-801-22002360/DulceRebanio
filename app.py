from functools import wraps
from models import DetallesVenta, Usuarios, Ventas, ComprasInsumos, DetallesProducto, Proveedores, Sabores, db, ProductosTerminados, MateriasPrimas
from forms import CompraInsumoForm, LoteForm, InsumoForm, MermaForm, ProveedorForm, PaqueteForm, RecuperarContrasenaForm
from flask import Flask, render_template, request, jsonify, redirect, session, url_for, flash,session
import forms
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import CSRFProtect, RecaptchaField
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import text
from fpdf import FPDF
import os

from logger import action_logger

from config import DevelopmentConfig
from flask_wtf import FlaskForm
from forms import EmpleadoForm, HiddenField, SubmitField, LoginForm, RecuperarContrasenaForm, RegisterForm
from decimal import Decimal
from datetime import datetime, timedelta, date

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf = CSRFProtect()

app.config["RECAPTCHA_PUBLIC_KEY"] = "6Lcb1f0qAAAAAMLjkyE44X40_nQq_FZns9Sj8CVs"
app.config["RECAPTCHA_PRIVATE_KEY"] = "6Lcb1f0qAAAAADFk-w_f5-Da5MyzdN2E8HdY-Vcs"
# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=200)

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


@app.route("/", methods=["GET", "POST"])
@app.route("/index")
def index():
    login_form = LoginForm()
    register_form = RegisterForm()
    recuperar_contrasena_form = RecuperarContrasenaForm()
    return render_template("client/mainClientes.html", 
                         login_form=login_form, 
                         register_form=register_form,
                         recuperar_contrasena_form=recuperar_contrasena_form)

@app.route("/clientes", methods=["GET", "POST"])
@login_required
@role_required(['Cliente','Admin'])
def clientes():
    sabores = Sabores.query.all()
    detalles_productos = DetallesProducto.query.all()

    if "carrito" not in session:
        session["carrito"] = []
    return render_template("client/clientes.html", sabores=sabores, detalles_productos=detalles_productos, carrito=session["carrito"], ultimo_login=current_user.ultimo_login)


@app.route("/agregar_carrito", methods=["POST"])
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
        producto_existente = next((item for item in carrito if item["id"] == sabor.idSabor), None)

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

#!============================== Modulo dashboard ==============================# 

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
@role_required(['Admin', 'Ventas'])
def dashboard():
    return render_template("admin/dashboard.html", ultimo_login=current_user.ultimo_login)


#!============================== Modulo de Productos ==============================#  

@app.route("/galletas", methods=["GET", "POST"])
@login_required  
@role_required(['Admin', 'Ventas', 'Produccion'])
def galletas():
    form = LoteForm()
    paquete_form = PaqueteForm()
    form.sabor.choices = [(sabor.idSabor, sabor.nombreSabor) for sabor in Sabores.query.all()]
    
    #* Estas son unicamente las galletas a granel
    productos_granel = db.session.query(
        ProductosTerminados.idProducto,
        Sabores.nombreSabor,
        DetallesProducto.tipoProducto,
        ProductosTerminados.cantidadDisponible
    ).join(Sabores, ProductosTerminados.idSabor == Sabores.idSabor)\
    .join(DetallesProducto, ProductosTerminados.idDetalle == DetallesProducto.idDetalle)\
    .filter(ProductosTerminados.idDetalle == 1, ProductosTerminados.estatus == 1).all()
    
    #* Verificar si estamos en temporada navideña
    today = date.today()
    is_christmas_season = today.month == 12
    
    #* Ajuste de mínimo stock según la temporada
    min_galletas = 60 if is_christmas_season else 30
    min_paquetes = 6 if is_christmas_season else 3

    #* Obtener todos los productos y marcar los de bajo stock
    productos = db.session.query(
        ProductosTerminados.idProducto,
        Sabores.nombreSabor,
        DetallesProducto.tipoProducto,
        ProductosTerminados.fechaCaducidad,
        ProductosTerminados.cantidadDisponible,
        ProductosTerminados.estatus
    ).join(Sabores, ProductosTerminados.idSabor == Sabores.idSabor)\
    .join(DetallesProducto, ProductosTerminados.idDetalle == DetallesProducto.idDetalle)\
    .filter(ProductosTerminados.estatus == 1)\
    .order_by(ProductosTerminados.idDetalle.asc()).all()
    
    #* Verificar productos con bajo stock
    productos_bajo_stock = db.session.query(
        ProductosTerminados.idProducto,
        Sabores.nombreSabor,
        DetallesProducto.tipoProducto,
        ProductosTerminados.cantidadDisponible
    ).join(Sabores, ProductosTerminados.idSabor == Sabores.idSabor)\
    .join(DetallesProducto, ProductosTerminados.idDetalle == DetallesProducto.idDetalle)\
    .filter(
        ProductosTerminados.estatus == 1,
        (ProductosTerminados.idDetalle == 1) & (ProductosTerminados.cantidadDisponible < min_galletas) |
        (ProductosTerminados.idDetalle.in_([2, 3]) & (ProductosTerminados.cantidadDisponible < min_paquetes))
    ).all()

    #* Generar alertas para productos con bajo stock
    for producto in productos_bajo_stock:
        flash(f"¡Alerta! Bajo stock: {producto.nombreSabor} ({producto.tipoProducto}) - Cantidad: {producto.cantidadDisponible}", "warning")

    #* Marcar los productos con bajo stock
    productos_marcados = []
    for producto in productos:
        bajo_stock = (
            (producto.tipoProducto == "Granel" and producto.cantidadDisponible < min_galletas) or
            (producto.tipoProducto in ["Kilo", "Med. Kilo"] and producto.cantidadDisponible < min_paquetes)
        )
        productos_marcados.append({
            "idProducto": producto.idProducto,
            "nombreSabor": producto.nombreSabor,
            "tipoProducto": producto.tipoProducto,
            "fechaCaducidad": producto.fechaCaducidad,
            "cantidadDisponible": producto.cantidadDisponible,
            "estatus": producto.estatus,
            "bajo_stock": bajo_stock
        })

    return render_template(
        "admin/galletas.html",
        productos=productos_marcados,
        productos_granel=productos_granel,
        form=form,
        paquete_form=paquete_form, ultimo_login=current_user.ultimo_login
    )

@app.route("/guardarLote", methods=["POST"])
def guardarLote():
    form = LoteForm()
    form.sabor.choices = [(sabor.idSabor, sabor.nombreSabor) for sabor in Sabores.query.all()]
    
    if form.validate_on_submit():
        try:
            print("Formulario validado correctamente")
            sabor_id = form.sabor.data
            id_detalle = 1
            print(f"Sabor seleccionado: {sabor_id}")

            nuevo_producto = ProductosTerminados(
                idSabor=sabor_id,
                cantidadDisponible=150,
                fechaCaducidad=date.today() + timedelta(days=7),
                idDetalle=id_detalle,
                estatus=1
            )
            db.session.add(nuevo_producto)
            print("Producto terminado agregado a la sesión")
            
            # Descontar materias primas
            insumos = {
                2: Decimal("0.9"),  # Harina (kg)
                3: Decimal("3"),    # Huevos (pzs)
                4: Decimal("0.3"),  # Azúcar (kg)
                7: Decimal("0.45"), # Mantequilla (kg)
                5: Decimal("0.015") # Sal (kg)
            }
            
            for id_materia, cantidad_usada in insumos.items():
                materia_prima = MateriasPrimas.query.get(id_materia)
                print(f"Procesando materia prima ID {id_materia}, Cantidad disponible: {materia_prima.cantidadDisponible}")
                if materia_prima and materia_prima.cantidadDisponible >= cantidad_usada:
                    materia_prima.cantidadDisponible -= cantidad_usada
                    print(f"Nueva cantidad disponible para ID {id_materia}: {materia_prima.cantidadDisponible}")
                else:
                    print(f"Error: No hay suficiente {materia_prima.materiaPrima} en inventario o ID no encontrado")
                    flash(f'No hay suficiente {materia_prima.materiaPrima} en inventario.', 'danger')
                    return redirect(url_for('galletas'))
            
            db.session.commit()
            print("Transacción confirmada y datos guardados correctamente")

            # Log de la acción
            action_logger.info(f"Usuario: {current_user.correo} - Acción: Guardar lote - Sabor: {nuevo_producto.idSabor} - Cantidad: {nuevo_producto.cantidadDisponible} - Fecha: {datetime.now()}")
            
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

@app.route("/recetas", methods=["GET", "POST"])
@login_required
def recetas():
    return render_template("admin/recetas.html")

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
@role_required(['Admin', 'Ventas'])
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

    if request.method == "POST":
        accion = request.form.get("accion")

        if accion == "agregar":
            try:
                idProducto = int(request.form.get("idProducto"))
                cantidad = int(request.form.get(f"cantidad_{idProducto}"))
            except (ValueError, TypeError):
                return redirect(url_for("puntoVenta"))

            # Buscar el producto en la lista de productos disponibles
            producto = next((p for p in productos_disponibles if p.idProducto == idProducto), None)
            if not producto or cantidad <= 0:
                return redirect(url_for("puntoVenta"))

            # Verificar si el producto ya está en la venta
            for prod in venta_actual:
                if prod["idProducto"] == idProducto:
                    return redirect(url_for("puntoVenta"))

            # Agregar el producto a la venta actual
            precio_total = float(producto.precio) * cantidad
            venta_actual.append({
                "idProducto": producto.idProducto,
                "sabor": producto.nombreSabor,
                "tipo": producto.tipoProducto,
                "cantidad": cantidad,
                "precio_unitario": float(producto.precio),
                "precio_total": precio_total
            })
            return redirect(url_for("puntoVenta"))

        elif accion == "confirmar":
            try:
                descuento = float(request.form.get("descuento", 0))
                dinero_recibido = float(request.form.get("dinero_recibido"))
            except (ValueError, TypeError):
                return redirect(url_for("puntoVenta"))

            total = sum(prod["precio_total"] for prod in venta_actual)
            total_con_descuento = total - (total * (descuento / 100))

            if dinero_recibido < total_con_descuento:
                return redirect(url_for("puntoVenta"))

            # Actualizar inventario y registrar la venta
            for prod in venta_actual:
                productoTerminado = ProductosTerminados.query.get(prod["idProducto"])
                if productoTerminado.cantidadDisponible < prod["cantidad"]:
                    flash(f"Inventario insuficiente para {prod['sabor']}.")
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
            db.session.commit()

            venta_actual.clear()
            return redirect(url_for("puntoVenta"))

    total = sum(prod["precio_total"] for prod in venta_actual)

    return render_template("admin/ventas.html",
                            productos_disponibles=productos_disponibles,
                            venta=venta_actual,
                            total=total,
                            ultimo_login=current_user.ultimo_login)



def generar_pdf(venta, descuento, dinero_recibido, total_con_descuento):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Don Galleto", ln=True, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(0, 10, "Ticket de Compra", ln=True, align="C")
    pdf.line(10, 30, 200, 30)
    now = datetime.datetime.now()
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

        if correo in failed_attempts:
            last_attempt_time, attempts = failed_attempts[correo]
            if attempts >= 3 and datetime.now() - last_attempt_time < timedelta(minutes=1):
                flash('Demasiados intentos fallidos. Por favor, espera un minuto antes de intentar nuevamente.', 'danger')
                return render_template("client/mainClientes.html", login_form=form, register_form=RegisterForm(), recuperar_contrasena_form=RecuperarContrasenaForm())

        usuario = Usuarios.query.filter_by(correo=correo).first()

        if usuario:
            if usuario.activo != 1:
                flash('Tu cuenta ha sido desactivada. Por favor, contacta al administrador.', 'danger')
                return render_template("client/mainClientes.html", login_form=form, register_form=RegisterForm())

        if usuario:
            if usuario.check_contrasena(contrasena): 
                login_user(usuario) 
                usuario.ultimo_login = datetime.now()
                db.session.commit()
                flash('Inicio de sesión exitoso.', 'success')
                if correo in failed_attempts:
                    del failed_attempts[correo]
                form.correo.data = ''
                form.contrasena.data = ''
                
                if usuario.rol == 'Cliente':
                    return redirect(url_for('clientes'))
                elif usuario.rol == 'Ventas':
                    return redirect(url_for('puntoVenta'))
                elif usuario.rol == 'Admin':
                    return redirect(url_for('miembros'))
                elif usuario.rol == 'Produccion':
                    return redirect(url_for('galletas'))
            else:
                flash('Correo o contraseña incorrectos. Por favor, intenta de nuevo.', 'danger')
                if correo in failed_attempts:
                    failed_attempts[correo] = (datetime.now(), failed_attempts[correo][1] + 1)
                else:
                    failed_attempts[correo] = (datetime.now(), 1)
        else:
            flash('Correo o contraseña incorrectos. Por favor, intenta de nuevo.', 'danger')
            if correo in failed_attempts:
                failed_attempts[correo] = (datetime.now(), failed_attempts[correo][1] + 1)
            else:
                failed_attempts[correo] = (datetime.now(), 1)
    return render_template("client/mainClientes.html", login_form=form, register_form=RegisterForm(), recuperar_contrasena_form=RecuperarContrasenaForm())

@app.route("/logout")
@login_required 
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('login'))


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        nombre = form.nombre.data
        apaterno = form.apaterno.data
        amaterno = form.amaterno.data
        correo = form.correo.data
        contrasena = form.contrasena.data

        if is_password_insecure(contrasena):
            flash('La contraseña es insegura. Por favor, elige una contraseña más segura.', 'danger')
            return render_template("client/mainClientes.html", login_form=LoginForm(), register_form=form)

        usuario_existente = Usuarios.query.filter_by(correo=correo).first()
        if usuario_existente:
            flash('El correo ya está registrado. Por favor, utiliza otro correo.', 'danger')
        else:
            nuevo_usuario = Usuarios(nombre=nombre, apaterno=apaterno, amaterno=amaterno, correo=correo, rol='Cliente')
            nuevo_usuario.set_contrasena(contrasena)
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash('Cuenta creada exitosamente. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
    return render_template("client/mainClientes.html", login_form=LoginForm(), register_form=form,  recuperar_contrasena_form=RecuperarContrasenaForm())

@app.route("/miembros", methods=["GET", "POST"])
@login_required
@role_required(['Admin'])
def miembros():
    form = EmpleadoForm()
    usuarios = Usuarios.query.filter_by(activo=1).filter(Usuarios.rol != 'Cliente').all()
    
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
    if form.validate_on_submit():
        correo = form.correo.data
        nueva_contrasena = form.nueva_contrasena.data
        confirmar_contrasena = form.confirmar_contrasena.data

        # Verificar si el correo existe en la base de datos
        usuario = Usuarios.query.filter_by(correo=correo).first()
        if not usuario:
            flash('El correo no está registrado.', 'danger')
            return redirect(url_for('login'))

        # Verificar que las contraseñas coincidan
        if nueva_contrasena != confirmar_contrasena:
            flash('Las contraseñas no coinciden.', 'danger')
            return redirect(url_for('login'))

        # Validar la contraseña
        if is_password_insecure(nueva_contrasena):
            flash('La contraseña es insegura. Por favor, elige una contraseña más segura.', 'danger')
            return redirect(url_for('login'))

        # Actualizar la contraseña en la base de datos
        usuario.set_contrasena(nueva_contrasena)
        db.session.commit()
        flash('Contraseña actualizada correctamente.', 'success')
        return redirect(url_for('login'))

    # Si el formulario no es válido, mostrar errores
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{error}', 'danger')
    return redirect(url_for('login'))


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