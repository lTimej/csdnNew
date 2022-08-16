import json

from flask import current_app

from redis.exceptions import RedisError
from sqlalchemy.orm import load_only,contains_eager
from sqlalchemy.exc import DatabaseError

from models.news import Channel,UserChannel
from caches import contants

class DefauleChannelsCaches():
    '''
    默认频道缓存
    key:[dict{channel_id:channel_name}]
    '''
    def __init__(self):
        self.key = "default:channel"
        self.redis = current_app.redis_cluster

    def get(self):
        try:
            channels_list = self.redis.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            channels_list = []
        if channels_list:
            return json.loads(channels_list)
        else:
            channels_list = self.save()
            return channels_list

    def save(self):
        try:
            channels = Channel.query.options(load_only(Channel.id,Channel.name)).filter(Channel.is_default==True,Channel.is_visible==True).order_by(Channel.sequence,Channel.id).all()
        except DatabaseError as e:
            current_app.logger.error(e)
            return {"msg":"Data error"},405
        if not channels:
            return []
        channel_list = []
        for channel in channels:
            channel_list.append({
                'id': channel.id,
                'channel_name': channel.name
            })
        #保存redis
        try:
            self.redis.setex(self.key,contants.ChannelCacheTTL.get_TTL(),json.dumps(channel_list))
        except RedisError as e:
            current_app.logger.error(e)
        return channel_list

    def exist(self):
        try:
            channels = self.redis.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            return False
        if channels:return True
        else:
            ch = self.save()
            return True if ch else False

    def delete(self):
        try:
            self.redis.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

class AllChannelCaches():
    """
    获取所有频道
    """
    key = "all:channel"


    @classmethod
    def get(cls):
        redis = current_app.redis_cluster
        try:
            all_channels = redis.get(cls.key)
        except RedisError as e:
            current_app.logger.error(e)
            all_channels = []
        if all_channels:return json.loads(all_channels)
        else:
            all_channel = cls.save()
            return all_channel

    @classmethod
    def save(cls):
        redis = current_app.redis_cluster
        try:
            all_channels = Channel.query.options(load_only(Channel.id ,Channel.name)).filter(Channel.is_visible==True,Channel.is_default==False).order_by(Channel.sequence,Channel.id).all()
        except DatabaseError as e:
            current_app.logger.error(e)
            return {"msg":"Data error"},405
        if not all_channels:
            return []
        channels_list = []
        for all_channel in all_channels:
            channels_list.append({
                'id': all_channel.id,
                'channel_name': all_channel.name
            })
        try:
            redis.setex(cls.key,contants.ChannelCacheTTL.get_TTL(),json.dumps(channels_list))
        except RedisError as e:
            current_app.logger.error(e)
        return channels_list

    @classmethod
    def exists(cls):
        pass

    @classmethod
    def delete(cls):
        '''
        清楚缓存
        :return:
        '''
        redis = current_app.redis_cluster
        try:
            redis.delete(cls.key)
        except RedisError as e:
            current_app.logger.error(e)

class UserChannelCaches():
    """
    用户选择的频道缓存
    """
    def __init__(self,user_id):
        self.key = "user:channel"
        self.user_id = user_id
        self.redis = current_app.redis_cluster

    def get(self):
        try:
            user_channel = self.redis.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            user_channel = []
        if user_channel: return json.loads(user_channel)
        res = self.save()
        return res

    def save(self):
        try:
            channels = UserChannel.query.join(UserChannel.channel).options(load_only(UserChannel.channel_id),contains_eager(UserChannel.channel).load_only(Channel.name)).filter(UserChannel.user_id==self.user_id,UserChannel.is_deleted==False,Channel.is_visible==True).all()
        except DatabaseError as e:
            current_app.logger.error(e)
            raise  e
        if not channels:return []
        user_channel = []
        for channel in channels:
            user_channel.append({
                "id": channel.channel_id,
                "channel_name": channel.channel.name
            })
        try :
            self.redis.setex(self.key,contants.ChannelCacheTTL.get_TTL(),json.dumps(user_channel))
        except RedisError as e:
            current_app.logger.error(e)
        return user_channel

    def exists(self,channel_id):
        channels = self.get()
        for channel in channels:
            if channel.get("id") == channel_id:
                return True
        return False

    def delete(self):
        '''
        清楚缓存
        :return:
        '''
        try:
            self.redis.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

class AnonymousUserChannelCaches():
    """
    获取所有没有登录用户所选频道
    不用保存数据库，直接缓存redis
    """
    key = "anonymoue:user:channel"

    @classmethod
    def get(cls):
        redis = current_app.redis_cluster
        try:
            all_channels = redis.get(cls.key)
        except RedisError as e:
            current_app.logger.error(e)
            all_channels = []
        if all_channels:
            return json.loads(all_channels)
        else:
            return []

    @classmethod
    def save(cls,channels_list):
        '''
        保存匿名用户的频道
        :param channels_list: list
        :return:
        '''
        redis = current_app.redis_cluster
        try:
            redis.setex(cls.key, contants.ChannelCacheTTL.get_TTL(), json.dumps(channels_list))
        except RedisError as e:
            current_app.logger.error(e)
            raise {"message": " saved failed"}

    @classmethod
    def exists(cls,channel_id):
        channels = cls.get()
        for channel in channels:
            if channel.get("id") == channel_id:return True
        return False

    @classmethod
    def delete(cls):
        '''
        清楚缓存
        :return:
        '''
        redis = current_app.redis_cluster
        try:
            redis.delete(cls.key)
        except RedisError as e:
            current_app.logger.error(e)