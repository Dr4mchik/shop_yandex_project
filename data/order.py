import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from .db_session import SqlAlchemyBase


class OrderItem(SqlAlchemyBase):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    amount = Column(Integer, nullable=1, default=1)

    # Связи
    product = relationship('Product')
