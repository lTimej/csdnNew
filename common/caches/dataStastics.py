from flask import current_app
from sqlalchemy import func

from redis.exceptions import RedisError

from models import db
from models.user import User,Relation,Visitors

class StasticsBase(object):
    '''
    静态值统计：用户关注量、粉丝数、文章发表数.....
    '''
    key = ""
    @classmethod
    def get(cls,user_id):
        '''
        获取用户相关数量
        :param user_id:某用户
        :return: count
        '''
        try:#先从主中查
            count = current_app.redis_master.zscore(cls.key,user_id)
        except RedisError as e:#主挂了，在从从中查
            current_app.logger.error(e)
            count = current_app.redis_slave.zscore(cls.key,user_id)

        if count:
            return int(count)
        else:
            return 0
    @classmethod
    def incr(cls,user_id,incr_num=1):
        '''
        用户相关数量自增
        :param user_id:某用户
        :param incr_num: 增加个数
        :return:无
        '''
        try:
            current_app.redis_master.zincrby(cls.key,user_id,incr_num)
        except RedisError as e:
            current_app.logger.error(e)
            raise e

    @classmethod
    def reset(cls,db_querys):
        '''
        定时刷新缓存中相关统计数量
        :param db_querys: 相关query操作集合
       :return:
        '''
        counts = []
        for user_id,count in db_querys:
            counts.append(count)
            counts.append(user_id)
        if not counts:
            return
        pl = current_app.redis_master.pipeline()
        pl.zadd(cls.key, *counts)
        pl.execute()


#用户关注数
class UserFocusStastics(StasticsBase):
    '''
    查询用户所关注的人数
    '''
    key = "user:focus"
    @staticmethod
    def db_querys():
        '''
        获取所有用户关注的人数
        :return: querys
        '''
        return db.session.query(Relation.user_id,func.count(Relation.target_user_id)).filter(Relation.relation == Relation.RELATION.FOLLOW).group_by(Relation.user_id).all()

#用户粉丝数
class UserFollwingStastics(StasticsBase):
    """
    查询用户的粉丝数
    """
    key = "user:following"
    @staticmethod
    def db_querys():
        '''
        获取用户的粉丝数
        :return: querys
        '''
        return db.session.query(Relation.target_user_id,func.count(Relation.user_id)).filter(Relation.relation == Relation.RELATION.FOLLOW).group_by(Relation.target_user_id).all()

#用户被访问数
class UserVisitedStastics(StasticsBase):
    """
    查询用户被访问的次数
    """
    key = "user:visited"
    @staticmethod
    def db_querys():
        return db.session.query(Visitors.user_id,Visitors.count).all()

