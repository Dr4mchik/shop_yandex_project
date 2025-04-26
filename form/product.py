from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, FloatField, TextAreaField, SubmitField
from wtforms.validators import DataRequired


class ProductForm(FlaskForm):
    name = StringField('Product name', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired()])
    description = TextAreaField('Description')
    image = FileField('Product image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Submit')
