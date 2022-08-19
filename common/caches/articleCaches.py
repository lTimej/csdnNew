import json

from flask import current_app

from redis.exceptions import RedisError
from sqlalchemy.orm import load_only,contains_eager
from sqlalchemy.exc import DatabaseError

from models.news import Article,ArticleContent

from caches import contants,userCaches,dataStastics

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
        cache = {}
        #redis版本>3.0.2时，redis.zadd(key,mapping)  mapping是字典类型
        for article in articles:
            return_article.append(article.id)
            cache[article.id] = article.ctime.timestamp()
            # cache.append(article.ctime.timestamp())
            # cache.append(article.id)
        try:
            pl = self.redis.pipeline()
            pl.zadd(self.key,cache)
            pl.expire(self.key,contants.ArticleChannelCacheTTL.get_TTL())
            res = pl.execute()
            if res[0] and not res[1]:
                self.redis.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)
        total_num = len(return_article)
        return total_num,return_article[(page-1)*page_num:page*page_num]

    def delete(self):
        try:
            self.redis.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

class ArticleDetailCache():
    """
    文章详情
        'title'、'user_id'、'create_time'、'art_id'、'channel_id'、'content'、 'allow_comment'
        一篇文章对应相应内容，redis存储格式，key:value
    """
    def __init__(self,article_id):
        self.key = "article:content:{}".format(article_id)
        self.redis = current_app.redis_cluster
        self.article_id = article_id

    def get(self):
        '''
        获取文章详情
        :return: dict
        '''
        articles = None
        try:
            articles = self.redis.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
        article_dict = {}
        if articles:
            if articles == b'-1':
                return {}
            article_dict = json.loads(articles)
        else:
            article_dict = self.save()
        article_dict = self.add_field(article_dict)
        return article_dict

    def add_field(self,article_dict):
        '''
        文章点赞，关注，评论数
        :return:
        '''
        article_dict["read_num"] = dataStastics.ArticleReadStastics.get(self.article_id)
        article_dict["comment_num"] = dataStastics.ArticleCommentStastics.get(self.article_id)
        article_dict["like_num"] = dataStastics.ArticleLikeStastics.get(self.article_id)
        article_dict["collection_num"] = dataStastics.ArticleCollectionStastics.get(self.article_id)
        return article_dict

    def save(self):
        try:
            articles = Article.query.join(Article.content).options(load_only(Article.title,Article.user_id,Article.ctime,Article.channel_id,Article.allow_comment,Article.id),contains_eager(Article.content).load_only(ArticleContent.content)).filter(Article.id==self.article_id,Article.status==Article.STATUS.APPROVED).first()
        except DatabaseError as e:
            current_app.logger.error(e)
            raise e
        if not articles:
            try:
                self.redis.setex(self.key,contants.DataBaseNotData.get_TTL(),-1)
            except RedisError as e:
                current_app.logger.error(e)
            return {}
        article_dict = {
            'title':articles.title,
            'user_id':str(articles.user_id),
            'create_time':str(articles.ctime)[:str(articles.ctime).find(' ')],
            'art_id':articles.id,
            'channel_id':articles.channel_id,
            'content': articles.content.content,
            'allow_comment':articles.allow_comment
        }
        user_dict = userCaches.UserBasicInfoCache(article_dict.get("user_id")).get()
        article_dict["user_name"] = user_dict.get("user_name")
        article_dict["head_photo"] = user_dict.get("head_photo")
        article_dict['career'] = user_dict.get("career")
        article_dict["code_year"] = user_dict.get("code_year")
        try:
            self.redis.setex(self.key,contants.ArticleDetailCacheTTL.get_TTL(),json.dumps(article_dict))
        except RedisError as e:
            current_app.logger.error(e)
        return article_dict

    def delete(self):
        try:
            self.redis.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

    def exists(self):
        try:
            article = self.redis.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            article = None
        if article:
            if article == b'-1':
                return False
            else:
                return True
        else:
            articles = self.save()
            if articles:
                return True
            return False

    def is_allow_comment(self):
        res = self.get()
        if not res:
            res = self.save()
        if res.get("allow_comment"):return True
        return False






