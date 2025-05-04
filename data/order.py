import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class OrderItem(SqlAlchemyBase):
    __tablename__ = 'order_items'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    product_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("products.id"))
    amount = sqlalchemy.Column(sqlalchemy.Integer, default=1)
    is_in_order = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    order_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("orders.id"), nullable=True)

    user = orm.relationship('User')
    product = orm.relationship('Product')
    order = orm.relationship('Order', back_populates='items')


class Order(SqlAlchemyBase):
    __tablename__ = 'orders'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"))
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    status = sqlalchemy.Column(sqlalchemy.String, default='new')  # new, paid, delivered, completed, cancelled
    total_price = sqlalchemy.Column(sqlalchemy.Float, nullable=False)

    # Контактная информация
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    surname = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    email = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    phone = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    # Доставка
    delivery_type = sqlalchemy.Column(sqlalchemy.String, nullable=False)  # self_pickup, pickup_point
    delivery_service = sqlalchemy.Column(sqlalchemy.String, nullable=True)  # yandex, wildberries, ozon, pochta, cdek
    pvz_info = sqlalchemy.Column(sqlalchemy.String, nullable=True)  # JSON с информацией о ПВЗ
    delivery_cost = sqlalchemy.Column(sqlalchemy.Float, default=0.0)

    # Оплата
    payment_method = sqlalchemy.Column(sqlalchemy.String, nullable=False)  # balance, card, cod
    is_paid = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    payment_date = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True)

    # Комментарий
    comment = sqlalchemy.Column(sqlalchemy.Text, nullable=True)

    user = orm.relationship('User')
    items = orm.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')