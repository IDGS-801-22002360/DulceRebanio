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