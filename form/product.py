from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, IntegerField, FloatField, TextAreaField, SubmitField, BooleanField
from wtforms.validators import DataRequired


class ProductForm(FlaskForm):
    name = StringField('Product name', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired()])
    description = TextAreaField('Description')
    image = FileField('Product image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    amount_available = IntegerField('Amount available')
    open = BooleanField('Open product for all', default=False)
    submit = SubmitField('Submit')
