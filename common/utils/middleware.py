from flask import current_app,g,request
from utils.get_token import verifyToken


def authVerify():
    """
    请求前判断是否登录，通过token查看
    :return:
    """
    token = request.headers.get("Authorization")
    g.user_id = None
    g.refresh = None
    if token and token.startswith("Bearer "):
        token = token[7:]
        payload = verifyToken(token)
        if payload:
            g.user_id = payload.get("user_id")
            g.refresh = payload.get("refresh")



