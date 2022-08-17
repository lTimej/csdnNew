from flask import current_app

from redis.exceptions import RedisError
from sqlalchemy.orm import load_only
from sqlalchemy.exc import DatabaseError

from models.user import Relation

from caches import contants

class UserFocusCaches():
    """
    用户关注缓存
    有序集合
    key  target_id create_time
    """
    def __init__(self,user_id):
        self.key = "user:focus:{}".format(user_id)
        self.user_id = user_id
        self.redis = current_app.redis_cluster

    def get(self):
        try:
            focus = self.redis.zrevrange(self.key,0,-1)
        except RedisError as e:
            current_app.logger.error(e)
            focus = None
        if focus:
            return [str(target_id) for target_id in focus]
        focus = self.save()
        return focus

    def save(self):
        try:
            relations = Relation.query.options(load_only(Relation.target_user_id,Relation.ctime)).filter(Relation.user_id==self.user_id,Relation.relation==Relation.RELATION.FOLLOW).order_by(Relation.ctime.desc()).all()
        except DatabaseError as e:
            current_app.logger.error(e)
            raise e
        if not relations : return []
        return_target_user_ids = []
        caches = {}
        for relation in relations:
            return_target_user_ids.append(str(relation.target_user_id))
            caches[relation.target_user_id] = relation.ctime.timestamp()
        try:
            pl = self.redis.pipeline()
            pl.zadd(self.key,caches)
            pl.expire(self.key,contants.UserFocusCacheTTL.get_TTL())
            res = pl.execute()
            if res[0] and not res[1]:
                self.redis.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)
        return return_target_user_ids

class UserFansCaches():
    """
    用户粉丝列表缓存
    缓存格式：有序集合
    key: mapping
    """
    def __init__(self,user_id):
        self.key = "user:fans:{}".format(user_id)
        self.user_id = user_id
        self.redis = current_app.redis_cluster

    def get(self):
        try:
            fans = self.redis.zrevrange(self.key,0,-1)
        except RedisError as e:
            current_app.logger.error(e)
            fans = None
        if fans:
            return [str(user_id) for user_id in fans]
        return self.save()

    def save(self):
        try:
            relations = Relation.query.options(load_only(Relation.user_id,Relation.ctime)).filter(Relation.target_user_id==self.user_id,Relation.relation==Relation.RELATION.FOLLOW).order_by(Relation.ctime.desc()).all()

        except DatabaseError as e:
            current_app.logger.error(e)
            raise e
        if not relations:return []
        return_list = []
        caches = {}
        for relation in relations:
            return_list.append(str(relation.user_id))
            caches[relation.user_id] = relation.ctime.timestamp()
        try:
            pl = self.redis.pipeline()
            pl.zadd(self.key,caches)
            pl.expire(self.key,contants.UserFansCacheTTL.get_TTL())
            res = pl.execute()
            if res[0] and not res[1]:
                self.redis.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

        return return_list
