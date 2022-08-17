from flask import g
from flask_restful import Resource,inputs
from flask_restful.reqparse import RequestParser

from utils import parsers
from . import constants
from utils.loginPrivileges import loginPrivi

from caches import focusFansCaches,userCaches

class FocusUser(Resource):
    """
    获取关注用户列表、关注用户、取消关注
    """
    method_decorators = [loginPrivi]
    def get(self):
        parser = RequestParser()
        parser.add_argument("page",type=parsers.check_page,required=False,location="args")
        parser.add_argument("page_num",type=inputs.int_range(constants.DEFAULT_USER_FOLLOWINGS_PER_PAGE_MIN,constants.DEFAULT_USER_FOLLOWINGS_PER_PAGE_MAX,"page_num"),required=False,location="args")
        args = parser.parse_args()

        page = args.page
        page_num = args.page_num if args.page_num else constants.DEFAULT_USER_FOLLOWINGS_PER_PAGE_MIN
        user_id = g.user_id
        focus_ids = focusFansCaches.UserFocusCaches(user_id).get()
        fans_ids = focusFansCaches.UserFansCaches(user_id).get()
        focus_list = []
        total_num = len(focus_ids)
        focus_id = focus_ids[(page-1)*page_num:page*page_num]
        for id in focus_id:
            userInfo = userCaches.UserBasicInfoCache(id).get()
            focus_list.append({
                'user_id': str(id),
                'flag': "已关注",
                'user_name': userInfo.get('user_name'),
                'head_photo': userInfo.get('head_photo'),
                'introduction': userInfo.get('introduction'),
                'mutual_focus': str(id) in fans_ids
            })
        return {"focus": focus_list, "total_num": total_num, "page": page, "page_num": page_num}, 201


    def post(self,user_id):
        pass

    def delete(self,user_id):
        pass

class FansUser(Resource):
    """
    用户粉丝
    """
    def get(self):
        parser = RequestParser()
        parser.add_argument("page",type=parsers.check_page,required=False,location="args")
        parser.add_argument("page_num",type=inputs.int_range(constants.DEFAULT_USER_FOLLOWINGS_PER_PAGE_MIN,constants.DEFAULT_USER_FOLLOWINGS_PER_PAGE_MAX,"page_num"),required=False,location="args")
        args = parser.parse_args()
        page = args.page
        page_num = args.page_num if args.page_num else constants.DEFAULT_USER_FOLLOWINGS_PER_PAGE_MIN
        user_id = g.user_id
        fans_ids = focusFansCaches.UserFansCaches(user_id).get()
        focus_ids = focusFansCaches.UserFocusCaches(user_id).get()
        fans_id = fans_ids[(page-1)*page_num:page*page_num]
        fans_list = []
        total_num = len(fans_ids)
        for id in fans_id:
            userInfo = userCaches.UserBasicInfoCache(id).get()
            fans_list.append({
                'user_id':str(id),
                'flag':"回关",
                'user_name':userInfo.get('user_name'),
                'head_photo':userInfo.get('head_photo'),
                'introduction':userInfo.get('introduction'),
                "mutual_focus": int(id) in focus_ids#判断是否互相关注
            })
        return {"fans":fans_list,"total_num":total_num,"page":page,"page_num":page_num},201