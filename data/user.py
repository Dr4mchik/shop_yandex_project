from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    name = Column(String, nullable=False)
    modified_date = Column(DateTime)
    # Добавляем поле баланса пользователя с дефолтным значением 0
    balance = Column(Float, default=0.0, nullable=False)

    # Связь с продуктами
    products = relationship("Product", back_populates="user")

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)
