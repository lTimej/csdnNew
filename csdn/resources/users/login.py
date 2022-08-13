import random
import datetime

from flask import current_app

from flask_restful import Resource
from flask_restful.reqparse import RequestParser

from models import db
from utils import parsers
from . import constants
from celery_tasks.sms.tasks import send_sms_code
from utils.get_token import getJWT

from redis.exceptions import ConnectionError

from models.user import User,UserProfile
from utils.generate_username import get_username

class GetSms(Resource):
    def get(self,mobile):
        """
        获取验证码
        :param mobile:手机号
        :return:
        """
        #随机生成6位数的验证码
        sms_code = "{:>6}".format(random.randint(0,999999))
        print("短信验证码：",sms_code)
        #发送短信
        try:
            # res = send_sms_code(mobile,sms_code)
            #发送成功将验证码存入redis   setex(键，过期时间，值）
            current_app.redis_master.setex("app:code:{}".format(mobile),constants.SMS_VERIFICATION_CODE_EXPIRES,sms_code)
            return {"msg": "发送成功"}, 201
        except Exception as e:
            return {"msg": "发送失败，请稍后重试"}, 401

class PhoneLogin(Resource):
    def get_token(self,user_id,refresh=True):
        '''
        第一次同时获取token和refreshtoken
        :param user_id:用户id
        :param refresh:refresh_token过期，则需要重新获取
        :return:token和自动刷新token
        '''
        secret = current_app.config.get("JWT_SCRET")
        expire = str(datetime.datetime.utcnow() + datetime.timedelta(hours=current_app.config.get("JWT_EXPIRY_HOURS")))
        payload = {"user_id":user_id,"refresh":False}
        token = getJWT(payload,expire,secret)
        refresh_token = None
        if refresh:
            expire = str(datetime.datetime.utcnow() + datetime.timedelta(hours=current_app.config.get("JWT_REFRESH_DAYS")))
            payload = {"user_id": user_id, "refresh": True}
            refresh_token = getJWT(payload,expire,secret)
        return token,refresh_token
    def post(self):
        """
        手机号登录
        :return:
        """
        parser = RequestParser()
        parser.add_argument("mobile",type=parsers.mobile,required=True,location="json")
        parser.add_argument("sms_code",type=parsers.regex(r"^\d{6}$"),required=True,location="json")
        args = parser.parse_args()
        mobile = args.mobile
        sms_code = args.sms_code
        print("验证码：",sms_code)
        #获取redis，和输入比较进行验证
        try:
            sms_code_v = current_app.redis_master.get("app:code:{}".format(mobile))
        except ConnectionError as e:
            current_app.logger.error(e)
            sms_code_v = current_app.redis_slave.get("app:code:{}".format(mobile))
        #获取后，清除密码
        try:
            current_app.redis_master.delete("app:code:{}".format(mobile))
        except ConnectionError as e:
            current_app.logger.error(e)
        #验证
        # 验证码失效
        if sms_code_v is None:
            return {"msg": "验证已过期，请重新发送"}, 400
        if sms_code_v.decode() != sms_code:
            return {"msg": "验证码输入错误，请重新输入"}, 401
        #验证用户是否存在，不存在则保存至数据库
        user = User.query.filter_by(mobile=mobile).first()
        if user:
            if user.status == User.STATUS.DISABLE:
                return {"msg":"用户不可用"},402
        else:
            idWork = current_app.idWorker.get_id()
            username = get_username(mobile)
            try:
                user = User(id=idWork, name=username, mobile=mobile, last_login=datetime.datetime.now())
                db.session.add(user)
                db.session.flush()
                profile = UserProfile(id=user.id, ctime=datetime.datetime.now(), utime=datetime.datetime.now(), company='无', career='无')
                db.session.add(profile)
                db.session.flush()
                db.session.commit()
            except Exception as e:
                current_app.logger.error(e)
                db.session.rollback()
                return {"msg":"数据库异常"},405
        #用户登陆成功，响应正确状态码同时，写入token认证
        token,refresh_token = self.get_token(user.id)
        print(token,refresh_token)
        return {"token":token,"refresh_token":refresh_token},201

class PasswdLogin(Resource):
    pass




