import time
from flask import g,current_app
from flask_restful import Resource,inputs
from flask_restful.reqparse import RequestParser
from sqlalchemy.exc import DatabaseError

from models import db
from models.user import Relation
from utils import parsers
from . import constants
from utils.loginPrivileges import loginPrivi

from caches import focusFansCaches,userCaches,dataStastics

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
        # focusFansCaches.UserFocusCaches(user_id).delete()
        # focusFansCaches.UserFocusCaches(user_id).delete()
        focus_ids = focusFansCaches.UserFocusCaches(user_id).get()
        fans_ids = focusFansCaches.UserFansCaches(user_id).get()
        focus_list = []
        total_num = len(focus_ids)
        focus_id = focus_ids[(page-1)*page_num:page*page_num]
        for id in focus_id:
            userInfo = userCaches.UserBasicInfoCache(id).get()
            if userInfo:
                focus_list.append({
                    'user_id': str(id),
                    'flag': "已关注",
                    'user_name': userInfo.get('user_name'),
                    'head_photo': userInfo.get('head_photo'),
                    'introduction': userInfo.get('introduction'),
                    'mutual_focus': str(id) in fans_ids
                })
        return {"focus": focus_list, "total_num": total_num, "page": page, "page_num": page_num}, 201

    def post(self):
        """
        点击关注
        :return:
        """
        parser = RequestParser()
        parser.add_argument("target",type=parsers.check_user_id,required=True,location="json")
        args = parser.parse_args()
        target_user_id = args.target
        user_id = g.user_id
        res = 1
        if target_user_id == user_id:
            return {"msg":"don't focus yourself"},405
        try:
            relation = Relation(user_id=user_id,target_user_id=target_user_id,relation=Relation.RELATION.FOLLOW)
            db.session.add(relation)
            db.session.commit()
        except DatabaseError as e:
            current_app.logger.error(e)
            db.session.rollback()
            res = Relation.query.filter(Relation.user_id==user_id,Relation.target_user_id==target_user_id,Relation.relation != Relation.RELATION.FOLLOW).update({"relation":Relation.RELATION.FOLLOW})
            db.session.commit()
        if res > 0:
            """增加或者修改成功，存入缓存"""
            timestamp = time.time()
            focusFansCaches.UserFocusCaches(user_id).update(target_user_id,timestamp)
            focusFansCaches.UserFansCaches(target_user_id).update(user_id,timestamp)
            dataStastics.UserFocusStastics.incr(user_id)
            dataStastics.UserFollwingStastics.incr(target_user_id)
        return {"target_id": str(target_user_id)}, 201

    def delete(self):
        """
        取消关注
        :param user_id:
        :return:
        """
        parser = RequestParser()
        parser.add_argument("target",type=parsers.check_user_id,required=True,location="json")
        args = parser.parse_args()
        target_user_id = args.target
        user_id = g.user_id
        ret = 1
        try:
            ret = Relation.query.filter(Relation.user_id==user_id,Relation.target_user_id==target_user_id,Relation.relation==Relation.RELATION.FOLLOW).update({"relation":Relation.RELATION.DELETE})
            db.session.commit()
        except DatabaseError as e:
            current_app.logger.error(e)
            db.session.rollback()
            return {"message": "focused user is not exist"}, 401
        if ret > 0:
            timestamp = time.time()
            focusFansCaches.UserFocusCaches(user_id).update(target_user_id, timestamp,-1)
            focusFansCaches.UserFansCaches(target_user_id).update(user_id, timestamp,-1)
            dataStastics.UserFocusStastics.incr(user_id,-1)
            dataStastics.UserFollwingStastics.incr(target_user_id,-1)
        return {"message": "success"}, 201

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