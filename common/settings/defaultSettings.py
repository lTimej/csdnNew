
class DefaultSettings():
    pass


class CeleryConfig():
    broker_url = 'amqp://time:liujun@192.168.153.3:5672/csdn'
    # 容联云通讯短信验证码有效期，单位：秒
    SMS_CODE_REDIS_EXPIRES = 300
    # 短信模板
    SEND_SMS_TEMPLATE_ID = 1