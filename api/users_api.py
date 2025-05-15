from flask_restful import reqparse, abort, Api, Resource
from flask import jsonify, Blueprint, make_response

from data import db_session
from data.user import User
from .users_parser import parser, put_parser

blueprint = Blueprint('users_api', __name__, template_folder='templates')
api = Api(blueprint)


def abort_if_users_not_found(users_id):
    db_sess = db_session.create_session()
    users = db_sess.query(User).filter(User.id == users_id).first()
    db_sess.close()
    if not users:
        abort(404, message=f"Users {users_id} not found")


class UsersResource(Resource):
    def get(self, users_id):
        abort_if_users_not_found(users_id)
        db_sess = db_session.create_session()
        users = db_sess.query(User).filter(User.id == users_id).first()
        db_sess.close()
        return jsonify({'users': users.to_dict(
            only=(
                'email', 'name', 'surname', 'hashed_password',
            ))})

    def delete(self, users_id):
        abort_if_users_not_found(users_id)
        db_sess = db_session.create_session()
        users = db_sess.query(User).filter(User.id == users_id).first()
        db_sess.delete(users)
        db_sess.commit()
        db_sess.close()
        return jsonify({'success': 'OK'})

    def put(self, users_id):
        args = put_parser.parse_args()
        password = args.get('password', '')
        new_password = args.get('new_password', '')
        balance = args.get('balance', 0)
        db_sess = db_session.create_session()
        text_for_response = []
        try:
            users = db_sess.query(User).filter(User.id == users_id).first()
            if not users:
                return make_response({'error': f'no user {users_id} (PUT)'}, 400)
            if password and new_password:
                if users.check_password(password):
                    users.set_password(new_password)
                    text_for_response.append('password change')
            if balance:
                users.balance += balance
                text_for_response.append('balance append')
            db_sess.commit()
            return make_response(jsonify({'OK': '|'.join(text_for_response)}))
        finally:
            db_sess.close()


class UsersListResource(Resource):
    def get(self):
        db_sess = db_session.create_session()
        users = db_sess.query(User).all()
        db_sess.close()
        return jsonify({'users': [item.to_dict(
            only=('id', 'email', 'name', 'surname', 'hashed_password', 'modified_date', 'balance'
                  )) for item in users]})

    def post(self):
        args = parser.parse_args()
        db_sess = db_session.create_session()
        try:
            user = db_sess.query(User).filter(User.email == args['email']).first()
            if user:
                return make_response(jsonify({'erorr': 'a user with email address has already been registered'}), 400)
            users = User(
                name=args['name'],
                surname=args['surname'],
                email=args['email'],
            )
            users.set_password(args['password'])
            db_sess.add(users)
            db_sess.commit()
            return jsonify({'id': users.id})
        finally:
            db_sess.close()


api.add_resource(UsersResource, '/api/users/<int:users_id>')
api.add_resource(UsersListResource, '/api/users/')
