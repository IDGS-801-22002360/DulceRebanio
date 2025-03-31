from flask import Blueprint, render_template
from flask_login import login_required
from app.utils import role_required
from app.extensions import db

# Definir el Blueprint
recetas_bp = Blueprint('recetas', __name__, template_folder='../templates/admin')

# Ruta para la página de recetas
@recetas_bp.route("/recetas", methods=["GET", "POST"])
@login_required
def recetas():
    return render_template("admin/recetas.html")