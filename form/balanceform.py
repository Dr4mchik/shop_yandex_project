from flask_wtf import FlaskForm
from wtforms import FloatField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class BalanceForm(FlaskForm):
    amount = FloatField('Сумма пополнения',
                       validators=[DataRequired(),
                                  NumberRange(min=1, message='Минимальная сумма пополнения 1 рубль')])
    submit = SubmitField('Пополнить баланс')