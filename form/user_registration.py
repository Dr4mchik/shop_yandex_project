from flask_wtf import FlaskForm
from wtforms import PasswordField, EmailField, StringField, SubmitField
from wtforms.validators import DataRequired


class RegistrationForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    name = StringField('Имя', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    repeat_password = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')
