from flask import current_app,g
from flask_restful import Resource
from flask_restful import inputs

from sqlalchemy.exc import DatabaseError
from flask_restful.reqparse import RequestParser

from utils.loginPrivileges import is_login
from utils import parsers

from caches import channelCaches
from models.news import UserChannel
from models import db

class UserChannlesView(Resource):
    '''
    登录和未登录时选择的文章频道的获取，增加和修改
    '''
    method_decorators = [is_login]

    def save(self,channel):
        '''
        修改或新增
        :param channel:字典类型
        :return:
        '''
        try:
            uc = UserChannel.query.filter(UserChannel.user_id == g.user_id, UserChannel.is_deleted == True,
                                          UserChannel.channel_id == channel.get("id")).first()
            if uc:
                uc.is_deleted = False
                db.session.add(uc)
                db.session.commit()
            else:
                uc = UserChannel(user_id=g.user_id,channel_id=channel.get("id"))
                db.session.add(uc)
                db.session.commit()
        except DatabaseError as e:
            current_app.logger.error(e)
            db.session.rollback()
            return {'message': "data Invalid"}, 401

    def get(self):
        """
        获取登录和未登录时频道
        :return:
        """
        #获取匿名登录时缓存频道信息
        anonymousChannel = channelCaches.AnonymousUserChannelCaches.get()
        #用户id
        user_id = g.user_id
        if user_id:#已登录
            #获取用户频道缓存
            user_channels = channelCaches.UserChannelCaches(user_id).get()
            #用户频道缓存不存在
            if not user_channels:
                if  not anonymousChannel:#没有登录和已登录时，缓存都为空
                    #返回空
                    return {'channels': anonymousChannel}, 201
                #没登陆时，缓存有，将选择的频道，添加到已登录状态
                for user_channel in user_channels:
                    self.save(user_channel)
                #更新数据库后，将缓存区删除，更新
                channelCaches.UserChannelCaches(user_id).delete()
                return {'channels': anonymousChannel}, 201
            if not anonymousChannel:#未登录缓存为空，将已登录缓存存入未登录缓存中
                channelCaches.AnonymousUserChannelCaches.save(user_channels)
                return {'channels': user_channels}, 201
            for c in anonymousChannel:
                flag = channelCaches.UserChannelCaches(user_id).exists(c.get("id"))
                if not flag:
                    self.save(c)
                    user_channels.append(c)
                    channelCaches.UserChannelCaches(user_id).delete()
            return {'channels': user_channels}, 201
        return {'channels': anonymousChannel}, 201

    def post(self):#增加登录和未登录频道
        parser = RequestParser()
        parser.add_argument("channel_id",type=inputs.positive,required=True,location="json")
        parser.add_argument("channel_name",type=parsers.check_channel_name,required=True,location="json")
        args = parser.parse_args()

        channel_id = args.channel_id
        channel_name = args.channel_name

        channel_dict = {
            "id": channel_id,
            "channel_name": channel_name
        }
        user_id = g.user_id
        if user_id:#已登录
            flag = channelCaches.UserChannelCaches(user_id).exists(channel_id)
            if not flag:
                self.save(channel_dict)
                channelCaches.UserChannelCaches(user_id).delete()
                channel_list = channelCaches.UserChannelCaches(user_id).get()
                channelCaches.AnonymousUserChannelCaches.save(channel_list)
                return {'channels': channel_list}, 201
            return {"message": "It is exist"}, 400
        else:#没有登录
            flag = channelCaches.AnonymousUserChannelCaches.exists(channel_id)
            if not flag:
                ac = channelCaches.AnonymousUserChannelCaches.get()
                ac.append(channel_dict)
                channelCaches.AnonymousUserChannelCaches.save(ac)
                return {'channels': ac}, 201
            return {"message": "It is exist"}, 400

    def patch(self):
        """
        修改登录和未登录频道
        :return:
        """
        parser = RequestParser()
        parser.add_argument("channel_id",type=inputs.positive,required=True,location="json")
        args = parser.parse_args()
        channel_id = args.channel_id

        user_id = g.user_id
        if not user_id:
            flag = channelCaches.AnonymousUserChannelCaches.exists(channel_id)
            if not flag:
                return {"message": "It is not exist"}, 400
            channels = channelCaches.AnonymousUserChannelCaches.get()
            for channel in channels:
                if channel.get("id") == channel_id:
                    channels.remove(channel)
                    break
            channelCaches.AnonymousUserChannelCaches.save(channels)
            return {'channels': channels}, 201
        else:
            flag = channelCaches.UserChannelCaches(user_id).exists(channel_id)
            if not flag:
                return {"message": "It is not exist"}, 400
            try:
                UserChannel.query.filter_by(user_id=user_id, channel_id=channel_id).update({'is_deleted': True})
                db.session.commit()
            except DatabaseError as e:
                current_app.logger.error(e)
                db.session.rollback()
            channelCaches.UserChannelCaches(user_id).delete()
            channels = channelCaches.UserChannelCaches(user_id).get()
            channelCaches.AnonymousUserChannelCaches.save(channels)
            return {'channels': channels}, 201

