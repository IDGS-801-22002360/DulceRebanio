from flask import Flask, render_template, request, redirect, url_for
from flask import flash
from flask_wtf import CSRFProtect
from flask import g
from config import DevelopmentConfig


from models import db
from models import Usuarios, MateriasPrimas, Proveedores, ComprasInsumos, Recetas, IngredientesReceta, ProductosTerminados, Ventas

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf = CSRFProtect(app)


@app.route("/", methods=["GET", "POST"])
@app.route("/index")
def index():
    return render_template("index.html")
    
if __name__ == '__main__':
    csrf.init_app(app)
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    app.run()