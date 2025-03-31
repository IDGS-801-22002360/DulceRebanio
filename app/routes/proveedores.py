from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Proveedores
from app.forms import ProveedorForm
from app.utils import role_required
from app.extensions import db

# Definir el Blueprint
proveedores_bp = Blueprint('proveedores', __name__, template_folder='../templates/admin')

# Ruta para la gestión de proveedores
@proveedores_bp.route("/proveedores", methods=["GET", "POST"])
@login_required
@role_required(['Admin'])
def proveedores():
    form = ProveedorForm(request.form)
    if request.method == "POST" and form.validate():
        # Si existe un id en el formulario, se trata de una edición
        id_prov = request.form.get("idProveedor")
        if id_prov:
            # Redirige al endpoint de edición
            return redirect(url_for("proveedores.editar_proveedor"))
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
            return redirect(url_for("proveedores.proveedores"))
    # Consulta de proveedores activos (estatus distinto de 0)
    proveedores_lista = Proveedores.query.filter(Proveedores.estatus != 0).all()
    return render_template("admin/proveedores.html", proveedores=proveedores_lista, form=form, ultimo_login=current_user.ultimo_login)

# Ruta para editar un proveedor
@proveedores_bp.route("/editar_proveedor", methods=["POST"])
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
    return redirect(url_for("proveedores.proveedores"))

# Ruta para eliminar un proveedor
@proveedores_bp.route("/eliminar_proveedor/<int:id>", methods=["GET"])
def eliminar_proveedor(id):
    proveedor = Proveedores.query.get(id)
    if proveedor:
        proveedor.estatus = 0  # Eliminación lógica
        db.session.commit()
        flash("Proveedor eliminado correctamente", "success")
    else:
        flash("Proveedor no encontrado", "danger")
    return redirect(url_for("proveedores.proveedores"))