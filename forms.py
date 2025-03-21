from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, StringField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Optional

class LoteForm(FlaskForm):
    sabor = SelectField('Sabor', validators=[DataRequired()])
    submit = SubmitField('Guardar')

class MermaForm(FlaskForm):
    idProducto = StringField('ID Producto', validators=[DataRequired()])
    cantidad = IntegerField('Cantidad', validators=[Optional()])
    mermar_todo = BooleanField('Mermar Todo')
    submit = SubmitField('Mermar')
    