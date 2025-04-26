from flask_wtf import FlaskForm
from wtforms import PasswordField, EmailField, StringField, SubmitField
from wtforms.validators import DataRequired


class RegistrationForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    name = StringField('name', validators=[DataRequired()])
    surname = StringField('Surname', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    repeat_password = PasswordField('Repeat password', validators=[DataRequired()])
    submit = SubmitField('Submit')
