from flask import Flask, render_template, request, jsonify, redirect, url_for, flash,session
import forms
from flask_wtf import CSRFProtect
from config import DevelopmentConfig
from models import db, ProductosTerminados, Sabores, DetallesProducto
from forms import LoteForm, MermaForm
from sqlalchemy import text
from flask_wtf import FlaskForm
from wtforms import HiddenField, SubmitField
from decimal import Decimal

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf = CSRFProtect()
app.config['SECRET_KEY'] = 'tu_clave_secreta'
app.secret_key = "tu_clave_secreta"


#!=============== Modulo de Clientes ===============# 

@app.route("/", methods=["GET", "POST"])
@app.route("/index")
def index():
    return render_template("client/mainClientes.html")

@app.route("/clientes", methods=["GET", "POST"])
def clientes():
    sabores = Sabores.query.all()
    detalles_productos = DetallesProducto.query.all()

    if "carrito" not in session:
        session["carrito"] = []

    return render_template("client/clientes.html", sabores=sabores, detalles_productos=detalles_productos, carrito=session["carrito"])

from decimal import Decimal

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

#!=============== Modulo dashboard ===============# 
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    return render_template("admin/dashboard.html")

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
        sabor = form.sabor.data
        db.session.execute(text("CALL saveLote(:sabor)"), {'sabor': sabor})
        db.session.commit()
        return jsonify({'success': True, 'message': 'Lote guardado Correctamente'})
    return jsonify({'success': False, 'message': 'Error al guardar'})

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