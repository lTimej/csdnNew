from flask import current_app,g


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