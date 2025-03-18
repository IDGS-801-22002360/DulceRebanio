from flask_wtf import FlaskForm
from wtforms import DateField, DecimalField, EmailField, IntegerField, SelectField, StringField, SubmitField, Form, validators
from wtforms.validators import DataRequired

#!======================= Modulo de Galletas =======================#  
class LoteForm(FlaskForm):
    sabor = SelectField('Sabor', choices=[
        ('', 'Seleccione un sabor'),
        ('Chocolate', 'Chocolate'),
        ('Vainilla', 'Vainilla'),
        ('Coco', 'Coco'),
        ('Chispas', 'Chispas'),
        ('Naranja', 'Naranja'),
        ('Integrales', 'Integrales'),
        ('Especiales', 'Especiales')
    ], validators=[DataRequired()])
    submit = SubmitField('Guardar')

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