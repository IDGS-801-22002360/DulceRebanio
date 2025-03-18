from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import text
from fpdf import FPDF
import os
import datetime

# Importación de configuración, base de datos y formularios
from config import DevelopmentConfig
from models import db, ProductosTerminados
from forms import LoteForm



app = Flask(__name__)
app.secret_key = "dongalleto" 
app.config.from_object(DevelopmentConfig)
csrf = CSRFProtect(app)

@app.route("/", methods=["GET", "POST"])
@app.route("/index")
def index():

    return render_template("client/mainClientes.html")

#!=============== Modulo de Productos ===============#  

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

#   @app.route("/guardarPaquete")
#       def guardarPaquete():
#           


#   @app.route("/eliminarPaquete")
#       def guardarPaquete():
#           if form.validate
#

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#!=============== Modulo de Insumos ===============#

@app.errorhandler(404)
def page_not_found(e):
    return render_template('admin/404.html'), 404
    

#!=============== Modulo de Ventas ===============#

# Datos locales simulados por mientras porque jaja si
sabores = [
    {"idSabor": 1, "sabor": "Chocolate", "cantidad": 100},
    {"idSabor": 2, "sabor": "Vainilla", "cantidad": 80},
    {"idSabor": 3, "sabor": "Fresa", "cantidad": 60}
]

tiposVenta = [
    {"idTipoVenta": 1, "tipo": "Paquete", "precio": 2.5, "cantidad": 30},
    {"idTipoVenta": 2, "tipo": "Caja", "precio": 4.0, "cantidad": 15},
    {"idTipoVenta": 3, "tipo": "Individual", "precio": 0.5, "cantidad": 1},
    {"idTipoVenta": 4, "tipo": "Especial", "precio": 3.0, "cantidad": 10},
    {"idTipoVenta": 5, "tipo": "Premium", "precio": 5.0, "cantidad": 8}
]

# Venta actual: lista de productos agregados a la venta
venta_actual = []  # Cada elemento es un diccionario con detalles del producto para que amarre el guardado 

@app.route("/puntoVenta", methods=["GET", "POST"])
def puntoVenta():
    if request.method == "POST":
        accion = request.form.get("accion")
        
        # Agregar producto a la venta
        if accion == "agregar":
            try:
                idSabor = int(request.form.get("idSabor"))
                idTipoVenta = int(request.form.get("idTipoVenta"))
                cantidad = int(request.form.get("cantidad"))
            except (ValueError, TypeError):
                flash("Datos inválidos para agregar producto.")
                return redirect(url_for("puntoVenta"))
            
            # Buscar el sabor y tipo de venta seleccionados
            flavor = next((s for s in sabores if s["idSabor"] == idSabor), None)
            sale_type = next((t for t in tiposVenta if t["idTipoVenta"] == idTipoVenta), None)
            
            if not flavor or not sale_type or cantidad <= 0:
                flash("Producto o cantidad inválida.")
                return redirect(url_for("puntoVenta"))
            
            # Verificar si el producto ya se encuentra en la venta
            for prod in venta_actual:
                if prod["idSabor"] == idSabor and prod["idTipoVenta"] == idTipoVenta:
                    flash("El producto ya está en la venta.")
                    return redirect(url_for("puntoVenta"))
            
            precio_total = sale_type["precio"] * cantidad
            producto = {
                "idSabor": flavor["idSabor"],
                "sabor": flavor["sabor"],
                "idTipoVenta": sale_type["idTipoVenta"],
                "tipo": sale_type["tipo"],
                "cantidad": cantidad,
                "precio_unitario": sale_type["precio"],
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
            
            # Actualizar inventario: para cada producto se descuenta (multiplicador * cantidad vendida)
            for prod in venta_actual:
                sale_type = next((t for t in tiposVenta if t["idTipoVenta"] == prod["idTipoVenta"]), None)
                if sale_type:
                    cantidad_a_restar = sale_type["cantidad"] * prod["cantidad"]
                    for s in sabores:
                        if s["idSabor"] == prod["idSabor"]:
                            if s["cantidad"] < cantidad_a_restar:
                                flash(f"Inventario insuficiente para {s['sabor']}.")
                                return redirect(url_for("puntoVenta"))
                            s["cantidad"] -= cantidad_a_restar
                            break
            
            # Generar el ticket en PDF
            pdf_path = generar_pdf(venta_actual, descuento, dinero_recibido, total_con_descuento)
            flash("Venta confirmada. Ticket generado en: " + pdf_path)
            venta_actual.clear()  # Limpiar venta para nueva operación
            return redirect(url_for("puntoVenta"))
    
    # Método GET: renderizamos la página con los datos actuales
    total = sum(prod["precio_total"] for prod in venta_actual)
    return render_template("admin/ventas.html",
                           sabores=sabores,
                           tiposVenta=tiposVenta,
                           venta=venta_actual,
                           total=total)

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
    total = 0
    for prod in venta:
        pdf.cell(50, 10, prod["sabor"], border=1)
        pdf.cell(50, 10, prod["tipo"], border=1)
        pdf.cell(30, 10, str(prod["cantidad"]), border=1, align="R")
        pdf.cell(30, 10, f"${prod['precio_total']:.2f}", border=1, align="R")
        pdf.ln()
        total += prod["precio_total"]
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

if __name__ == '__main__':
    csrf.init_app(app)
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    app.run()