import json

from flask import current_app, g

from redis.exceptions import RedisError
from sqlalchemy.orm import load_only
from sqlalchemy.exc import DatabaseError

from caches.userCaches import UserBasicInfoCache
from caches import dataStastics
from caches import  contants

from models.news import CommentLiking

from models.news import Comment


class CommentCaches():
    """
    评论缓存,获取评论详细信息
    """
    def __init__(self,comment_id):
        self.key = "article:comment:{}".format(comment_id)
        self.comment_id = comment_id
        self.redis = current_app.redis_cluster

    def get(self):
        '''
        comment_id  ,   parent_comment_id  ,  ctime  ,  author_id  ,  is_top
        :return:字典，评论信息
        '''
        try:
            comments = self.redis.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            comments = None
        if comments is None:
            return None
        comments_dict = json.loads(comments)
        comments_dict = CommentCaches.add_field(comments_dict)
        return comments_dict

    @classmethod
    def add_field(cls,comment_dict):
        user = UserBasicInfoCache(comment_dict.get('author_id')).get()
        comment_dict['user_name'] = user.get("user_name")
        comment_dict['code_year'] = user.get('code_year')
        comment_dict['head_photo'] = user.get('head_photo')
        comment_dict['like_num'] = dataStastics.CommentLikeStastics.get(comment_dict.get('comment_id'))
        comment_dict['comment_response_num'] = dataStastics.CommentResponseStastics.get(
            comment_dict.get('comment_id'))
        return comment_dict

    def save(self,comment=None):
        if comment is None:
            try:
                comment = Comment.query.filter(Comment.id==self.comment_id,Comment.status==Comment.STATUS.APPROVED).first()
            except DatabaseError as e:
                current_app.logger.error(e)
                return {"msg":"database error"},405
        if comment is None:
            return None
        comment_dict = {
            "comment_id": str(comment.id),
            "parent_comment_id": str(comment.parent_id),
            "ctime": str(comment.ctime),
            "author_id": str(comment.user_id),
            "is_top": comment.is_top,
            "content": comment.content
        }
        print("hahahahhah555555555555555555555555555ahahahhaha",comment_dict)
        try:
            self.redis.setex(self.key,contants.ArticleCommentCacheTTL.get_TTL(),json.dumps(comment_dict))
        except RedisError as e:
            current_app.logger.error(e)
        return comment_dict

    @classmethod
    def get_list(cls,comments):
        '''
        评论列表详细信息
        :param comments: 列表套字典
        :return:
        '''
        query = []
        return_data = []
        cache = {}
        for comment_id in comments:
            comment = CommentCaches(comment_id).get()
            if comment:#comment是一个字典
                cache[comment_id] = comment
                return_data.append(comment)
            else:
                query.append(comment_id)
        if not query:#缓存都有，直接返回
            return return_data
        else:
            comment_query = Comment.query.filter(Comment.id.in_(query),Comment.status==Comment.STATUS.APPROVED).all()
            pl = current_app.redis_cluster.pipeline()
            for c in comment_query:
                caches = {
                    "comment_id": str(c.id),
                    "parent_comment_id": str(c.parent_id),
                    "ctime": str(c.ctime),
                    "author_id": c.user_id,
                    "is_top": c.is_top,
                    "content": c.content
                }
                pl.setex(CommentCaches(c.id).key,contants.ArticleCommentCacheTTL.get_TTL(),json.dumps(caches))
                caches = cls.add_field(caches)
                cache[c.id] = caches
            try:
                pl.execute()
            except RedisError as e:
                current_app.logger.error(e)
            return_data = []
            for c in comments:
                return_data.append(cache.get(c))
            return return_data
    def exists(self):
        res = self.get()
        if res:
            if res == b'-1':
                return False
            return True
        else:
            ret = self.save()
            if not ret:
                self.redis.setex(self.key,contants.ArticleCommentNotCacheTTL.get_TTL(),-1)
                return False
            return True
    def delete(self):
        try:
            self.redis.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

    def user_is_comment(self,user_id):
        comment = self.get()
        if not comment:return False
        if int(comment.get("author_id")) == int(user_id):return True
        return False


class ArticleCommentBaseCaches(object):
    """
    文章缓存，获取评论id
    """
    def __init__(self,id_val):
        self.id_val = id_val
        self.key = self.set_key()
        self.redis = current_app.redis_cluster

    def set_key(self):
        return ""

    def cal_count(self):
        return 0

    def db_query(self,query):
        return query

    def get_cache_ttl(self):
        return 0

    def get_page(self,offset,limit):
        '''
        :param offset: 时间戳
        :param limit: 限制几条评论
        :return: 总共评论数，最后一评论的时间戳，最新的一评论时间戳，评论id列表（limit）
        '''
        try:#从缓存中取
            pl = self.redis.pipeline()
            pl.zcard(self.key)#获取缓存中该key下的总个数
            pl.zrange(self.key,0,0,withscores=True)#返回最后一个{comment_id,timestamp}
            if offset:#在时间范围里取评论数
                #zrevrangebyscore(key,max(分数最大即score值),min（分数最小）,start（从第几个开始）,nums（拿几个）,withscores)
                pl.zrevrangebyscore(self.key,offset-1,0,0,limit,withscores=True)
            else:
                pl.zrevrange(self.key,0,limit,withscores=True)
            #end_id,res都是列表形式   [(comment_id,timestamp),(),......]
            total_num,end_id,res = pl.execute()
            print("----------------------????----------------",total_num,end_id,res)
        except DatabaseError as e:
            current_app.logger.error(e)
            total_num = 0
            end_id = None
            res = []
        if total_num > 0:#有缓存，直接返回
            end_id = end_id[0][1]#  timestamp
            last_id = int(res[-1][1]) if res else None#最后一个 timestamp
            return total_num,end_id,last_id,[int(cid[0]) for cid in res]

        total_num = self.cal_count()
        if total_num == 0:return 0,None,None,[]
        #从数据库取，根据指定类
        query = Comment.query.options(load_only(Comment.id,Comment.parent_id,Comment.ctime,Comment.is_top))
        query = self.db_query(query)
        #倒序
        comment_query = query.order_by(Comment.is_top.desc(),Comment.id.desc()).all()
        comment_ids = []
        cache = {}
        page_num = 0
        last_ids = None
        #构造返回数据，以及缓存数据
        for comment in comment_query:
            score = comment.ctime.timestamp()
            if comment.is_top:
                score += contants.COMMENTS_CACHE_MAX_SCORE
                #根据限制数构造返回评论数
            if ((not offset and score < offset) or offset is None) and page_num <= limit:
                comment_ids.append(comment.id)
                page_num += 1#自增1限制达到limit
                last_ids = comment
            cache[comment.id] = score
        end_id = comment_query[-1].ctime.timestamp()
        last_id = last_ids.ctime.timestamp() if last_ids else None
        total_num = len(comment_query)
        if cache:
            pl = self.redis.pipeline()
            pl.zadd(self.key,cache)
            pl.expire(self.key,contants.ArticleCommentCacheTTL.get_TTL())
            ret = pl.execute()
            if ret[0] and not ret[1]:
                self.redis.delete(self.key)
        return total_num,end_id,last_id,comment_ids

    def update(self,comment):
        try:
            # ttl = self.redis.ttl(self.key)
            # print(ttl,"====","222222222222222222000000000000009999999999999", {comment.id: comment.ctime.timestamp()})
            # if ttl > contants.ALLOW_UPDATE_ARTICLE_COMMENTS_CACHE_TTL_LIMIT:
            score = comment.ctime.timestamp()
            self.redis.zadd(self.key,{comment.id:score})
            print("3333333333333333333000000000000009999999999999",{comment.id:score})
        except RedisError as e:
            print(666666666666666666,"error")
            current_app.logger.error(e)

    def exists(self,comment):
        res = self.get_page(None,dataStastics.ArticleCommentStastics.get(self.id_val))
        for cid in res[3]:
            if CommentCaches(cid).user_is_comment(g.user_id):
                return True
        else: return False

class ArticleCommentCaches(ArticleCommentBaseCaches):

    def set_key(self):
        key = "article:comments:{}".format(self.id_val)
        return key

    def cal_count(self):
        return dataStastics.ArticleCommentStastics.get(self.id_val)

    def db_query(self,query):#第一级评论
        return query.filter(Comment.article_id==self.id_val,Comment.status==Comment.STATUS.APPROVED,Comment.parent_id==None)

    def get_cache_ttl(self):
        return contants.ArticleCommentCacheTTL.get_TTL()

class ArticleResponseCommentCaches(ArticleCommentBaseCaches):
    def set_key(self):
        self.key = "article:response:comments:{}".format(self.id_val)
        return self.key

    def cal_count(self):
        return dataStastics.CommentResponseStastics.get(self.id_val)

    def db_query(self,query):#二级评论
        return query.filter(Comment.parent_id==self.id_val,Comment.status==Comment.STATUS.APPROVED)

    def get_cache_ttl(self):
        return contants.ArticleCommentCacheTTL.get_TTL()

class CommentAttitudeCaches():
    """
    评论点赞情况
    """
    def __init__(self,comment_id):
        self.key = "comment:attitude:{}".format(comment_id)
        self.redis = current_app.redis_cluster
        self.comment_id = comment_id

    def get(self):
        try:
            comment = self.redis.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            comment = []

        if comment: return json.loads(comment)

        try:
            comment_obj = CommentLiking.query.options(load_only(CommentLiking.user_id)).filter(CommentLiking.comment_id == self.comment_id,CommentLiking.is_deleted==False).all()
        except DatabaseError as e:
            current_app.logger.error(e)
            return {"msg": "database error"},405
        if not comment_obj: return []
        comment_like = []
        for comm in comment_obj:
            comment_like.append(comm.user_id)

        try:
            self.redis.setex(self.key,contants.ArticleCommentCacheTTL.get_TTL(),json.dumps(comment_like))
        except RedisError as e:
            current_app.logger.error(e)

        return comment_like

    def exists(self,user_id):
        user_ids = self.get()
        return user_id in user_ids

    def delete(self):
        try:
            self.redis.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)











