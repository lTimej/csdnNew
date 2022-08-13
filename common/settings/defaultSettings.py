
class DefaultSettings():
    #mysql数据库配置
    SQLALCHEMY_BINDS = {
        "m":"mysql://root:liujun@192.168.153.3:3306/csdn",
        "s":"mysql://root:liujun@192.168.153.3:8306/csdn",
        "master":["m"],
        "slaves":["s"],
        "default":"m"
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 追踪数据的修改信号
    SQLALCHEMY_ECHO = True  # 是否打印sql语句执行过程

# 设置三个redis 哨兵
    REDIS_SENTINELS = [
        ('127.0.0.1', '26380'),
        ('127.0.0.1', '26381'),
        ('127.0.0.1', '26382'),
    ]
    REDIS_SENTINEL_SERVICE_NAME = 'mymaster'

    # redis 集群
    REDIS_CLUSTER = [
        {'host': '127.0.0.1', 'port': '7000'},
        {'host': '127.0.0.1', 'port': '7001'},
        {'host': '127.0.0.1', 'port': '7002'},
    ]


class CeleryConfig():
    broker_url = 'amqp://time:liujun@192.168.153.3:5672/csdn'
    # 容联云通讯短信验证码有效期，单位：秒
    SMS_CODE_REDIS_EXPIRES = 300
    # 短信模板
    SEND_SMS_TEMPLATE_ID = 1