from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Usuarios
from app.forms import RegisterForm, EmpleadoForm, LoginForm, RecuperarContrasenaForm
from app.utils import role_required, is_password_insecure
from app.extensions import db

# Definir el Blueprint
usuarios_bp = Blueprint('usuarios', __name__, template_folder='../templates/admin')

# Ruta para la página principal de usuarios
@usuarios_bp.route('/')
def index():
    return render_template('usuarios/usuarios.html')

# Ruta para registrar un usuario
@usuarios_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        nombre = form.nombre.data
        apaterno = form.apaterno.data
        amaterno = form.amaterno.data
        correo = form.correo.data
        contrasena = form.contrasena.data

        if is_password_insecure(contrasena):
            flash('La contraseña es insegura. Por favor, elige una contraseña más segura.', 'danger')
            return render_template("client/mainClientes.html", login_form=LoginForm(), register_form=form)

        usuario_existente = Usuarios.query.filter_by(correo=correo).first()
        if usuario_existente:
            flash('El correo ya está registrado. Por favor, utiliza otro correo.', 'danger')
        else:
            nuevo_usuario = Usuarios(nombre=nombre, apaterno=apaterno, amaterno=amaterno, correo=correo, rol='Cliente')
            nuevo_usuario.set_contrasena(contrasena)
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash('Cuenta creada exitosamente. Ahora puedes iniciar sesión.', 'success')
            return redirect(url_for('usuarios.index'))
    return render_template("client/mainClientes.html", login_form=LoginForm(), register_form=form, recuperar_contrasena_form=RecuperarContrasenaForm())

# Ruta para gestionar miembros (usuarios no clientes)
@usuarios_bp.route("/miembros", methods=["GET", "POST"])
@login_required
@role_required(['Admin'])
def miembros():
    form = EmpleadoForm()
    usuarios = Usuarios.query.filter_by(activo=1).filter(Usuarios.rol != 'Cliente').all()
    
    if form.validate_on_submit():
        nombre = form.nombre.data
        apaterno = form.apaterno.data
        amaterno = form.amaterno.data
        correo = form.correo.data
        contrasena = form.contrasena.data
        rol = form.rol.data

        if is_password_insecure(contrasena):
            flash('La contraseña es insegura. Por favor, elige una contraseña más segura.', 'danger')
            return render_template("admin/usuarios.html", form=form, usuarios=usuarios, ultimo_login=current_user.ultimo_login)

        usuario_existente = Usuarios.query.filter_by(correo=correo).first()
        if usuario_existente:
            flash('El correo ya está registrado. Por favor, utiliza otro correo.', 'danger')
        else:
            nuevo_usuario = Usuarios(nombre=nombre, apaterno=apaterno, amaterno=amaterno, correo=correo, rol=rol)
            nuevo_usuario.set_contrasena(contrasena)
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash('Usuario registrado exitosamente.', 'success')
        return redirect(url_for('usuarios.miembros'))
    
    return render_template("admin/usuarios.html", form=form, usuarios=usuarios, ultimo_login=current_user.ultimo_login)

# Ruta para eliminar un usuario
@usuarios_bp.route("/eliminar_usuario/<int:id_usuario>", methods=["POST"])
@login_required
def eliminar_usuario(id_usuario):
    usuario = Usuarios.query.get(id_usuario)
    if usuario:
        usuario.activo = 0 
        db.session.commit()
        flash('Usuario eliminado correctamente.', 'success')
    else:
        flash('Usuario no encontrado.', 'danger')
    return redirect(url_for('usuarios.miembros'))

# Ruta para editar un usuario
@usuarios_bp.route("/editar_usuario/<int:id_usuario>", methods=["POST"])
@login_required
@role_required(['Admin'])
def editar_usuario(id_usuario):
    usuario = Usuarios.query.get_or_404(id_usuario)

    usuario.nombre = request.form.get('nombre')
    usuario.apaterno = request.form.get('apaterno')
    usuario.amaterno = request.form.get('amaterno')
    usuario.correo = request.form.get('correo')
    usuario.rol = request.form.get('rol')
    usuario.activo = int(request.form.get('activo'))  # Convertir a entero
    
    db.session.commit()
    flash('Usuario actualizado correctamente.', 'success')
    return redirect(url_for('usuarios.miembros'))

# Ruta para recuperar contraseña
@usuarios_bp.route("/recuperar_contrasena", methods=["POST"])
def recuperar_contrasena():
    form = RecuperarContrasenaForm()
    if form.validate_on_submit():
        correo = form.correo.data
        nueva_contrasena = form.nueva_contrasena.data
        confirmar_contrasena = form.confirmar_contrasena.data

        # Verificar si el correo existe en la base de datos
        usuario = Usuarios.query.filter_by(correo=correo).first()
        if not usuario:
            flash('El correo no está registrado.', 'danger')
            return redirect(url_for('usuarios.index'))

        # Verificar que las contraseñas coincidan
        if nueva_contrasena != confirmar_contrasena:
            flash('Las contraseñas no coinciden.', 'danger')
            return redirect(url_for('usuarios.index'))

        # Validar la contraseña
        if is_password_insecure(nueva_contrasena):
            flash('La contraseña es insegura. Por favor, elige una contraseña más segura.', 'danger')
            return redirect(url_for('usuarios.index'))

        # Actualizar la contraseña en la base de datos
        usuario.set_contrasena(nueva_contrasena)
        db.session.commit()
        flash('Contraseña actualizada correctamente.', 'success')
        return redirect(url_for('usuarios.index'))

    # Si el formulario no es válido, mostrar errores
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{error}', 'danger')
    return redirect(url_for('usuarios.index'))