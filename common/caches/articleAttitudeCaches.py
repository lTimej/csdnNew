import json

from flask import current_app
from sqlalchemy.orm import load_only
from sqlalchemy.exc import DatabaseError

from models.news import Attitude

from redis.exceptions import RedisError

from caches import contants

class UserArticlesAttitudeCache():
    """
    用户对文章态度缓存，点赞还是不点赞
    """
    def __init__(self,user_id):
        self.key = "article:user:attitude:{}".format(user_id)
        self.user_id = user_id
        self.redis = current_app.redis_cluster

    def get(self):
        try:
            attitudes = self.redis.hgetall(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            attitudes = None

        if attitudes:
            if attitudes == b'-1':return {}
            return {int(article_id):int(eval(attitude)) for article_id,attitude in attitudes.items()}
        return self.save()

    def save(self):
        try:
            attitudes = Attitude.query.options(load_only(Attitude.article_id,Attitude.attitude)).filter(Attitude.user_id==self.user_id,Attitude.attitude==Attitude.ATTITUDE.LIKING).all()
        except DatabaseError as e:
            current_app.logger.error(e)
            return {"msg":"database error"},405
        if not attitudes:return {}
        caches = {}
        for attitude in attitudes:
            caches[attitude.article_id] = attitude.attitude
        try:
            pl = self.redis.pipeline()
            if caches:
                pl.hmset(self.key,caches)
                pl.expire(self.key,contants.ArticleAttitudeCacheTTL.get_TTL())
            else:
                pl.hmset(self.key,{-1,-1})
                pl.expire(self.key,contants.ArticleAttitudeNotExistCacheTTL.get_TTL())
            res = pl.execute()
            if res[0] and not res[1]:
                self.redis.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

        return caches
    def exists(self,article_id):
        attitude = self.get()
        flag = attitude.get(article_id,False)
        return True if flag == 1 else False
    def delete(self):
        try:
            self.redis.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

class ArticlesAttitudeCache():
    """
    文章点赞缓存
    """
    def __init__(self,article_id):
        self.key = "article:attitude:{}".format(article_id)
        self.redis = current_app.redis_cluster
        self.article_id = article_id

    def get(self):
        try:
            attitude = self.redis.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            attitude = None

        if attitude:
            return json.loads(attitude)
        return self.save()

    def save(self):
        try:
            attitude = Attitude.query.options(load_only(Attitude.user_id)).filter(Attitude.article_id==self.article_id,Attitude.attitude==Attitude.ATTITUDE.LIKING).order_by(Attitude.utime.desc()).all()
        except DatabaseError as e:
            current_app.logger.error(e)
            return {"msg":"database error"},405

        if not attitude:return []
        attitude_list = []
        for a in attitude:
            attitude_list.append(a.user_id)
        try:
            self.redis.setex(self.key,contants.ArticleAttitudeCacheTTL.get_TTL(),json.dumps(attitude_list))
        except RedisError as e:
            current_app.logger.error(e)
        return attitude_list


    def delete(self):
        try:
            self.redis.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)
