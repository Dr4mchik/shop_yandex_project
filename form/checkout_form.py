from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Regexp, Length


class CheckoutForm(FlaskForm):
    # Контактная информация
    name = StringField('Имя', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    email = StringField('Email', validators=[
        DataRequired(),
        Regexp(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
               message='Invalid email address.')
    ])
    phone = StringField('Телефон', validators=[DataRequired(), Length(min=10, max=12)])

    # Доставка
    delivery_type = SelectField('Способ доставки', choices=[
        ('self_pickup', 'Самовывоз'),
        ('pickup_point', 'Пункт выдачи заказов')
    ], validators=[DataRequired()])

    # Пункт выдачи
    delivery_service = SelectField('Служба доставки', choices=[
        ('yandex', 'Яндекс.Доставка'),
        ('wildberries', 'Wildberries'),
        ('ozon', 'Ozon'),
        ('pochta', 'Почта России'),
        ('cdek', 'СДЭК')
    ])
    address = StringField('Адрес')
    selected_pvz = HiddenField('Выбранный ПВЗ')

    # Оплата
    payment_method = SelectField('Способ оплаты', choices=[
        ('cash', 'Наличными при получении'),
        ('card', 'Банковской картой при получении'),
        ('online', 'Банковской картой онлайн'),
        ('balance', 'С баланса пользователя')
    ], validators=[DataRequired()])

    # Для онлайн оплаты
    card_number = StringField('Номер карты')
    card_expiry = StringField('Срок действия')
    card_cvv = StringField('CVV')

    # Комментарий
    comment = TextAreaField('Комментарий к заказу')