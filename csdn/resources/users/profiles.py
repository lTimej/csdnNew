from flask_restful import Resource

from flask import g,current_app

from caches import userCaches

from utils.loginPrivileges import loginPrivi

class Profile(Resource):
    method_decorators = {
        "get":[loginPrivi]
    }
    """
    方法装饰器，判断是否登录，没有登录则不能进入视图
    """
    def get(self):
        user_id = g.user_id
        user_dict = userCaches.UserBasicInfoCache(user_id).get()
        print(user_dict,type(user_dict))
        user_other_dict = userCaches.UserOtherInfo(user_id).get()
        if not user_dict and not user_other_dict:
            return {"msg":"data not exist"},403
        user_dict.update(user_other_dict)
        return user_dict,201


