from flask import current_app

from redis.exceptions import RedisError
from sqlalchemy.orm import load_only
from sqlalchemy.exc import DatabaseError

from models.news import Article

from caches import contants

class ChannelArticleCache():
    """
    每个频道的文章id列表
    """
    def __init__(self,channel_id):
        self.key = "article:{}".format(channel_id)
        self.redis = current_app.redis_cluster
        self.channel_id = channel_id

    def get(self,page,page_num):
        try:
            pl = self.redis.pipeline()
            #获取文章个数
            n = pl.zcard(self.key)
            #获取文章区间
            pl.zrevrange(self.key,(page-1)*page_num,page*page_num)
            total_num,articles = pl.execute()
        except RedisError as e:
            current_app.logger.error(e)
            total_num = 0
            articles = []
        if total_num:
            return total_num,articles

        return self.save(page,page_num)

    def save(self,page,page_num):
        try:
            articles = Article.query.options(load_only(Article.id,Article.ctime)).filter(Article.channel_id==self.channel_id,Article.status==Article.STATUS.APPROVED).all()
        except DatabaseError as e:
            current_app.logger.error(e)
            raise e
        if not articles:return 0,[]

        return_article = []
        cache = []
        for article in articles:
            return_article.append(article.id)
            cache.append(article.ctime.timestamp)
            cache.append(article.id)
        try:
            pl = self.redis.pipeline()
            pl.zadd(self.key,*cache)
            pl.expire(self.key,contants.ArticleChannelCacheTTL.get_TTL())
            res = pl.execute()
            if res[0] and not res[1]:
                self.redis.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)
        total_num = len(return_article)
        return total_num,return_article[(page-1)*page_num:page*page_num]

class ArticleDetailCache():
    """
    文章详情
    """
    def __init__(self,article_id):
        self.key = "article:content"
        self.redis = current_app.redis_cluster
        self.article_id = article_id

    def get(self):
        pass



