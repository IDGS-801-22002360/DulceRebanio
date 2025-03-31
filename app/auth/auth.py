from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.forms import LoginForm, RegisterForm, RecuperarContrasenaForm
from app.utils import is_password_insecure
from datetime import datetime, timedelta
from app.extensions import db
from app.models import Usuarios

auth_bp = Blueprint('auth', __name__, template_folder='../templates/client')

# Variable para rastrear intentos fallidos
failed_attempts = {}

# Ruta para login
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        correo = form.correo.data
        contrasena = form.contrasena.data

        if correo in failed_attempts:
            last_attempt_time, attempts = failed_attempts[correo]
            if attempts >= 3 and datetime.now() - last_attempt_time < timedelta(minutes=1):
                flash('Demasiados intentos fallidos. Por favor, espera un minuto antes de intentar nuevamente.', 'danger')
                return render_template("client/mainClientes.html", login_form=form, register_form=RegisterForm(), recuperar_contrasena_form=RecuperarContrasenaForm())

        usuario = Usuarios.query.filter_by(correo=correo).first()

        if usuario:
            if usuario.activo != 1:
                flash('Tu cuenta ha sido desactivada. Por favor, contacta al administrador.', 'danger')
                return render_template("client/mainClientes.html", login_form=form, register_form=RegisterForm())

        if usuario:
            if usuario.check_contrasena(contrasena): 
                login_user(usuario) 
                usuario.ultimo_login = datetime.now()
                db.session.commit()
                flash('Inicio de sesión exitoso.', 'success')
                if correo in failed_attempts:
                    del failed_attempts[correo]
                form.correo.data = ''
                form.contrasena.data = ''
                
                if usuario.rol == 'Cliente':
                    return redirect(url_for('clientes.index'))
                elif usuario.rol == 'Ventas':
                    return redirect(url_for('ventas.puntoVenta'))
                elif usuario.rol == 'Admin':
                    return redirect(url_for('usuarios.miembros'))
                elif usuario.rol == 'Produccion':
                    return redirect(url_for('produccion.galletas'))
            else:
                flash('Correo o contraseña incorrectos. Por favor, intenta de nuevo.', 'danger')
                if correo in failed_attempts:
                    failed_attempts[correo] = (datetime.now(), failed_attempts[correo][1] + 1)
                else:
                    failed_attempts[correo] = (datetime.now(), 1)
        else:
            flash('Correo o contraseña incorrectos. Por favor, intenta de nuevo.', 'danger')
            if correo in failed_attempts:
                failed_attempts[correo] = (datetime.now(), failed_attempts[correo][1] + 1)
            else:
                failed_attempts[correo] = (datetime.now(), 1)
    return render_template("client/mainClientes.html", login_form=form, register_form=RegisterForm(), recuperar_contrasena_form=RecuperarContrasenaForm())

# Ruta para logout
@auth_bp.route("/logout")
@login_required 
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('auth.login'))