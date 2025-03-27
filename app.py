from models import DetallesVenta, Usuarios, Ventas, ComprasInsumos, DetallesProducto, Proveedores, Sabores, db, ProductosTerminados, MateriasPrimas
from forms import CompraInsumoForm, LoteForm, InsumoForm, MermaForm, ProveedorForm, PaqueteForm
from flask import Flask, render_template, request, jsonify, redirect, session, url_for, flash,session
import forms
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import text
from fpdf import FPDF
import os

from config import DevelopmentConfig
from flask_wtf import FlaskForm
from forms import EmpleadoForm, HiddenField, SubmitField, LoginForm, RecuperarContrasenaForm, RegisterForm
from decimal import Decimal
from datetime import datetime, timedelta, date

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf = CSRFProtect()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuarios.query.get(int(user_id))

failed_attempts = {}

@app.route("/", methods=["GET", "POST"])
@app.route("/index")
def index():
    login_form = LoginForm()
    register_form = RegisterForm()
    return render_template("client/mainClientes.html", login_form=login_form, register_form=register_form)

@app.route("/clientes", methods=["GET", "POST"])
def clientes():
    sabores = Sabores.query.all()
    detalles_productos = DetallesProducto.query.all()

    if "carrito" not in session:
        session["carrito"] = []
    return render_template("client/clientes.html", sabores=sabores, detalles_productos=detalles_productos, carrito=session["carrito"])


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
def dashboard():
    return render_template("admin/dashboard.html")


#!============================== Modulo de Productos ==============================#  

@app.route("/galletas", methods=["GET", "POST"])
@login_required  
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
        paquete_form=paquete_form
    )


@app.route("/guardarLote", methods=["POST"])
def guardarLote():
    form = LoteForm()
    form.sabor.choices = [(sabor.idSabor, sabor.nombreSabor) for sabor in Sabores.query.all()]
    
    if form.validate_on_submit():
        try:
            sabor_id = form.sabor.data
            id_detalle = 1

            nuevo_producto = ProductosTerminados(
                idSabor=sabor_id,
                cantidadDisponible=150,
                fechaCaducidad=date.today() + timedelta(days=7),
                idDetalle=id_detalle,
                estatus=1
            )
            db.session.add(nuevo_producto)
            db.session.commit()

            #! Log de la acción para guardar lotes de galletas
            action_logger.info(f"Usuario: {current_user.correo} - Acción: Guardar lote - Sabor: {nuevo_producto.idSabor} - Cantidad: {nuevo_producto.cantidadDisponible} - Fecha: {datetime.now()}")

            flash('Lote guardado correctamente', 'success')
        except Exception as e:
            flash(f'Error al guardar el lote: {str(e)}', 'danger')
        return redirect(url_for('galletas'))

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
    return render_template("admin/insumos.html", insumos=insumos_lista, form=form)

# Endpoint para editar un insumo
@app.route("/editar_insumo", methods=["POST"])
def editar_insumo():
    form = InsumoForm(request.form)
    id_insumo = request.form.get("idMateriaPrima")
    if id_insumo and form.validate():
        insumo = MateriasPrimas.query.get(id_insumo)
        if insumo:
            insumo.materiaPrima = form.materiaPrima.data
            insumo.unidadMedida = form.unidadMedida.data
            insumo.fechaCaducidad = form.fechaCaducidad.data
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
@app.route("/comprasInsumos", methods=["GET", "POST"])
def comprasInsumos():
    form = CompraInsumoForm(request.form)
    proveedores = Proveedores.query.all()
    insumos = MateriasPrimas.query.all()
    form.idProveedor.choices = [(prov.idProveedor, prov.nombreProveedor) for prov in proveedores]
    form.idMateriaPrima.choices = [(insumo.idMateriaPrima, insumo.materiaPrima) for insumo in insumos]

    if request.method == "POST" and form.validate():
        # Si el campo idCompra está vacío, se trata de una inserción y se usa el SP.
        # Dentro de la ruta comprasInsumos, en el bloque POST:
        if not request.form.get("idCompra"):
            sql = text("CALL guardarCompraInsumo(:idProveedor, :idMateriaPrima, :cantidad, :fecha, :totalCompra)")
            params = {
                "idProveedor": form.idProveedor.data,
                "idMateriaPrima": form.idMateriaPrima.data,
                "cantidad": form.cantidad.data,
                "fecha": form.fecha.data,
                "totalCompra": form.totalCompra.data  # Añadir totalCompra
            }
            db.session.execute(sql, params)
            db.session.commit()
            flash("Compra registrada correctamente", "success")
        else:
            # Edición: se actualiza el registro existente, incluyendo totalCompra
            id_compra = request.form.get("idCompra")
            compra = ComprasInsumos.query.get(id_compra)
            if compra:
                compra.idProveedor = form.idProveedor.data
                compra.idMateriaPrima = form.idMateriaPrima.data
                compra.cantidad = Decimal(form.cantidad.data)
                compra.fecha = form.fecha.data
                # Se asume que totalCompra es un campo numérico; convertirlo a Decimal:
                compra.totalCompra = Decimal(form.totalCompra.data)
                db.session.commit()
                flash("Compra actualizada correctamente", "success")
            else:
                flash("Compra no encontrada", "danger")
        return redirect(url_for("comprasInsumos"))
    else:
        compras = db.session.execute(text("SELECT * FROM vista_comprasInsumos")).fetchall()
        return render_template("admin/comprasInsumos.html", form=form, compras=compras, proveedores=proveedores, insumos=insumos)

@app.route("/editar_compraInsumo", methods=["POST"])
def editar_compraInsumo():
    form = CompraInsumoForm(request.form)
    proveedores = Proveedores.query.all()
    insumos = MateriasPrimas.query.all()
    form.idProveedor.choices = [(prov.idProveedor, prov.nombreProveedor) for prov in proveedores]
    form.idMateriaPrima.choices = [(insumo.idMateriaPrima, insumo.materiaPrima) for insumo in insumos]

    id_compra = request.form.get("idCompra")
    if id_compra:
        compra = ComprasInsumos.query.get(id_compra)
        if compra:
            try:
                # Actualizar campos
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
    return render_template("admin/proveedores.html", proveedores=proveedores_lista, form=form)

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
    sabores = Sabores.query.all()
    tiposVenta = DetallesProducto.query.all()
    
    print("Sabores cargados:", sabores)
    print("Tipos de venta cargados:", tiposVenta)
    
    if request.method == "POST":
        accion = request.form.get("accion")

        if accion == "agregar":
            try:
                idSabor = int(request.form.get("idSabor"))
                idTipoVenta = int(request.form.get("idTipoVenta"))
                cantidad = int(request.form.get("cantidad"))
            except (ValueError, TypeError):
                flash("Datos inválidos para agregar producto.")
                return redirect(url_for("puntoVenta"))

            sabor = Sabores.query.get(idSabor)
            tipo_venta = DetallesProducto.query.get(idTipoVenta)

            if not sabor or not tipo_venta or cantidad <= 0:
                flash("Producto o cantidad inválida.")
                return redirect(url_for("puntoVenta"))

            for prod in venta_actual:
                if prod["idSabor"] == idSabor and prod["idTipoVenta"] == idTipoVenta:
                    flash("El producto ya está en la venta.")
                    return redirect(url_for("puntoVenta"))

            # Guarda los datos del producto para su venta
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
            flash("Producto agregado correctamente.")
            return redirect(url_for("puntoVenta"))

        # Confirmar compra
        elif accion == "confirmar":
            try:
                descuento = float(request.form.get("descuento", 0))
                dinero_recibido = float(request.form.get("dinero_recibido"))
            except (ValueError, TypeError):
                flash("Datos de confirmación inválidos.")
                return redirect(url_for("puntoVenta"))

            total = sum(prod["precio_total"] for prod in venta_actual)
            total_con_descuento = total - (total * (descuento / 100))

            if dinero_recibido < total_con_descuento:
                flash("El dinero recibido no es suficiente.")
                return redirect(url_for("puntoVenta"))

            # Actualizar inventario en la BD usando la cantidadDisponible en ProductosTerminados
            for prod in venta_actual:
                # Buscamos el producto terminado que corresponda al idSabor y al idDetalle (tipo de venta)
                productoTerminado = ProductosTerminados.query.filter_by(
                    idSabor=prod["idSabor"],
                    idDetalle=prod["idTipoVenta"]
                ).first()
                if productoTerminado is None:
                    flash(f"Producto terminado no encontrado para {prod['sabor']}.")
                    return redirect(url_for("puntoVenta"))
                if productoTerminado.cantidadDisponible < prod["cantidad"]:
                    flash(f"Inventario insuficiente para {prod['sabor']}.")
                    return redirect(url_for("puntoVenta"))
                productoTerminado.cantidadDisponible -= prod["cantidad"]
            
            db.session.commit()

            nueva_venta = Ventas(total=total_con_descuento)
            db.session.add(nueva_venta)
            db.session.flush() 

            for prod in venta_actual:
                productoTerminado = ProductosTerminados.query.filter_by(
                    idSabor=prod["idSabor"],
                    idDetalle=prod["idTipoVenta"]
                ).first()
                detalle = DetallesVenta(
                    idVenta=nueva_venta.idVenta,
                    idProducto=productoTerminado.idProducto,
                    cantidad=prod["cantidad"],
                    subtotal=prod["precio_total"]
                )
                db.session.add(detalle)
            db.session.commit() 

            # Generar el ticket en PDF
            pdf_path = generar_pdf(venta_actual, descuento, dinero_recibido, total_con_descuento)
            flash("Venta confirmada. Ticket generado en: " + pdf_path)
            venta_actual.clear()  
            return redirect(url_for("puntoVenta"))

    sabores = Sabores.query.all()
    tiposVenta = DetallesProducto.query.all()
    total = sum(prod["precio_total"] for prod in venta_actual)
    
    inventario = {}
    productos = ProductosTerminados.query.all()
    for producto in productos:
        inventario[(producto.idSabor, producto.idDetalle)] = producto.cantidadDisponible

    return render_template("admin/ventas.html",
                            sabores=sabores,
                            tiposVenta=tiposVenta,
                            venta=venta_actual,
                            total=total,
                            inventario=inventario)


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
                return render_template("client/mainClientes.html", login_form=form, register_form=RegisterForm())

        usuario = Usuarios.query.filter_by(correo=correo).first()

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
                    return redirect(url_for('galletas'))
                elif usuario.rol == 'Ventas':
                    return redirect(url_for('galletas'))
                elif usuario.rol == 'Admin':
                    return redirect(url_for('galletas'))
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
    return render_template("client/mainClientes.html", login_form=form, register_form=RegisterForm())

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
    return render_template("client/mainClientes.html", login_form=LoginForm(), register_form=form)


#!============================== Modulo de Usuarios ==============================#

@app.route("/usuarios", methods=["GET", "POST"])
@login_required
def usuarios():
    form = EmpleadoForm()
    usuarios = Usuarios.query.filter_by(activo=1).all()
    
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
        return redirect(url_for('usuarios'))
    
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
    return redirect(url_for('usuarios'))


def is_password_insecure(contrasena):
    with open('insecure_passwords.txt', 'r') as file:
        insecure_passwords = [line.strip() for line in file]
    return contrasena in insecure_passwords


if __name__ == '__main__':
    csrf.init_app(app)
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    app.run()