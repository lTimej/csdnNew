from flask_restful import Resource,inputs
from flask_restful.reqparse import RequestParser

from flask import current_app,g

from . import constants

from caches import articleCaches,searchCaches

from utils import parsers
from utils.loginPrivileges import loginPrivi

class AllSearchList(Resource):
    """
    获取所有所有
    """
    def get(self):
        parser = RequestParser()
        parser.add_argument("keyword",type=parsers.regex(r"^.{1,50}$"),required = True,location="args")
        parser.add_argument("page",type=parsers.check_page,required=False,location="args")
        parser.add_argument("page_num",type=inputs.int_range(constants.DEFAULT_SEARCH_PER_PAGE_MIN,constants.DEFAULT_SEARCH_PER_PAGE_MAX,"page_num"),required=False,location="args")
        args = parser.parse_args()
        keyword = args.keyword
        page = args.page
        page_num = args.page_num if args.page_num else constants.DEFAULT_SEARCH_PER_PAGE_MIN
        print(keyword)
        query = {
            "query":{
                "bool":{
                    "must":[
                        {
                            "match":{
                                "title": keyword
                            }
                        }
                    ],
                    "filter":{
                        "term":{
                            "status":1
                        }
                    }
                }
            },
            "from":(page-1)*page_num,
            "size":page_num,
            "_source":False
        }
        ret = current_app.es.search(index="articles",doc_type="article",body=query)
        total_num = ret.get("hits").get("total")
        article_ids = ret.get("hits").get("hits")
        articles = []
        for aid in article_ids:
            articles_dict = articleCaches.ArticleDetailCache(aid.get("_id")).get()
            if articles_dict:
                articles.append(articles_dict)
        if g.user_id and page == 1:
            searchCaches.SearchsCaches(g.user_id).save(keyword)
        return {"message":"ok","articles":articles,"total_num":total_num},201

class SearchHistory(Resource):
    '''
    搜索记录
    '''
    method_decorators = [loginPrivi]
    def get(self):
        history = searchCaches.SearchsCaches(g.user_id).get()
        return {"keywords": history}, 201

    def delete(self):
        searchCaches.SearchsCaches(g.user_id).delete()
        return {"message": "ok"}, 201

class SearchSuggest(Resource):
    '''
    搜索建议
    '''
    def suggestKeyword(self,keyword):
        query = {
            "suggest":{
                "mySuggest":{
                    "prefix":keyword,
                    "completion":{
                        "field":"suggest"
                    }
                }
            },
            "from":0,
            "size":20,
            "_source":False
        }
        ret = current_app.es.search(index="completions",body=query)
        option = ret.get("suggest").get("mySuggest")[0].get("options")
        return option
    def wordCurect(self,keyword):
        query = {
            "suggest":{
                "text":keyword,
                "mySuggestModify":{
                    "phrase":{
                        "field":"title",
                        "size":1
                    }
                }
            },
            "from":0,
            "size":20,
            "_source":False
        }
        ret = current_app.es.search(index='articles', doc_type='article', body=query)
        options = ret['suggest']['mySuggestModify'][0]['options']
        if options:
            return self.suggestKeyword(options[0].get("text"))
        return []
    def get(self):
        parser = RequestParser()
        parser.add_argument("keyword",type=parsers.regex(r"^.{1,50}$"),required=True,location="args")
        args = parser.parse_args()
        keyword = args.keyword
        options = self.suggestKeyword(keyword)
        if not options:
            options = self.wordCurect(keyword)
        suggest = []
        for op in options:
            sug = op.get("text")
            if sug not in suggest:
                suggest.append(sug)
        print(suggest)
        return {"message":"ok","searchs":suggest},201
