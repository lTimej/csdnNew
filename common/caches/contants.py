import random

# 默认用户头像
DEFAULT_USER_PROFILE_PHOTO = 'group1/M00/00/00/wKiZA2L4ThiATR41AAEwN58xN6E785.png'
#   "http://192.168.153.3:8888/group1/M00/00/00/wKiZA2L4ThiATR41AAEwN58xN6E785.png"

class CacheTTL():
    """
    为了防止缓存雪崩以及缓存击穿，根据不同业务设置不同的过期时间
    """
    TTL = 0
    MAX_TTL = 10 * 60

    @classmethod
    def get_TTL(cls):
        return cls.TTL + random.randrange(0,cls.MAX_TTL)

class DataBaseNotData(CacheTTL):
    """
    为了防止缓存穿透，将缓存时间设置小点
    """
    TTL = 5 * 60
    MAX_TTL = 60

class UserInfoCachesTTL(CacheTTL):
    """
    用户信息数据缓存过期时间
    """
    TTL = 30 * 60

class UserStatusCachesTTL(CacheTTL):
    """
    用户信息数据缓存过期时间
    """
    TTL = 60 * 60

class UserOtherInfoCachesTTL(CacheTTL):
    """
    用户信息数据缓存过期时间
    """
    TTL = 30 * 60

class ChannelCacheTTL(CacheTTL):
    """
    频道的缓存过期时间
    """
    TTL = 60 * 60
