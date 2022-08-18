from flask_restful import Resource,inputs
from flask_restful.reqparse import RequestParser

from flask import g,current_app

from caches import articleAttitudeCaches,articleCollectionCaches,dataStastics,focusFansCaches,articleCaches,userCaches
from utils import parsers
from utils.loginPrivileges import loginPrivi

from . import  constants
from models.news import Collection,Attitude
from models import db

from sqlalchemy.exc import DatabaseError

class ArticleStatus(Resource):
    """
    获取文章收藏、点赞、like数
    """
    def get(self):

        parser = RequestParser()
        parser.add_argument('aid',type=parsers.check_article_id,required=True,location="args")
        parser.add_argument('uid',type=parsers.check_user_id,required=True,location="args")
        args = parser.parse_args()
        article_id = args.aid
        target_user_id = args.uid
        user_id = g.user_id
        if user_id:
            is_focus = focusFansCaches.UserFocusCaches(user_id).is_focus(target_user_id)
            is_like = articleAttitudeCaches.UserArticlesAttitudeCache(user_id).exists(article_id)
            is_collection = articleCollectionCaches.ArticlesCollectionCache(user_id).exists(article_id)
        else:
            """
            没有登录，不能收藏，先登录
            """
            is_focus = False
            is_like = False
            is_collection = False

        collection_num = dataStastics.ArticleCollectionStastics.get(article_id)
        like_num = dataStastics.ArticleLikeStastics.get(article_id)
        read_num = dataStastics.ArticleReadStastics.get(article_id)

        context = {
            "isfocus": is_focus,
            "iscollection": is_collection,
            "islike": is_like,
            "collection_num": collection_num,
            "like_num": like_num,
            "read_num": read_num,
            "aid": article_id
        }
        return context,201

class ArticleCollection(Resource):
    '''
    文章收藏、取消收藏
    '''
    method_decorators = [loginPrivi]
    def get(self):
        parser = RequestParser()
        parser.add_argument("page",type=parsers.check_page,required = False,location="args")
        parser.add_argument("page_num",type=inputs.int_range(constants.DEFAULT_ARTICLE_PER_PAGE_MIN,constants.DEFAULT_ARTICLE_PER_PAGE_MAX,"page_num"),required=False,location="args")
        args = parser.parse_args()
        page = args.page
        page_num = args.page_num if args.page_num else constants.DEFAULT_ARTICLE_PER_PAGE_MIN
        user_id = g.user_id
        total_num,collections = articleCollectionCaches.ArticlesCollectionCache(user_id).get(page,page_num)

        articles = []
        for article_id in collections:
            articles.append(articleCaches.ArticleDetailCache(article_id).get())
        return {"page": page, "page_num": page_num, "total_num": total_num, "collections": articles}, 201

    def post(self):
        parser = RequestParser()
        parser.add_argument("aid",type=parsers.check_article_id,required=True,location="json")
        args = parser.parse_args()
        article_id = args.aid

        user_id = g.user_id
        ret = 1
        try:
            article_collection = Collection(article_id=article_id,user_id=user_id,is_deleted=False)
            db.session.add(article_collection)
            db.session.commit()
        except DatabaseError as e:
            current_app.logger.error(e)
            db.session.rollback()
            ret = Collection.query.filter(Collection.article_id==article_id,Collection.user_id==user_id,Collection.is_deleted==True).update({"is_deleted":False})
            db.session.commit()
        if ret > 0:
            articleCollectionCaches.ArticlesCollectionCache(user_id).delete()
            dataStastics.ArticleCollectionStastics.incr(article_id)
            dataStastics.UserArticleCollectionStastics.incr(user_id)

        return {"aid":article_id},201

    def delete(self):
        parser = RequestParser()
        parser.add_argument("aid",type=parsers.check_article_id,required=True,location="json")
        args = parser.parse_args()

        article_id = args.aid
        user_id = g.user_id
        ret = 1
        try:
            ret = Collection.query.filter(Collection.article_id==article_id,Collection.user_id==user_id,Collection.is_deleted==False).update({"is_deleted":True})
            db.session.commit()
        except DatabaseError as e:
            current_app.logger.error(e)
            return {"message": "collection user is not exist"}, 401
        if ret > 0:
            articleCollectionCaches.ArticlesCollectionCache(user_id).delete()
            dataStastics.ArticleCollectionStastics.incr(article_id,-1)
            dataStastics.UserArticleCollectionStastics.incr(user_id,-1)
        return {"message": "ok"}, 201

class ArticleAttitude(Resource):
    """
    文章点赞情况
    """
    method_decorators = [loginPrivi]

    def get(self):
        parser = RequestParser()
        parser.add_argument('aid',type=parsers.check_article_id,required=True,location="args")
        args = parser.parse_args()
        article_id = args.aid
        users = articleAttitudeCaches.ArticlesAttitudeCache(article_id).get()
        user_list = []
        for user in users:
            user_dict = userCaches.UserBasicInfoCache(user).get()
            user_list.append({
                'head_photo': user_dict.get('head_photo'),
                'aid': article_id
            })
        return {'users_info': user_list}, 201

    def post(self):
        parser = RequestParser()
        parser.add_argument("aid",type=parsers.check_article_id,required=True,location="json")

        args = parser.parse_args()
        article_id = args.aid
        user_id = g.user_id
        ret = 1
        try:
            attitude = Attitude(user_id=user_id,article_id=article_id,attitude=Attitude.ATTITUDE.LIKING)
            db.session.add(attitude)
            db.session.commit()
        except DatabaseError as e:
            current_app.logger.error(e)
            db.session.rollback()
            ret = Attitude.query.filter(Attitude.user_id==user_id,Attitude.article_id==article_id,Attitude.attitude==Attitude.ATTITUDE.DISLIKE).update({"attitude":Attitude.ATTITUDE.LIKING})
            db.session.commit()
        if ret > 0:
            articleAttitudeCaches.UserArticlesAttitudeCache(user_id).delete()
            articleAttitudeCaches.ArticlesAttitudeCache(article_id).delete()
            dataStastics.ArticleLikeStastics.incr(article_id)
            dataStastics.UserArticleLikeStastics.incr(user_id)
        return {"aid": article_id}, 201

    def delete(self):
        parser = RequestParser()
        parser.add_argument("aid", type=parsers.check_article_id, required=True, location="json")

        args = parser.parse_args()
        article_id = args.aid
        user_id = g.user_id
        ret = 1
        try:
            ret = Attitude.query.filter(Attitude.user_id==user_id,Attitude.article_id==article_id,Attitude.attitude==Attitude.ATTITUDE.LIKING).update({"attitude":Attitude.ATTITUDE.DISLIKE})
            db.session.commit()
        except DatabaseError as e:
            current_app.logger.error(e)
            return {"message": "attitude user is not exist"}, 401
        if ret > 0:
            articleAttitudeCaches.UserArticlesAttitudeCache(user_id).delete()
            articleAttitudeCaches.ArticlesAttitudeCache(article_id).delete()
            dataStastics.ArticleLikeStastics.incr(article_id,-1)
            dataStastics.UserArticleLikeStastics.incr(user_id,-1)
        return {"message": "success"}, 201




