from flask import Flask, redirect, render_template, request, jsonify, flash, url_for
from flask_wtf import CSRFProtect
from config import DevelopmentConfig
from models import ComprasInsumos, Proveedores, db, ProductosTerminados, MateriasPrimas
from forms import CompraInsumoForm, LoteForm, InsumoForm, ProveedorForm
from sqlalchemy import text
from decimal import Decimal


app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf = CSRFProtect(app)
app.secret_key = "DulceRebanio" 

@app.route("/", methods=["GET", "POST"])
@app.route("/index")
def index():
    return render_template("client/mainClientes.html")

#!============================== Modulo de Productos ==============================#  

@app.route("/galletas", methods=["GET", "POST"])
def galletas():
    form = LoteForm()
    productos = db.session.execute(text("SELECT * FROM productosTerminados WHERE estatus=1")).fetchall()
    return render_template("admin/galletas.html", productos=productos, form=form)

@app.route("/guardarLote", methods=["POST"])
def guardarLote():
    form = LoteForm()
    if form.validate_on_submit():
        sabor = form.sabor.data
        db.session.execute(text("CALL saveLote(:sabor)"), {'sabor': sabor})
        db.session.commit()
        return jsonify({'success': True, 'message': 'Lote guardado Correctamente'})
    return jsonify({'success': False, 'message': 'Error al guardar'})

#   @app.route("/eliminarPaquete")
#       def guardarPaquete():
#           if form.validate
#

#!============================== Modulo de Insumos ==============================#
@app.route("/insumos", methods=["GET", "POST"])
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




#Endpoint para proveedores
@app.route("/proveedores", methods=["GET", "POST"])
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
#!================= Inicio de app =================#
if __name__ == '__main__':
    csrf.init_app(app)
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    app.run()