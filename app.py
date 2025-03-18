from flask import Flask, render_template, request, jsonify
from flask_wtf import CSRFProtect
from config import DevelopmentConfig
from models import db, ProductosTerminados
from forms import LoteForm
from sqlalchemy import text


app = Flask(__name__)
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

#   @app.route("/eliminarPaquete")
#       def guardarPaquete():
#           if form.validate
#

#!=============== Modulo de Insumos ===============#

@app.errorhandler(404)
def page_not_found(e):
    return render_template('admin/404.html'), 404



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        # Aquí puedes agregar la lógica para validar el usuario en la base de datos
        if username == "admin" and password == "1234":  # Ejemplo, reemplaza con validación real
            return render_template("admin/galletas.html")
        else:
            return jsonify({"success": False, "message": "Credenciales incorrectas"})

    return render_template("admin/login.html")

if __name__ == '__main__':
    csrf.init_app(app)
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    app.run()