from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import ProductosTerminados, Sabores, DetallesProducto, VentasCliente, Ventas, DetallesVenta
from app.utils import role_required
from app.extensions import db, csrf
from fpdf import FPDF
import datetime

# Definir el Blueprint
ventas_bp = Blueprint('ventas', __name__, template_folder='../templates/admin')

# Variable global para la venta actual
venta_actual = []

# Ruta para el punto de venta
@ventas_bp.route("/puntoVenta", methods=["GET", "POST"])
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

    ventas_estatus_1 = VentasCliente.query.filter_by(estatus=1).all()

    if request.method == "POST":
        accion = request.form.get("accion")

        if accion == "agregar":
            try:
                idProducto = int(request.form.get("idProducto"))
                cantidad = int(request.form.get(f"cantidad_{idProducto}"))
            except (ValueError, TypeError):
                flash("Datos inválidos para agregar producto.", "danger")
                return redirect(url_for("ventas.puntoVenta"))

            # Buscar el producto en la lista de productos disponibles
            producto = next((p for p in productos_disponibles if p.idProducto == idProducto), None)
            if not producto or cantidad <= 0:
                flash("Producto o cantidad inválida.", "danger")
                return redirect(url_for("ventas.puntoVenta"))

            # Verificar si el producto ya está en la venta
            for prod in venta_actual:
                if prod["idProducto"] == idProducto:
                    flash("El producto ya está en la venta.", "warning")
                    return redirect(url_for("ventas.puntoVenta"))

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
            flash("Producto agregado correctamente.", "success")
            return redirect(url_for("ventas.puntoVenta"))

        elif accion == "confirmar":
            try:
                descuento = float(request.form.get("descuento", 0))
                dinero_recibido = float(request.form.get("dinero_recibido"))
            except (ValueError, TypeError):
                flash("Datos de confirmación inválidos.", "danger")
                return redirect(url_for("ventas.puntoVenta"))

            total = sum(prod["precio_total"] for prod in venta_actual)
            total_con_descuento = total - (total * (descuento / 100))

            if dinero_recibido < total_con_descuento:
                flash("El dinero recibido no es suficiente.", "danger")
                return redirect(url_for("ventas.puntoVenta"))

            # Actualizar inventario y registrar la venta
            for prod in venta_actual:
                productoTerminado = ProductosTerminados.query.get(prod["idProducto"])
                if productoTerminado.cantidadDisponible < prod["cantidad"]:
                    flash(f"Inventario insuficiente para {prod['sabor']}.", "danger")
                    return redirect(url_for("ventas.puntoVenta"))
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

            flash("Venta confirmada correctamente.", "success")
            venta_actual.clear()
            return redirect(url_for("ventas.puntoVenta"))

    total = sum(prod["precio_total"] for prod in venta_actual)

    return render_template("admin/ventas.html",
                        productos_disponibles=productos_disponibles,
                        venta=venta_actual,
                        total=total,
                        ventas_estatus_1=ventas_estatus_1,
                        ultimo_login=current_user.ultimo_login)

# Función para generar el ticket en PDF
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