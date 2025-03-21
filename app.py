from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_wtf import CSRFProtect
from config import DevelopmentConfig
from models import db, ProductosTerminados, Sabores, DetallesProducto
from forms import LoteForm, MermaForm
from sqlalchemy import text
import datetime

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf = CSRFProtect()

@app.route("/", methods=["GET", "POST"])
@app.route("/index")
def index():
    return render_template("client/mainClientes.html")

#!=============== Modulo de Productos ===============#  

@app.route("/galletas", methods=["GET", "POST"])
def galletas():
    form = LoteForm()
    form.sabor.choices = [(sabor.idSabor, sabor.nombreSabor) for sabor in Sabores.query.all()]
    
    productos = db.session.query(
        ProductosTerminados.idProducto,
        Sabores.nombreSabor,
        DetallesProducto.tipoProducto,
        ProductosTerminados.fechaCaducidad,
        ProductosTerminados.cantidadDisponible,
        ProductosTerminados.estatus
    ).join(Sabores, ProductosTerminados.idSabor == Sabores.idSabor)\
    .join(DetallesProducto, ProductosTerminados.idDetalle == DetallesProducto.idDetalle)\
    .filter(ProductosTerminados.estatus == 1).all()
    
    return render_template("admin/galletas.html", productos=productos, form=form)

@app.route("/guardarLote", methods=["POST"])
def guardarLote():
    form = LoteForm()
    form.sabor.choices = [(sabor.idSabor, sabor.nombreSabor) for sabor in Sabores.query.all()]
    
    if form.validate_on_submit():
        sabor_id = form.sabor.data
        id_detalle = 1

        nuevo_producto = ProductosTerminados(
            idSabor=sabor_id,
            cantidadDisponible=150,
            fechaCaducidad=datetime.date.today() + datetime.timedelta(days=7),
            idDetalle=id_detalle,
            estatus=1
        )
        db.session.add(nuevo_producto)
        db.session.commit()

        flash('Lote guardado correctamente', 'success')
        return redirect(url_for('galletas'))

    flash('Error al guardar el lote', 'danger')
    return redirect(url_for('galletas'))


@app.route("/mermar", methods=["POST"])
def mermar():
    form = MermaForm()
    if form.validate_on_submit():
        id_producto = form.idProducto.data
        cantidad = form.cantidad.data
        mermar_todo = form.mermar_todo.data
        
        print(f"Cantidad recibida: {cantidad} (Tipo: {type(cantidad)})")
        print(f"Mermar todo: {mermar_todo}")
        
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
            producto.cantidadDisponible = 0
            producto.estatus = 0
        else:
            producto.cantidadDisponible -= cantidad

        db.session.commit()
        flash('Producto mermado correctamente', 'success')
        return redirect(url_for('galletas'))

    flash('Error al mermar el producto', 'danger')
    return redirect(url_for('galletas'))


#!=============== Modulo de Insumos ===============#

@app.errorhandler(404)
def page_not_found(e):
    return render_template('admin/404.html'), 404

if __name__ == '__main__':
    csrf.init_app(app)
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    app.run()