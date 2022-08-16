from flask import current_app,g
from caches.userCaches import UserStatusCache


def loginPrivi(methods):
    '''
    用户是否登录装饰器
    :param methods:被判断的视图是否登录
    :return:
    '''
    def wrapper(*args,**kwargs):
        user_id = g.user_id
        refresh = g.refresh
        if user_id and not refresh:
            return methods(*args,**kwargs)
        else:
            return {"msg":"user not login"},401
    return wrapper

def is_login(methods):
    '''
    判断用户是否登录，登录了并验证用户状态
    :param methods:
    :return:
    '''
    def wrapper(*args,**kwargs):
        user_id = g.user_id
        if user_id:
            status = UserStatusCache(user_id).get()
            if not status:
                return {'message': 'User denied'}, 403
        return methods(*args,** kwargs)
    return wrapper