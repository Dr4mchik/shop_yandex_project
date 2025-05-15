from flask_restful import reqparse

parser = reqparse.RequestParser()
parser.add_argument('user_id', type=int, required=True)
parser.add_argument('name', type=str, required=True)
parser.add_argument('price', type=float, required=True)
parser.add_argument('description', type=str)
parser.add_argument('open', type=bool)
parser.add_argument('amount_available', type=int)

put_parser = reqparse.RequestParser()
parser.add_argument('name', type=str)
parser.add_argument('price', type=float)
parser.add_argument('description', type=str)
parser.add_argument('open', type=bool)
parser.add_argument('amount_available', type=int)
parser.add_argument('user_id', type=int)