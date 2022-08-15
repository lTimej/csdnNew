

class StasticsBase(object):
    '''
    静态值统计：用户关注量、粉丝数、文章发表数.....
    '''
    key = ""

    def get(self):
        pass

    def incr(self):
        pass

    def reset(self):
        pass

#用户关注数
class UserFocusStastics(StasticsBase):
    key = ""