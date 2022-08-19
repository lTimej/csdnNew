from flask import current_app,g

from flask_restful import Resource,inputs
from flask_restful.reqparse import RequestParser

from sqlalchemy.exc import DatabaseError

from caches import commentCaches,dataStastics,articleCaches

from utils.loginPrivileges import loginPrivi
from utils import parsers

from . import constants

from models import  db
from models.news import Comment

class CommentListView(Resource):
    """
    获取评论列表
    """
    method_decorators = [loginPrivi]
    def get(self):
        parser = RequestParser()
        parser.add_argument("type",type=parsers.check_type,required=True,location="args")
        parser.add_argument("offset",type=inputs.positive,required=False,location="args")
        parser.add_argument("limit",type=inputs.int_range(constants.DEFAULT_COMMENT_PER_PAGE_MIN,constants.DEFAULT_COMMENT_PER_PAGE_MAX,"limit"),required=False,location="args")
        parser.add_argument("article_id",type=parsers.check_article_id,required=True,location="args")
        args = parser.parse_args()
        type = args.type
        article_id = args.article_id
        offset = args.offset
        limit = args.limit
        user_id = g.user_id
        total_num,end_id,last_id,comment_ids = commentCaches.ArticleCommentCaches(article_id).get_page(offset,limit)
        print("33333333334444444444555555555555",comment_ids)
        comment_list = commentCaches.CommentCaches.get_list(comment_ids)
        for comment_dict in comment_list:
            flag = commentCaches.CommentAttitudeCaches(comment_dict.get('comment_id')).exists(user_id)
            comment_dict["comment_is_like"] = flag
            total_res_num,end_res_id,last_res_id,comment_res_ids = commentCaches.ArticleResponseCommentCaches(comment_dict.get('comment_id')).get_page(offset,limit)
            comment_res_list = commentCaches.CommentCaches.get_list(comment_res_ids)
            if not comment_res_list:
                comment_dict['cComments'] = []

            for comment_res_dict in comment_res_list:
                if comment_res_dict.get("parent_comment_id") == comment_dict.get("comment_id"):
                    flag = commentCaches.CommentAttitudeCaches(comment_res_dict.get("comment_id")).exists(user_id)
                    comment_res_dict['comment_is_like'] = flag
                    comment_dict["cComments"] = comment_res_list
        total_num = dataStastics.ArticleCommentStastics.get(article_id)
        return {"total_num": total_num, "end_id": end_id, 'last_id': last_id, 'comments': comment_list}, 201

    def post(self):
        '''
        增加评论
        :return:
        '''
        parser = RequestParser()
        parser.add_argument("article_id",type=parsers.check_article_id,required=True,location="json")
        parser.add_argument("content",required=True,location="json")
        parser.add_argument("comment_id",type=inputs.positive,required=False,location="json")
        args = parser.parse_args()
        # 解析参数
        article_id = args.article_id
        content = args.content
        comment_parent_id = args.comment_id

        if not content:return {"msg":"content is not empty"},405

        is_allow = articleCaches.ArticleDetailCache(article_id).is_allow_comment()
        if not is_allow:return {"msg":"content is not allow"},405

        user_id = g.user_id
        if not comment_parent_id:#一级评论
            comment_id = current_app.idWorker.get_id()
            try:
                comment = Comment(id=comment_id,article_id=article_id,user_id=user_id,content=content,parent_id=None)
                db.session.add(comment)
                db.session.commit()
            except DatabaseError as e:
                current_app.logger.error(e)
                db.session.rollback()
                return {"msg":"database is not bad"},405
            dataStastics.ArticleCommentStastics.incr(article_id)
            comment_dict = commentCaches.CommentCaches(comment_id).save(comment)
            commentCaches.ArticleCommentCaches(article_id).update(comment)
        else:#二级评论
            flag = commentCaches.CommentCaches(comment_parent_id).exists()
            if not flag:return {"msg":"current comment is not exist"},405
            comment_id = current_app.idWorker.get_id()
            try:
                comment = Comment(id=comment_id,article_id=article_id,user_id=user_id,content=content,parent_id=comment_parent_id)
                db.session.add(comment)
                db.session.commit()
            except DatabaseError as e:
                db.session.rollback()
                current_app.logger.error(e)
                return {"msg":"database error"},405
            dataStastics.CommentResponseStastics.incr(comment_parent_id)
            dataStastics.ArticleCommentStastics.incr(article_id)
            commentCaches.CommentCaches(comment_id).save(comment)
            commentCaches.ArticleResponseCommentCaches(comment_parent_id).update(comment)
        return {'comment_id': comment.id, 'art_id': article_id, 'parent_comment_id': comment_parent_id}, 201








