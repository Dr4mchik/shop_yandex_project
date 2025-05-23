import datetime
from .db_session import SqlAlchemyBase
import sqlalchemy

from sqlalchemy_serializer import SerializerMixin


class Product(SqlAlchemyBase, SerializerMixin):
    """модель товара"""
    __tablename__ = 'products'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    price = sqlalchemy.Column(sqlalchemy.Float, nullable=False)
    description = sqlalchemy.Column(sqlalchemy.Text)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    category_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("categories.id"), nullable=True)


    open = sqlalchemy.Column(sqlalchemy.Boolean)  # открыт ли продукт для общего доступа
    amount_available = sqlalchemy.Column(sqlalchemy.Integer)  # сколько есть продукта для продажи
    amount_sell = sqlalchemy.Column(sqlalchemy.Integer)  # сколько продано для статистики
    category = sqlalchemy.orm.relationship('Category', back_populates="products")

    image = sqlalchemy.Column(sqlalchemy.String)

    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    user = sqlalchemy.orm.relationship('User', back_populates='products')

    def __repr__(self):
        return f'{self.name}'
