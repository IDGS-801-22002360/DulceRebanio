from flask_wtf import FlaskForm
from wtforms import HiddenField, SelectField, PasswordField, SubmitField, StringField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Optional, Email, Length, ValidationError
import re

class LoteForm(FlaskForm):
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