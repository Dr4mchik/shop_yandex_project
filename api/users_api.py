from flask_restful import reqparse, abort, Api, Resource
from flask import jsonify, Blueprint

from data import db_session
from data.user import User
from .users_parser import parser, put_parser

blueprint = Blueprint('users_api', __name__, template_folder='templates')
api = Api(blueprint)


def abort_if_users_not_found(users_id):
    db_sess = db_session.create_session()
    users = db_sess.query(User).filter(User.id == users_id).first()
    if not users:
        abort(404, message=f"Users {users_id} not found")


class UsersResource(Resource):
    def get(self, users_id):
        abort_if_users_not_found(users_id)
        db_sess = db_session.create_session()
        users = db_sess.query(User).filter(User.id == users_id).first()
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
        return jsonify({'success': 'OK'})

    def put(self, users_id):
        args = put_parser.parse_args()
        password = args['password']
        new_password = args['new_password']

        db_sess = db_session.create_session()
        users = db_sess.query(User).filter(User.id == users_id).first()
        if users.check_password(password):
            users.set_password(password)


class UsersListResource(Resource):
    def get(self):
        session = db_session.create_session()
        users = session.query(User).all()
        return jsonify({'users': [item.to_dict(
            only=('id', 'email', 'name', 'surname', 'hashed_password', 'modified_date', 'balance'
                  )) for item in users]})

    def post(self):
        args = parser.parse_args()
        db_sess = db_session.create_session()
        users = User(
            name=args['name'],
            surname=args['surname'],
            email=args['email'],
        )
        users.set_password(args['password'])
        db_sess.add(users)
        db_sess.commit()
        return jsonify({'id': users.id})


api.add_resource(UsersResource, '/api/users/<int:users_id>')
api.add_resource(UsersListResource, '/api/users/')
