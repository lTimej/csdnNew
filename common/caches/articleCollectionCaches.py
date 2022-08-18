from flask import current_app

from sqlalchemy.orm import load_only,contains_eager
from sqlalchemy.exc import DatabaseError

from redis.exceptions import RedisError

from models.news import Collection

from caches.dataStastics import ArticleCollectionStastics
from caches import contants


class ArticlesCollectionCache():
    """
    文章收藏列表缓存
    """
    def __init__(self,user_id):
        self.key = "article_collection:{}".format(user_id)
        self.user_id = user_id
        self.redis = current_app.redis_cluster

    def get(self,page,page_num):
        try:
            pl = self.redis.pipeline()
            pl.zcard(self.key)
            pl.zrevrange(self.key,(page-1)*page_num,page*page_num)
            total_num,collections = pl.execute()
        except RedisError as e:
            current_app.logger.error(e)
            total_num = 0
            collections = None
        if total_num > 0:
            return total_num,[article_id for article_id in collections]
        total_num,collections = self.save()
        collections = collections[(page-1)*page_num:page*page_num]
        return total_num,collections

    def save(self):
        total_num = ArticleCollectionStastics.get(self.user_id)
        if total_num == 0:
            return 0,[]
        try:
            collections = Collection.query.options(load_only(Collection.article_id,Collection.ctime)).filter(Collection.user_id==self.user_id,Collection.is_deleted==False).order_by(Collection.ctime.desc()).all()
        except DatabaseError as e:
            current_app.logger.error(e)
            return {"msg":"database bad"},405
        if not collections:
            return 0,[]
        return_collection = []
        caches = {}
        for collection in collections:
            return_collection.append(collection.article_id)
            caches[collection.article_id] = collection.ctime
        if caches:
            try:
                pl = self.redis.pipeline()
                pl.zadd(self.key,caches)
                pl.expire(self.key,contants.ArticleCollectionCacheTTL.get_TTL())
                res = pl.execute()
                if res[0] and not res[1]:
                    self.redis.delete(self.key)
            except RedisError as e:
                current_app.logger.error(e)

        total_num = len(return_collection)
        return total_num,return_collection

    def delete(self):
        try:
            self.redis.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

    def exists(self,article_id):
        total_num,article_ids =  self.get(0,-1)
        return article_id in article_ids




