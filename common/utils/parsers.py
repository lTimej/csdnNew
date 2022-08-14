
import re
from utils.getMD5 import getMd5


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

#账户名验证
def check_name(str):
    if str.find("@") != -1:
        return check_email(str)
    elif len(str) > 8:
        return mobile(str)
    else:
        res = re.match(r"^\w{4,8}$", str)
        if not res:
            raise ValueError("{} is invalid".format(str))
        return str

#密码验证
def check_pwd(str):

    res = re.match(r"^.{8,16}$",str)
    if not res:
        raise ValueError("{} is invalid".format(str))
    else:
        try:
            pwd = getMd5(str)
            return pwd
        except:
            return str

#邮箱验证
def check_email(str):
    pattern = r"^\w*@(qq|126|yeah|139).(net|com|cn)$"
    if not re.match(pattern,str):
        raise ValueError("{} is invalid".format(str))
    return str