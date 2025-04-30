import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from .db_session import SqlAlchemyBase


class Order(SqlAlchemyBase):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_date = Column(DateTime, default=datetime.datetime.now)
    total_price = Column(Float, nullable=False)
    status = Column(String, default='new')

    # Связь с пользователем
    user = relationship('User', back_populates='orders')
    # Связь с товарами в заказе
    products = relationship('OrderItem', back_populates='order')


class OrderItem(SqlAlchemyBase):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, default=1)
    price = Column(Float, nullable=False)  # Сохраняем цену на момент заказа

    # Связи
    order = relationship('Order', back_populates='products')
    product = relationship('Product')