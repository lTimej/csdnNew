import json

from flask import current_app
from redis.exceptions import RedisError
from models.user import User,UserProfile

from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm import load_only,contains_eager

from caches import contants
class UserBasicInfoCache():
    '''
    用户基本情况
    key:"dict"
    获取user_name、head_photo、introduce、career、year_code
    '''
    def __init__(self,user_id):
        """
        :param user_id:指定用户
        """
        self.key = "user:basic:info:{}".format(user_id)
        self.redis = current_app.redis_cluster
        self.user_id = user_id

    def get(self):
        """
        获取数据，redis中没有，去数据库查，数据库没有返回None，并在redis设置为-1，数据库存在，redis没有，则在redis存一份
        :return: dict
        """
        try:#首先从redis中获取数据
            user_info = self.redis.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            user_info = None
        if user_info:#有缓存
            if user_info == b"-1":#缓存没有数据
                return None
            else:#缓存有数据
                return json.loads((user_info))
        else:#没有缓存
            return self.save()

    def save(self):
        """
        查数据库并进行缓存
        :return:查询的数据
        """
        try:
            user = User.query.join(User.profile).options(load_only(User.name,User.profile_photo,User.introduction,User.code_year),contains_eager(User.profile).load_only(UserProfile.career)).filter(User.id==self.user_id).first()
        except DatabaseError as e:
            current_app.logger.error(e)
            raise e
        if not user:#数据库没有数据，缓存存入-1
            try:
                self.redis.setex(self.key, contants.DataBaseNotData.get_TTL(), -1)
            except RedisError as e:
                current_app.logger.error(e)
            return None
        #构造返回数据并存入redis中
        user_dict = {
            "user_name":user.name,
            "user_profile_photo":user.profile_photo if user.profile_photo else contants.DEFAULT_USER_PROFILE_PHOTO,
            "user_introduction":user.introduction,
            "user_code_year":user.code_year,
            "user_career":user.profile.career
        }
        user_str = json.dumps(user_dict)
        try:
            self.redis.setex(self.key,contants.UserInfoCachesTTL.get_TTL(),user_str)
        except RedisError as e:
            current_app.logger.error(e)
        return user_dict

    def exist(self):
        try:
            res = self.redis.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            res = None
        if res:
            if res == b"-1":
                return False
        else:
            res = self.save()
            if res is None:
                return False
        return True

    def delete(self):
        try:
            self.redis.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

class UserOtherInfo():
    """
    用户其他信息
    key:"dict
    获取生日，性别，标签，地区在UserProfile
    """
    def __init__(self,user_id):
        self.key = "user:other:info:{}".format(user_id)
        self.redis = current_app.redis_cluster
        self.user_id = user_id

    def get(self):
        try:
            user_profile = self.redis.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            user_profile = None
        if user_profile:#由于UerProfile表是User的扩展，因此不必将数据库不存在做继续验证
            return json.loads(user_profile)
        else:#缓存没有，去数据库找，并存入redis
            return self.save()

    def save(self):
        try:
            userProfile = UserProfile.query.options(
                load_only(UserProfile.birthday, UserProfile.gender, UserProfile.tag, UserProfile.area)).filter(
                UserProfile.id == self.user_id).first()
            user_profile = {
                'birthday': userProfile.birthday.strftime('%Y-%m-%d') if userProfile.birthday else '',
                'gender': '男' if userProfile.gender == 0 else '女',
                'tag': userProfile.tag,
                'area': userProfile.area
            }
            # 存入redis
            try:
                self.redis.setex(self.key, contants.UserOtherInfoCachesTTL.get_TTL(), json.dumps(user_profile))
            except RedisError as e:
                current_app.logger.error(e)
            return user_profile
        except DatabaseError as e:
            current_app.logger.error(e)
            return {"msg": "database error"}, 405

    def exist(self):
        try:
            user_profile = self.redis.get(self.key)
        except RedisError as e:
            current_app.logger.error(e)
            user_profile = None
        if user_profile:#由于UerProfile表是User的扩展，因此不必将数据库不存在做继续验证
            return True
        else:#缓存没有，去数据库找，并存入redis
            if self.save(): return True
            else: return False

    def delete(self):
        try:
            self.redis.delete(self.key)
        except RedisError as e:
            current_app.logger.error(e)

