from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from app.models import MateriasPrimas, ComprasInsumos, Proveedores
from app.forms import InsumoForm, CompraInsumoForm
from app.utils import role_required
from decimal import Decimal
from sqlalchemy.sql import text
from app.extensions import db

# Definir el Blueprint
insumos_bp = Blueprint('insumos', __name__, template_folder='../templates/admin')

# Ruta para la gestión de insumos
@insumos_bp.route("/insumos", methods=["GET", "POST"])
@login_required
@role_required(['Admin', 'Produccion'])
def insumos():
    form = InsumoForm(request.form)
    if request.method == "POST" and form.validate():
        id_insumo = request.form.get("idMateriaPrima")
        if id_insumo:
            return redirect(url_for("insumos.editar_insumo"))
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
            return redirect(url_for("insumos.insumos"))
    
    insumos_lista = MateriasPrimas.query.filter(MateriasPrimas.estatus != 0).all()
    return render_template("admin/insumos.html", insumos=insumos_lista, form=form, ultimo_login=current_user.ultimo_login)

# Ruta para editar un insumo
@insumos_bp.route("/editar_insumo", methods=["POST"])
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
                factor = Decimal(str(conversiones[(insumo.unidadMedida, nueva_unidad)]))
                insumo.cantidadDisponible *= factor
            
            insumo.unidadMedida = nueva_unidad
            db.session.commit()
            flash("Insumo actualizado correctamente", "success")
        else:
            flash("Insumo no encontrado", "danger")
    else:
        flash("Error en la validación del formulario", "danger")
    return redirect(url_for("insumos.insumos"))

# Ruta para eliminar un insumo
@insumos_bp.route("/eliminar_insumo/<int:id>", methods=["GET"])
def eliminar_insumo(id):
    insumo = MateriasPrimas.query.get(id)
    if insumo:
        insumo.estatus = 0  # Cambio lógico
        db.session.commit()
        flash("Insumo eliminado correctamente", "success")
    else:
        flash("Insumo no encontrado", "danger")
    return redirect(url_for("insumos.insumos"))

# Ruta para aplicar merma a un insumo
@insumos_bp.route("/mermar_insumo/<int:id>/<merma>", methods=["GET"])
def mermar_insumo(id, merma):
    try:
        merma_val = Decimal(merma)
    except ValueError:
        flash("Valor de merma no válido", "danger")
        return redirect(url_for("insumos.insumos"))
    
    insumo = MateriasPrimas.query.get(id)
    if insumo:
        nueva_cantidad = insumo.cantidadDisponible - merma_val
        insumo.cantidadDisponible = max(nueva_cantidad, 0)  # Evitar valores negativos
        db.session.commit()
        flash("Merma aplicada correctamente", "success")
    else:
        flash("Insumo no encontrado", "danger")
    return redirect(url_for("insumos.insumos"))

# Ruta para gestionar compras de insumos
@insumos_bp.route("/comprasInsumos", methods=["GET", "POST"])
@login_required
@role_required(['Admin'])
def comprasInsumos():
    form = CompraInsumoForm(request.form)
    proveedores = Proveedores.query.all()
    insumos = MateriasPrimas.query.all()
    form.idProveedor.choices = [(prov.idProveedor, prov.nombreProveedor) for prov in proveedores]
    form.idMateriaPrima.choices = [(insumo.idMateriaPrima, insumo.materiaPrima) for insumo in insumos]
    form.sabor.choices = [('default', 'Default')]
    if not form.sabor.data:
        form.sabor.data = 'default'

    if request.method == "POST" and form.validate():
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
        return redirect(url_for("insumos.comprasInsumos"))
    else:
        compras = db.session.execute(text("SELECT * FROM vista_comprasInsumos")).fetchall()
        return render_template("admin/comprasInsumos.html", form=form, compras=compras, proveedores=proveedores, insumos=insumos, ultimo_login=current_user.ultimo_login)

# Ruta para editar una compra de insumo
@insumos_bp.route("/editar_compraInsumo", methods=["POST"])
def editar_compraInsumo():
    form = CompraInsumoForm(request.form)
    proveedores = Proveedores.query.all()
    insumos = MateriasPrimas.query.all()
    form.idProveedor.choices = [(prov.idProveedor, prov.nombreProveedor) for prov in proveedores]
    form.idMateriaPrima.choices = [(insumo.idMateriaPrima, insumo.materiaPrima) for insumo in insumos]
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
    
    return redirect(url_for("insumos.comprasInsumos"))