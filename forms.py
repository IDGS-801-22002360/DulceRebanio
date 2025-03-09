from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired

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