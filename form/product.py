from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, FloatField, TextAreaField, SubmitField, BooleanField
from wtforms.validators import DataRequired


class ProductForm(FlaskForm):
    name = StringField('Product name', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired()])
    description = TextAreaField('Description')
    image = FileField('Product image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    amount_available = FileField('Amount available')
    open = BooleanField('Open')
    submit = SubmitField('Submit')
