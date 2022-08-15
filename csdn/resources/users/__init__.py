from flask import Blueprint
from flask_restful import Api,output_json
from . import login,profiles
user_bp = Blueprint("user",__name__)

user_api = Api(user_bp,catch_all_404s=True)
user_api.representation('application/json')(output_json)

user_api.add_resource(login.PhoneLogin,"/v1/login/auth",endpoint="auth")
user_api.add_resource(login.GetSms,"/v1/login/smscode/<mobile:mobile>",endpoint="smscode")
user_api.add_resource(login.PasswdLogin,"/v1/login",endpoint="login")
user_api.add_resource(profiles.Profile,"/v1/curr/user",endpoint="curruser")
