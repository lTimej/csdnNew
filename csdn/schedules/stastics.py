from caches import dataStastics


def _schedule(cls):
    '''

    :param cls:重新设置统计数据数量的类
    :return:
    '''
    c = cls.db_querys()
    cls.reset(c)



def setSchedule(app):
    '''
    设置定时任务
    :return:
    '''
    with app.app_context():
        _schedule(dataStastics.UserFocusStastics)
        _schedule(dataStastics.UserFollwingStastics)
        _schedule(dataStastics.UserVisitedStastics)

