from flask_restful import Resource
from flask_restful.reqparse import RequestParser

from utils import parsers

class GetSms(Resource):
    pass

class PhoneLogin(Resource):
    def post(self):
        """
        手机号登录
        :return:
        """
        parser = RequestParser()
        parser.add_argument("mobile",type=parsers.mobile,required=True,location="json")
        parser.add_argument("sms_code",type=parsers.regex(r"^\d{6}$"),required=True,localtion="json")
        args = parser.parse_args()
        mobile = args.mobile
        sms_code = args.sms_code
        print(mobile,sms_code)
        return {"token": 123, "refresh_token": 123}, 201



class PasswdLogin(Resource):
    pass




