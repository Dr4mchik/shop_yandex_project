from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, IntegerField, FloatField, TextAreaField, SubmitField, BooleanField
from wtforms.validators import DataRequired, InputRequired, NumberRange


class ProductForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    price = FloatField('Цена', validators=[
        InputRequired(message="Введите корректное число"),
        NumberRange(min=0, message="Цена должна быть положительным числом")
    ])
    description = TextAreaField('Описание')
    image = FileField('Изображение продукта', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    amount_available = IntegerField('Количество товара')
    open = BooleanField('Открытый товар для всех', default=False)
    submit = SubmitField('Добавить товар')
