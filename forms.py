from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, StringField, IntegerField, widgets, validators, BooleanField
from wtforms.validators import DataRequired, Regexp, Optional

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

class MermaForm(FlaskForm):
    idProducto = StringField('ID Producto', validators=[DataRequired()])
    cantidad = IntegerField('Cantidad', validators=[Optional()])
    mermar_todo = BooleanField('Mermar Todo')
    submit = SubmitField('Mermar')