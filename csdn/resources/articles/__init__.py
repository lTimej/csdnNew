from flask import Blueprint
from flask_restful import Api
from utils.outputJson import output_json
from . import channels,articles,articleStatus,comment

art_bp = Blueprint('article',__name__)

art_api = Api(art_bp,catch_all_404s=True)
art_api.representation('application/json')(output_json)

art_api.add_resource(channels.DefaultChannel,"/v1/default/channel",endpoint="defaultChannels")
art_api.add_resource(channels.AllChannel,'/v1/articles/channel',endpoint='allChannels')
art_api.add_resource(articles.ChannelArticle,'/v1/articles/<int(min=1):channel_id>',endpoint='article')
art_api.add_resource(articleStatus.ArticleStatus,'/v1/article/status',endpoint='status')
art_api.add_resource(articleStatus.ArticleCollection,'/v1/article/collection',endpoint='collection')
art_api.add_resource(articleStatus.ArticleAttitude,'/v1/article/likes',endpoint='likes')
art_api.add_resource(comment.CommentListView,'/v1/article/comment',endpoint='comment')




