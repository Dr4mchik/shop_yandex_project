import datetime
from .db_session import SqlAlchemyBase
import sqlalchemy
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin


class User(SqlAlchemyBase, UserMixin):
    """Модель пользователя"""
    __tablename__ = 'users'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    surname = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    email = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    hashed_password = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    role = sqlalchemy.Column(sqlalchemy.Integer)
    # роль для управлений правами пользователя
    # для привязки к магазину, например владелец магазина, продавец
    products = sqlalchemy.orm.relationship("Product", back_populates="user")

    def __repr__(self):
        return f'<User> -- {self.id} | {self.surname} | {self.name} | {self.email}'

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
