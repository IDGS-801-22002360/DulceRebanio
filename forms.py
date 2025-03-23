from wtforms.validators import Optional
from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, DecimalField, EmailField, IntegerField, SelectField, StringField, SubmitField, Form, validators, HiddenField, SelectField, PasswordField, SubmitField, StringField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Optional, Email, Length, ValidationError
import re

#!======================= Modulo de Galletas =======================#  
class LoteForm(FlaskForm):
    sabor = SelectField('Sabor', validators=[DataRequired()])
    submit = SubmitField('Guardar')

class MermaForm(FlaskForm):
    idProducto = StringField('ID Producto', validators=[DataRequired()])
    cantidad = IntegerField('Cantidad', validators=[Optional()])
    mermar_todo = BooleanField('Mermar Todo')
    submit = SubmitField('Mermar')

class PaqueteForm(FlaskForm):
    tipo_producto = SelectField(
        "Tipo de Producto",
        choices=[
            (2, "Kilo"),
            (3, "Medio Kilo")
        ],
        coerce=int,  # Convierte el valor seleccionado a un entero
        validators=[DataRequired(message="El campo es requerido")]
    )
    cantidad = IntegerField(
        "Cantidad",
        validators=[
            DataRequired(message="El campo es requerido"),
            validators.NumberRange(min=1, message="La cantidad debe ser mayor a 0")
        ]
    )
    submit = SubmitField("Guardar")


#!======================= Modulo de Insumos =======================#  
class InsumoForm(Form):
    materiaPrima = StringField("Materia Prima", validators=[
        DataRequired(message="El campo es requerido")
    ])
    unidadMedida = StringField("Unidad de Medida", validators=[
        DataRequired(message="El campo es requerido")
    ])
    fechaCaducidad = DateField("Fecha de Caducidad", format="%Y-%m-%d", validators=[
        DataRequired(message="El campo es requerido")
    ])
    
class ProveedorForm(Form):
    nombreProveedor = StringField("Nombre del Proveedor", validators=[
        DataRequired(message="El campo es requerido")
    ])
    correo = EmailField("Correo", [
        validators.Email(message='Correo invalido')
    ])
    telefono = StringField("Teléfono", validators=[
        DataRequired(message="El campo es requerido")
    ])

class CompraInsumoForm(Form):
    idProveedor = SelectField("Proveedor", coerce=int, validators=[DataRequired(message="El campo es requerido")])
    idMateriaPrima = SelectField("Insumo", coerce=int, validators=[DataRequired(message="El campo es requerido")])
    cantidad = IntegerField("Cantidad", validators=[DataRequired(message="El campo es requerido")])
    fecha = DateField("Fecha de Compra", format="%Y-%m-%d", validators=[DataRequired(message="El campo es requerido")])
    totalCompra = DecimalField("Total Compra", validators=[DataRequired(message="El campo es requerido")])
    sabor = SelectField('Sabor', validators=[DataRequired()])
    submit = SubmitField('Guardar')

class MermaForm(FlaskForm):
    idProducto = StringField('ID Producto', validators=[DataRequired()])
    cantidad = IntegerField('Cantidad', validators=[Optional()])
    mermar_todo = BooleanField('Mermar Todo')
    submit = SubmitField('Mermar')

class PaqueteForm(FlaskForm):
    tipo_producto = SelectField(
        "Tipo de Producto",
        choices=[
            (2, "Kilo"),
            (3, "Medio Kilo")
        ],
        coerce=int,  # Convierte el valor seleccionado a un entero
        validators=[DataRequired(message="El campo es requerido")]
    )
    cantidad = IntegerField(
        "Cantidad",
        validators=[
            DataRequired(message="El campo es requerido"),
            validators.NumberRange(min=1, message="La cantidad debe ser mayor a 0")
        ]
    )
    submit = SubmitField("Guardar")


#!======================= Modulo de Insumos =======================#  
class InsumoForm(Form):
    materiaPrima = StringField("Materia Prima", validators=[
        DataRequired(message="El campo es requerido")
    ])
    unidadMedida = StringField("Unidad de Medida", validators=[
        DataRequired(message="El campo es requerido")
    ])
    fechaCaducidad = DateField("Fecha de Caducidad", format="%Y-%m-%d", validators=[
        DataRequired(message="El campo es requerido")
    ])
    
class ProveedorForm(Form):
    nombreProveedor = StringField("Nombre del Proveedor", validators=[
        DataRequired(message="El campo es requerido")
    ])
    correo = EmailField("Correo", [
        validators.Email(message='Correo invalido')
    ])
    telefono = StringField("Teléfono", validators=[
        DataRequired(message="El campo es requerido")
    ])

class CompraInsumoForm(Form):
    idProveedor = SelectField("Proveedor", coerce=int, validators=[DataRequired(message="El campo es requerido")])
    idMateriaPrima = SelectField("Insumo", coerce=int, validators=[DataRequired(message="El campo es requerido")])
    cantidad = IntegerField("Cantidad", validators=[DataRequired(message="El campo es requerido")])
    fecha = DateField("Fecha de Compra", format="%Y-%m-%d", validators=[DataRequired(message="El campo es requerido")])
    totalCompra = DecimalField("Total Compra", validators=[DataRequired(message="El campo es requerido")])
    sabor = SelectField('Sabor', validators=[DataRequired()])
    submit = SubmitField('Guardar')

class MermaForm(FlaskForm):
    idProducto = StringField('ID Producto', validators=[DataRequired()])
    cantidad = IntegerField('Cantidad', validators=[Optional()])
    mermar_todo = BooleanField('Mermar Todo')
    submit = SubmitField('Mermar')

def validate_contrasena(form, field):
    contrasena = field.data
    if len(contrasena) < 8:
        raise ValidationError('La contraseña debe tener al menos 8 caracteres.')
    if not re.search(r"[A-Z]", contrasena):
        raise ValidationError('La contraseña debe contener al menos una letra mayúscula.')
    if not re.search(r"[a-z]", contrasena):
        raise ValidationError('La contraseña debe contener al menos una letra minúscula.')
    if not re.search(r"[0-9]", contrasena):
        raise ValidationError('La contraseña debe contener al menos un número.')
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", contrasena):
        raise ValidationError('La contraseña debe contener al menos un carácter especial.')

class LoginForm(FlaskForm):
    correo = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    contrasena = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Ingresar')

class RegisterForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    apaterno = StringField('Apellido Paterno', validators=[DataRequired()])
    amaterno = StringField('Apellido Materno', validators=[DataRequired()])
    correo = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    contrasena = PasswordField('Contraseña', validators=[DataRequired(), validate_contrasena])
    submit = SubmitField('Registrarse')

class EmpleadoForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired()])
    apaterno = StringField('Apellido Paterno', validators=[DataRequired()])
    amaterno = StringField('Apellido Materno', validators=[DataRequired()])
    correo = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    contrasena = PasswordField('Contraseña', validators=[DataRequired(), validate_contrasena])
    rol = SelectField('Rol', choices=[('Admin', 'Admin'), ('Ventas', 'Ventas'), ('Produccion', 'Produccion')], validators=[DataRequired()])
    submit = SubmitField('Registrar')


class RecuperarContrasenaForm(FlaskForm):
    correo = StringField('Correo Electrónico', validators=[DataRequired(), Email()])
    nueva_contrasena = PasswordField('Nueva Contraseña', validators=[DataRequired(), validate_contrasena])
    confirmar_contrasena = PasswordField('Confirmar Contraseña', validators=[DataRequired()])
    submit = SubmitField('Cambiar Contraseña')

    def validate_confirmar_contrasena(self, field):
        if self.nueva_contrasena.data != field.data:
            raise ValidationError('Las contraseñas no coinciden.')