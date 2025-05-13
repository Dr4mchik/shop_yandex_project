import flask
from flask_restful import reqparse, abort, Api, Resource
from flask import Blueprint, jsonify, request, make_response
from sqlalchemy.exc import StatementError
from .products_parser import parser, put_parser

from data import db_session
from data.product import Product

from sqlalchemy import and_

blueprint = Blueprint('products_api', __name__, template_folder='templates')
api = Api(blueprint)


def abort_if_products_not_found(products_id):
    session = db_session.create_session()
    products = session.query(Product).filter(Product.id == products_id).first()
    if not products:
        abort(400, message=f"Products {products_id} not found")


class ProductsResource(Resource):
    def get(self, products_id):
        abort_if_products_not_found(products_id)
        db_sess = db_session.create_session()
        products = db_sess.query(Product).filter(
            and_(products_id == Product.id)
        ).first()
        return jsonify(
            {
                'products': products.to_dict(
                    only=('id', 'name', 'price', 'description', 'created_date', 'amount_available', 'image', 'user_id')
                )
            }
        )

    def delete(self, products_id):
        abort_if_products_not_found(products_id)
        db_sess = db_session.create_session()
        products = db_sess.query(Product).filter(Product.id == products_id).first()
        db_sess.delete(products)
        db_sess.commit()
        return jsonify({'success': 'OK'})

    def put(self, products_id):
        abort_if_products_not_found(products_id)
        args = put_parser.parse_args()
        none = [i for i in args if args[i] is None]  # находим пустые значения словаря
        for i in none:
            args.pop(i)  # удаляем элементы с пустыми ключами

        db_sess = db_session.create_session()
        products = db_sess.query(Product).filter(
            products_id == Product.id
        ).first()

        new_products = Product(
            name=args.get('name', products.name),
            price=args.get('price', products.proce),
            description=args.get('description', products.description),
            open=args.get('open', products.open),
            amount_available=args.get('amount_available', products.amount_available),
            user_id=args.get('user_id', products.user_id)
        )

        products.name = new_products.name
        products.price = new_products.price
        products.description = new_products.description
        products.open = new_products.open
        products.amount_available = new_products.amount_available
        products.user_id = new_products.user_id

        db_sess.commit()
        return jsonify({'OK': 'success'})


class ProductsListResource(Resource):
    def get(self):
        db_sess = db_session.create_session()
        products = db_sess.query(Product).filter(Product.open == True).all()
        return jsonify(
            {
                'products': [item.to_dict(
                    only=('id', 'name', 'price', 'description', 'created_date', 'amount_available', 'image', 'user_id')
                ) for item in products]
            }
        )

    def post(self):
        args = parser.parse_args()

        none = [i for i in args if args[i] is None]  # находим пустые значения словаря
        for i in none:
            args.pop(i)  # удаляем элементы с пустыми ключами

        try:
            db_sess = db_session.create_session()
            product = Product(
                name=args['name'],
                price=args['price'],
                description=args.get('description', ''),
                open=args.get('open', 0),
                amount_available=args.get('amount_available', 0),
                user_id=args.get('user_id', None)
            )
            db_sess.add(product)
            db_sess.commit()
            return jsonify({'id': f'{product.id}'})
        except StatementError:  # обработка не правильных данных
            return make_response(jsonify({'error': 'Bad request'}), 400)
        except Exception as e:
            return make_response(jsonify({'error': f'{e.__class__.__name__}'}, 500))


api.add_resource(ProductsListResource, '/api/products/')
api.add_resource(ProductsResource, '/api/products/<int:products_id>')
