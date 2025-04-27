from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, IntegerField, FloatField, TextAreaField, SubmitField, BooleanField
from wtforms.validators import DataRequired


class ProductForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    price = FloatField('Цена', validators=[DataRequired()])
    description = TextAreaField('Описание')
    image = FileField('Изображение продукта', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    amount_available = IntegerField('Количество товара')
    open = BooleanField('Открытый товар для всех', default=False)
    submit = SubmitField('Добавить товар')
