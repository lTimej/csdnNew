from flask_restful import Resource
from flask_restful import inputs
from flask_restful.reqparse import RequestParser

from utils import  parsers

from . import constants


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
        page_num = args.page_num if args.page_nume else constants.DEFAULT_ARTICLE_PER_PAGE_MIN

