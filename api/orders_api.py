import datetime

import flask
from flask_restful import reqparse, abort, Api, Resource
from flask import Blueprint, jsonify, request, make_response, url_for
from .orders_parser import order_item_parser, put_order_item_parser, order_parser
from sqlalchemy import and_

from data import db_session
from data.order import OrderItem, Order
from data.product import Product

blueprint = Blueprint('order_api', __name__, template_folder='templates')
api = Api(blueprint)


class OrdersItemsListResource(Resource):
    def get(self):
        db_sess = db_session.create_session()
        orders_items_list = db_sess.query(OrderItem).all()
        return jsonify(
            {
                'orders_items': [item.to_dict(
                    only=('id', 'user_id', 'product_id', 'amount', 'is_in_order', 'order_id',)
                ) for item in orders_items_list]
            }
        )

    def post(self):
        args = order_item_parser.parse_args()
        product_id = args['product_id']
        current_user = args['user_id']

        db_sess = db_session.create_session()
        # проверим на наличие такого же товара в корзине

        order_item = db_sess.query(OrderItem).filter(
            and_(OrderItem.product_id == product_id, OrderItem.user_id == current_user.id,
                 OrderItem.is_in_order == False)
        ).first()
        if order_item:
            if order_item.product.amount_available >= order_item.amount + args['amount']:  # добавляем товар к товару
                order_item.amount += args['amount']
                db_sess.commit()
                return jsonify({'OK': 'success'})
            else:  # превысили доступный товар
                db_sess.close()
                return make_response(jsonify({'error': f'{args['amount'] + order_item.amount} not available'}), 400)

        order_item = OrderItem(
            user_id=product_id,
            product_id=current_user,
            amount=args['amount'],
        )
        db_sess.add(order_item)
        db_sess.commit()
        return jsonify({'id': {order_item.id}})


class OrdersItemsResource(Resource):
    def get(self, orders_items_id):
        db_sess = db_session.create_session()
        orders_items = db_sess.query(OrderItem).filter(OrderItem.id == orders_items_id).first()
        if not orders_items:
            return make_response(jsonify({'error': f'{orders_items_id} id not found'}), 400)
        return jsonify(
            {
                'orders_items': orders_items.to_dict(
                    only=('id', 'user_id', 'product_id', 'amount', 'is_in_order', 'order_id',)
                )
            }
        )

    def put(self, orders_items_id):
        """Обновляем только кол-во товара"""
        args = put_order_item_parser.parse_args()
        db_sess = db_session.create_session()
        orders_items = db_sess.query(OrderItem).filter(OrderItem.id == orders_items_id).first()
        if not orders_items:
            return make_response(jsonify({'error': f'{orders_items_id} id not found'}), 400)

        if orders_items.product.amount_available < args['amount']:  # нету такого кол-во товара для покупки
            return make_response(jsonify({'error': f'{args['amount']} not available'}), 400)
        orders_items.amount = args['amount']
        db_sess.commit()
        return jsonify({'OK': 'success'})

    def delete(self, orders_items_id):
        db_sess = db_session.create_session()
        orders_items = db_sess.query(OrderItem).filter(OrderItem.id == orders_items_id).first()
        if not orders_items:
            return make_response(jsonify({'error': f'{orders_items_id} id not found'}), 400)
        db_sess.delete(orders_items)
        db_sess.commit()
        return jsonify({'success': 'OK'})


class OrdersListResource(Resource):
    def get(self):
        db_sess = db_session.create_session()
        orders = db_sess.query(Order).all()
        return jsonify(
            {
                'orders': [item.to_dict(
                    only=('id', 'user_id', 'created_date', 'status', 'total_price', 'phone', 'delivery_type',
                          'delivery_service', 'pvz_info', 'delivery_cost', 'payment_method', 'is_paid', 'payment_date',
                          'comment')
                ) for item in orders]
            }
        )

    def post(self):
        args = order_parser.parse_args()
        user_id = args['user_id']
        db_sess = db_session.create_session()

        order_items_users = db_sess.query(OrderItem).filter(and_(
            OrderItem.user_id == user_id,
            OrderItem.is_in_order == False
        )).all()

        # перепроверим все ли в корзине предметы доступны, вдруг что-то закончилось
        for item in order_items_users:
            product = db_sess.query(Product).filter(Product.id == item.product_id).first()
            if product.amount_available < item.amount:
                db_sess.close()
                return make_response(jsonify({'error': f'not available amount product id {product.id}'}), 400)

        if not order_items_users:
            return make_response(jsonify({'error': f'no orders items by user id {user_id}'}), 400)

        product_price_sum = sum([item.amount * item.product.price for item in order_items_users])

        if user_id.balance < product_price_sum:
            return make_response(jsonify({'error': f'no many for buy by user id {user_id}'}), 400)

        order = Order(
            user_id=user_id,
            created_date=datetime.datetime.now(),
            status='new',
            total_price=product_price_sum,
            is_paid=1,
            comment=args.get('comment', ''),
        )

        db_sess.add(order)
        db_sess.commit()

        user_id.balance -= product_price_sum

        for item in order_items_users:
            item.is_in_order = True
            item.order_id = order.id

        return jsonify({'OK': 'success'})


class OrdersResource(Resource):
    def get(self, orders_id):
        db_sess = db_session.create_session()
        orders = db_sess.query(Order).filter(Order.id == orders_id).first()
        if not orders:
            return make_response(jsonify({'error': f'id orders {orders_id} not found'}), 400)
        return jsonify(
            {
                'orders': orders.to_dict(
                    only=('id', 'user_id', 'created_date', 'status', 'total_price', 'phone', 'delivery_type',
                          'delivery_service', 'pvz_info', 'delivery_cost', 'payment_method', 'is_paid', 'payment_date',
                          'comment')
                )
            }
        )


api.add_resource(OrdersItemsListResource, '/api/orders_items/')
api.add_resource(OrdersItemsResource, '/api/orders_items/<int:orders_items_id>')
api.add_resource(OrdersListResource, '/api/orders/')
api.add_resource(OrdersResource, '/api/orders/<int:orders_id>')
