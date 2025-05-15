from flask_restful import reqparse

parser = reqparse.RequestParser()
parser.add_argument('name', required=True)
parser.add_argument('surname', required=True)
parser.add_argument('email', required=True)
parser.add_argument('password', required=True)

put_parser = reqparse.RequestParser()
put_parser.add_argument('password', type=str)
put_parser.add_argument('new_password', type=str)
put_parser.add_argument('balance', type=int)