import jwt
from flask import current_app
from flask import g


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
    print(token,type(token))
    return token

def verifyToken(token,secret):
    if not secret:
        secret = current_app.config.get("JWT_SECRET")
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        payload = None
    return payload

