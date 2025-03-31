from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import Sabores, DetallesProducto, ProductosTerminados, MateriasPrimas
from app.forms import LoteForm, PaqueteForm, MermaForm
from app.utils import role_required
from datetime import date, timedelta, datetime
from decimal import Decimal
from app.extensions import db

# Definir el Blueprint
produccion_bp = Blueprint('produccion', __name__, template_folder='../templates/admin')

# Ruta para la página principal de producción
@produccion_bp.route('/')
def index():
    return render_template('produccion/produccion.html')

# Ruta para gestionar galletas
@produccion_bp.route("/galletas", methods=["GET", "POST"])
@login_required  
@role_required(['Admin', 'Ventas', 'Produccion'])
def galletas():
    form = LoteForm()
    paquete_form = PaqueteForm()
    form.sabor.choices = [(sabor.idSabor, sabor.nombreSabor) for sabor in Sabores.query.all()]
    
    # Obtener productos a granel
    productos_granel = db.session.query(
        ProductosTerminados.idProducto,
        Sabores.nombreSabor,
        DetallesProducto.tipoProducto,
        ProductosTerminados.cantidadDisponible
    ).join(Sabores, ProductosTerminados.idSabor == Sabores.idSabor)\
    .join(DetallesProducto, ProductosTerminados.idDetalle == DetallesProducto.idDetalle)\
    .filter(ProductosTerminados.idDetalle == 1, ProductosTerminados.estatus == 1).all()
    
    today = date.today()
    is_christmas_season = today.month == 12
    
    min_galletas = 60 if is_christmas_season else 30
    min_paquetes = 6 if is_christmas_season else 3

    # Obtener todos los productos y marcar los de bajo stock
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
    
    # Verificar productos con bajo stock
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

    for producto in productos_bajo_stock:
        flash(f"¡Alerta! Bajo stock: {producto.nombreSabor} ({producto.tipoProducto}) - Cantidad: {producto.cantidadDisponible}", "warning")

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


# Ruta para guardar un lote
@produccion_bp.route("/guardarLote", methods=["POST"])
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
            
            insumos = {
                2: Decimal("0.9"),  # Harina
                3: Decimal("3"),    # Huevos
                4: Decimal("0.3"),  # Azúcar
                7: Decimal("0.45"), # Mantequilla
                5: Decimal("0.015") # Sal
            }
            
            for id_materia, cantidad_usada in insumos.items():
                materia_prima = MateriasPrimas.query.get(id_materia)
                if materia_prima and materia_prima.cantidadDisponible >= cantidad_usada:
                    materia_prima.cantidadDisponible -= cantidad_usada
                else:
                    flash(f'No hay suficiente {materia_prima.materiaPrima} en inventario.', 'danger')
                    return redirect(url_for('produccion.galletas'))
            
            db.session.commit()
            flash('Lote guardado y materias primas descontadas correctamente', 'success')
            return jsonify({'message': 'Lote guardado correctamente'}), 200
        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar el lote: {str(e)}', 'danger')
        return redirect(url_for('produccion.galletas'))

    flash('Error al guardar el lote. Verifica los datos ingresados.', 'danger')
    return redirect(url_for('produccion.galletas'))

# Ruta para mermar productos
@produccion_bp.route("/mermar", methods=["POST"])
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
            return redirect(url_for('produccion.galletas'))
        
        if cantidad is not None:
            cantidad = int(cantidad)
            if cantidad <= 0:
                flash('La cantidad debe ser mayor a 0', 'danger')
                return redirect(url_for('produccion.galletas'))
        
        producto = ProductosTerminados.query.get(id_producto)
        if not producto:
            flash('Producto no encontrado', 'danger')
            return redirect(url_for('produccion.galletas'))
        
        if cantidad is None or cantidad >= producto.cantidadDisponible:
            cantidad_mermada = producto.cantidadDisponible
            producto.cantidadDisponible = 0
            producto.estatus = 0
        else:
            cantidad_mermada = cantidad
            producto.cantidadDisponible -= cantidad

        db.session.commit()
        flash('Producto mermado correctamente', 'success')
        return redirect(url_for('produccion.galletas'))

    flash('Error al mermar el producto', 'danger')
    return redirect(url_for('produccion.galletas'))

# Ruta para guardar paquetes
@produccion_bp.route("/guardar_paquete", methods=["POST"])
def guardar_paquete():
    paquete_form = PaqueteForm()
    if paquete_form.validate_on_submit():
        tipo_producto = paquete_form.tipo_producto.data
        cantidad_paquetes = paquete_form.cantidad.data
        id_producto = request.form.get("txtIdGalletaGranel")

        producto = ProductosTerminados.query.get(id_producto)
        if not producto:
            flash("El lote seleccionado no existe.", "danger")
            return redirect(url_for("produccion.galletas"))

        galletas_por_paquete = 24 if tipo_producto == 2 else 12
        galletas_necesarias = galletas_por_paquete * cantidad_paquetes

        if producto.cantidadDisponible < galletas_necesarias:
            flash("No hay suficientes galletas en el lote seleccionado.", "danger")
            return redirect(url_for("produccion.galletas"))

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

        flash(f"Paquete creado correctamente: {cantidad_paquetes} paquetes de tipo {tipo_producto}.", "success")
        return redirect(url_for("produccion.galletas"))

    flash("Error al guardar el paquete. Verifica los datos ingresados.", "danger")
    return redirect(url_for("produccion.galletas"))