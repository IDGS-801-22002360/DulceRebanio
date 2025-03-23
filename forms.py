from wtforms.validators import Optional
from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, DecimalField, EmailField, IntegerField, SelectField, StringField, SubmitField, Form, validators
from wtforms.validators import DataRequired

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