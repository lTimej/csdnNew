
import re


#手机号验证
def mobile(mobile_str):

    res = re.match(r"^1[3-9]\d{9}$",mobile_str)
    if not res:
        raise ValueError("{} is invalid".format(mobile_str))
    else:
        return mobile_str

#断行验证码
def regex(pattern):
    """
    正则匹配格式验证
    :param str: 匹配字符串
    :return:
    """
    def validate(str):
        res = re.match(pattern,str)
        if not res:
            raise ValueError("{} is invalid".format(str))
        else:
            return str
    return validate