from flask import Flask, render_template, request, jsonify, redirect, session, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_wtf import CSRFProtect
from config import DevelopmentConfig
from models import db, ProductosTerminados, Sabores, DetallesProducto, Usuarios
from forms import EmpleadoForm, LoteForm, MermaForm, LoginForm, RecuperarContrasenaForm, RegisterForm
from sqlalchemy import text
from datetime import datetime, timedelta

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
csrf = CSRFProtect()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Usuarios.query.get(int(user_id))

failed_attempts = {}

@app.route("/", methods=["GET", "POST"])
@app.route("/index")
def index():
    login_form = LoginForm()
    register_form = RegisterForm()
    return render_template("client/mainClientes.html", login_form=login_form, register_form=register_form)

#!=============== Modulo de Productos ===============#  

@app.route("/galletas", methods=["GET", "POST"])
@login_required  # Proteger la ruta con Flask-Login
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
@login_required  # Proteger la ruta con Flask-Login
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
@login_required  # Proteger la ruta con Flask-Login
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
    return render_template('404.html'), 404

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        correo = form.correo.data
        contrasena = form.contrasena.data

        if correo in failed_attempts:
            last_attempt_time, attempts = failed_attempts[correo]
            if attempts >= 3 and datetime.now() - last_attempt_time < timedelta(minutes=1):
                flash('Demasiados intentos fallidos. Por favor, espera un minuto antes de intentar nuevamente.', 'danger')
                return render_template("client/mainClientes.html", login_form=form, register_form=RegisterForm())

        usuario = Usuarios.query.filter_by(correo=correo).first()

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
                    return redirect(url_for('galletas'))
                elif usuario.rol == 'Ventas':
                    return redirect(url_for('galletas'))
                elif usuario.rol == 'Admin':
                    return redirect(url_for('galletas'))
                elif usuario.rol == 'Produccion':
                    return redirect(url_for('galletas'))
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
    return render_template("client/mainClientes.html", login_form=form, register_form=RegisterForm())

@app.route("/logout")
@login_required 
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente.', 'success')
    return redirect(url_for('login'))


@app.route("/register", methods=["GET", "POST"])
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
            return redirect(url_for('login'))
    return render_template("client/mainClientes.html", login_form=LoginForm(), register_form=form)

@app.route("/usuarios", methods=["GET", "POST"])
@login_required
def usuarios():
    form = EmpleadoForm()
    usuarios = Usuarios.query.filter_by(activo=1).all()
    
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
        return redirect(url_for('usuarios'))
    
    return render_template("admin/usuarios.html", form=form, usuarios=usuarios, ultimo_login=current_user.ultimo_login)

@app.route("/eliminar_usuario/<int:id_usuario>", methods=["POST"])
@login_required
def eliminar_usuario(id_usuario):
    usuario = Usuarios.query.get(id_usuario)
    if usuario:
        usuario.activo = 0 
        db.session.commit()
        flash('Usuario eliminado correctamente.', 'success')
    else:
        flash('Usuario no encontrado.', 'danger')
    return redirect(url_for('usuarios'))



def is_password_insecure(contrasena):
    with open('insecure_passwords.txt', 'r') as file:
        insecure_passwords = [line.strip() for line in file]
    return contrasena in insecure_passwords


if __name__ == '__main__':
    csrf.init_app(app)
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    app.run()