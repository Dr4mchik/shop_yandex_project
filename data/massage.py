import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .db_session import SqlAlchemyBase


class Message(SqlAlchemyBase):
    """Модель сообщений в чате"""
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Отправитель и получатель
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    recipient_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Связи с пользователями
    sender = relationship("User", foreign_keys=[sender_id])
    recipient = relationship("User", foreign_keys=[recipient_id])

    # Связь с заказом (необязательно)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=True)
    order = relationship("Order")

    # Содержимое сообщения
    text = Column(String, nullable=True)
    image = Column(String, nullable=True)  # Путь к изображению

    # Метаданные
    timestamp = Column(DateTime, default=datetime.datetime.now)
    is_read = Column(Boolean, default=False)