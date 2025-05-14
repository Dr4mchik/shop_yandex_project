import datetime
import sqlalchemy
from sqlalchemy import orm
from flask_login import current_user
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class OrderStatus:
    NEW = 'new'
    PAID = 'paid'
    PROCESSING = 'processing'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    RETURNED = 'returned'
    CHAT_ONLY = 'chat_only'

    @classmethod
    def get_buyer_viewable_statuses(cls):
        return {
            cls.NEW: 'Новый',
            cls.PAID: 'Оплачен',
            cls.PROCESSING: 'В обработке',
            cls.SHIPPED: 'Отправлен',
            cls.DELIVERED: 'Доставлен',
            cls.COMPLETED: 'Завершен',
            cls.CANCELLED: 'Отменен',
            cls.RETURNED: 'Возврат',
            cls.CHAT_ONLY: 'Только чат'
        }

    @classmethod
    def get_seller_status_actions(cls):
        return {
            cls.NEW: [cls.PROCESSING, cls.CANCELLED],
            cls.PAID: [cls.PROCESSING, cls.CANCELLED],
            cls.PROCESSING: [cls.SHIPPED, cls.CANCELLED],
            cls.SHIPPED: [cls.DELIVERED, cls.RETURNED],
            cls.DELIVERED: [cls.COMPLETED, cls.RETURNED],
            cls.COMPLETED: [],
            cls.CANCELLED: [],
            cls.RETURNED: [],
            cls.CHAT_ONLY: []
        }


class OrderItem(SqlAlchemyBase, SerializerMixin):
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

    def sum_price(self) -> float:
        return self.amount * self.product.price


class Order(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'orders'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    status = sqlalchemy.Column(sqlalchemy.String, default=OrderStatus.NEW)
    total_price = sqlalchemy.Column(sqlalchemy.Float)

    # Контактная информация
    name = sqlalchemy.Column(sqlalchemy.String)
    surname = sqlalchemy.Column(sqlalchemy.String)
    email = sqlalchemy.Column(sqlalchemy.String)
    phone = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    # Информация о доставке
    delivery_type = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    delivery_service = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    pvz_info = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    delivery_cost = sqlalchemy.Column(sqlalchemy.Float, default=0.0)

    # Информация об оплате
    payment_method = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    is_paid = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    payment_date = sqlalchemy.Column(sqlalchemy.DateTime, nullable=True)

    # Комментарий к заказу
    comment = sqlalchemy.Column(sqlalchemy.Text, nullable=True)

    # Флаг, указывающий, были ли средства переданы продавцу
    balance_transferred = sqlalchemy.Column(sqlalchemy.Boolean, default=False)

    # Отношения
    user = orm.relationship('User')
    items = orm.relationship('OrderItem', back_populates='order')
    status_history = orm.relationship('OrderStatusHistory', back_populates='order',
                                      order_by='OrderStatusHistory.timestamp.desc()')

    def get_items_count(self):
        return sum(item.amount for item in self.items)

    def get_status_display(self):
        return OrderStatus.get_buyer_viewable_statuses().get(self.status, self.status)

    def get_available_status_changes(self, user):
        is_seller = any(item.product.user_id == user.id for item in self.items)

        if is_seller:
            return OrderStatus.get_seller_status_actions().get(self.status, [])

        return []


class OrderStatusHistory(SqlAlchemyBase):
    __tablename__ = 'order_status_history'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    order_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('orders.id'))
    status = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    timestamp = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    comment = sqlalchemy.Column(sqlalchemy.Text, nullable=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))

    # Отношения
    order = orm.relationship('Order')
    user = orm.relationship('User')

    def get_status_display(self):
        return OrderStatus.get_buyer_viewable_statuses().get(self.status, self.status)