from flask import Blueprint
from flask_restful import Api,output_json
from . import login
user_bp = Blueprint("user",__name__)

user_api = Api(user_bp,catch_all_404s=True)
user_api.representation('application/json')(output_json)

user_api.add_resource(login.PhoneLogin,"/v1/login/phoneLogin",endpoint="auth")
