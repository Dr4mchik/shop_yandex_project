import datetime
from .db_session import SqlAlchemyBase
import sqlalchemy


class Product(SqlAlchemyBase):
    """модель товара"""
    __tablename__ = 'products'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    price = sqlalchemy.Column(sqlalchemy.Float, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.Text)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    open = sqlalchemy.Column(sqlalchemy.Boolean)  # открыт ли продукт для общего доступа
    amount_available = sqlalchemy.Column(sqlalchemy.Integer)  # сколько есть продукта для продажи
    amount_sell = sqlalchemy.Column(sqlalchemy.Integer)  # сколько продано для статистики

    image = sqlalchemy.Column(sqlalchemy.String)

    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    user = sqlalchemy.orm.relationship('User', back_populates='products')
