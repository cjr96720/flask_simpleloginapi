from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_marshmallow import Marshmallow
import os
from dotenv import load_dotenv
import json
# from connection import my_cursor

# access to .env file
load_dotenv()

# create an app and add middlewares
app = Flask(__name__)
CORS(app)
api = Api(app)

# config
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{os.environ.get("MYSQL_USER")}:{os.environ.get("MYSQL_PASSWORD")}@{os.environ.get("MYSQL_HOST")}/{os.environ.get("MYSQL_DATABASE")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)

# for password hashing
bcrypt = Bcrypt(app)

############################################
# models


class Members(db.Model):

    __tablename__ = 'members'

    memberid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    membername = db.Column(db.String(50))
    memberemail = db.Column(db.String(300), unique=True, index=True)
    memberpwd = db.Column(db.String(300))

    def __init__(self, membername, memberemail, memberpwd):
        self.membername = membername
        self.memberemail = memberemail
        self.memberpwd = bcrypt.generate_password_hash(memberpwd)

    def __repr__(self):
        return f'Name: {self.membername}, Email: {self.memberemail}'


############################################

############################################
# create schema


class MembersSchema(ma.Schema):
    class Meta:
        fields = (
            'memberid',
            'membername',
            'memberemail',
            'memberpwd'
        )


member_schema = MembersSchema()
members_schema = MembersSchema(many=True)

############################################


############################################
# APIs

class EmailCheck(Resource):

    def get(self):
        memberemail = request.json['memberemail']
        member = Members.query.filter_by(memberemail=memberemail).first()
        if member:
            return {'Message': 'Member exists'}


class Login(Resource):
    
    def post(self):
        memberemail = request.json['memberemail']
        memberpwd = request.json['memberpwd']

        member = Members.query.filter_by(memberemail=memberemail).first()
        if member:
            pwd = Members.query.filter_by(
                memberemail=memberemail).with_entities(Members.memberpwd).first()
            result = member_schema.dumps(pwd)
            print(result)
            result_json = json.loads(result)
            password = bcrypt.check_password_hash(
                result_json['memberpwd'], memberpwd)
            if not password:
                return {'Message' : 'Wrong password'}
        else:
            return {'Message' : 'Member does not exist'}


class Register(Resource):

    def post(self):
        membername = request.json['membername']
        memberemail = request.json['memberemail']
        memberpwd = request.json['memberpwd']
        member = Members(membername, memberemail, memberpwd)
        db.session.add(member)
        db.session.commit()
        return member_schema.jsonify(member)


class ShowMembers(Resource):

    def get(self):
        all_members = Members.query.all()
        results = members_schema.dump(all_members)
        return jsonify(results)


# add api route
api.add_resource(ShowMembers, '/showmembers')
api.add_resource(Register, '/register')
api.add_resource(EmailCheck, '/emailCheck')
api.add_resource(Login, '/login')

############################################


if __name__ == '__main__':
    app.run(debug=True)
