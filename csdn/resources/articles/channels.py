from flask_restful import Resource
from flask import g

from caches import channelCaches

from utils.loginPrivileges import is_login

from caches import channelCaches

class DefaultChannel(Resource):
    """
    数据库中is_default:1的频道
    """
    def get(self):
        """
        获取所有默认的文章频道
        :return:
        """
        channels = channelCaches.DefauleChannelsCaches().get()
        return {"default_channel": channels}, 201


class AllChannel(Resource):
    """
    获取所有频道
    """
    method_decorators = {
        "get":[is_login]
    }
    def get(self):
        """
        获取登录和没登录时文章频道列表
        :return:
        """
        user_id = g.user_id
        #获取所有频道
        all_channels = channelCaches.AllChannelCaches.get()
        if user_id:#用户登录
            channels = channelCaches.UserChannelCaches(user_id).get()

        else:#匿名登录
            channels = channelCaches.AnonymousUserChannelCaches.get()

        return_channel = []
        if channels:
            for i in all_channels:
                if i not in channels:
                    return_channel.append(i)
            return {"channels": return_channel}, 201
        else:
            return {"channels": all_channels}, 201

