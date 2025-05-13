from flask_restful import reqparse

order_item_parser = reqparse.RequestParser()
order_item_parser.add_argument('user_id', required=True, type=int)
order_item_parser.add_argument('product_id', required=True, type=int)
order_item_parser.add_argument('amount', required=True, type=int)

put_order_item_parser = reqparse.RequestParser()
order_item_parser.add_argument('amount', required=True, type=int)

order_parser = reqparse.RequestParser()
order_parser.add_argument('user_id', required=True, type=int)
order_parser.add_argument('comment', type=str)
