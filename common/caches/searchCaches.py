import time

from flask import current_app
from sqlalchemy.exc import DatabaseError
from redis.exceptions import RedisError

from caches import contants

class SearchsCaches():
    """
    搜索缓存
    """
    def __init__(self,user_id):
        self.key = "article:search:{}".format(user_id)
        self.user_id = user_id

    def get(self):
        try:
            search = current_app.redis_master.zrevrange(self.key,0,-1)
        except RedisError as e:
            current_app.logger.error(e)
            search = current_app.rdis_slave.zrevrange(self.key,0,-1)
        if not search:return []
        return [keyword.decode() for keyword in search]

    def save(self,keyword):
        try:
            pl = current_app.redis_master.pipeline()
            pl.zadd(self.key,{keyword:time.time()})
            pl.zremrangebyrank(self.key, 0, -1 * (contants.ALLOW_UPDATE_SEARCH_CACHE_TTL_LIMIT + 1))
            pl.execute()
        except RedisError as e:
            current_app.logger.error(e)

    def delete(self):
        try:
            current_app.redis_master.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)


