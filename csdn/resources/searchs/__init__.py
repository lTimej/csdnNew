from flask import Blueprint
from flask_restful import Api
from . import  searchContents
from utils.outputJson import output_json

search_bp = Blueprint("search",__name__)
search_api = Api(search_bp,catch_all_404s=True)
search_api.representation("application/json")(output_json)

search_api.add_resource(searchContents.AllSearchList,"/v1/user/search",endpoint="search")
search_api.add_resource(searchContents.SearchHistory,"/v1/search/history",endpoint="sHistory")
#搜索建议
search_api.add_resource(searchContents.SearchSuggest,"/v1/search/suggest",endpoint="suggest")