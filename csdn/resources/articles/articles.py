from flask_restful import Resource
from flask_restful import inputs
from flask_restful.reqparse import RequestParser

from utils import  parsers

from . import constants

from caches import articleCaches

class ChannelArticle(Resource):
    """
    分页获取指定频道的文章列表
    """
    def get(self,channel_id):
        """
        page,page_nue
        :param channel_id: 频道id
        :return:
        """
        parser = RequestParser()
        parser.add_argument("page",type=parsers.check_page,required=False,location="args")
        parser.add_argument("page_num",type=inputs.int_range(constants.DEFAULT_ARTICLE_PER_PAGE_MIN,constants.DEFAULT_ARTICLE_PER_PAGE_MAX,"page_num"),required=False,location="args")
        args = parser.parse_args()
        page = args.page
        page_num = args.page_num if args.page_num else constants.DEFAULT_ARTICLE_PER_PAGE_MIN
        # articleCaches.ChannelArticleCache(channel_id).delete()
        total_num,article_ids = articleCaches.ChannelArticleCache(channel_id).get(page,page_num)

        article_list = []
        for article_id in article_ids:
            # articleCaches.ArticleDetailCache(article_id).delete()
            article_dict = articleCaches.ArticleDetailCache(article_id).get()
            if article_dict:
                article_list.append(article_dict)
        return {"total_num": total_num, "page": page, "page_num": page_num, "articles": article_list}, 201


