import jwt
import datetime
from flask import current_app

def getJWT(payload: dict,expire,secret=None):
    """
    生成token
    :param payload: 载荷，包含用户名
    :expire: token过期时间
    :param secret: 密钥
    :return:
    """
    # payload["expire"] = expire
    _payload = {"expire":expire}
    payload.update(_payload)
    if not secret:
        secret = current_app.config.get("JWT_SECRET")
    token = jwt.encode(payload,secret,algorithm="HS256")
    return token

def verifyToken(token,secret=None):
    if not secret:
        secret = current_app.config.get("JWT_SECRET")
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        payload = None
    return payload

def getToken(user_id,refresh=True):
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