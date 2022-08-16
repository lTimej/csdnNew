
import re
import imghdr
from datetime import datetime
from utils.getMD5 import getMd5

from models.user import UserProfile


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

#图片验证
def check_img(str):
    """
    imghdr是一个用来检测图片类型的模块，传递给它的可以是一个文件对象，也可以是一个字节流
    :param str:
    :return:
    """
    try:
        img_type = imghdr.what(str)
        print(1111111111111111111111,img_type)
    except :
        raise ValueError("{} is invalid".format(str))
    if not img_type:
        raise ValueError("{} is invalid".format(str))
    else:
        return str

def check_gender(str):
    try:
        str = int(str)
    except:
        raise ValueError("{} is invalid".format(str))
    if str == UserProfile.GENDER.FEMALE or str == UserProfile.GENDER.MALE:
        return str
    else:
        raise ValueError("{} is invalid".format(str))

def chech_date(str):
    try:
        if not str:
            return str
        #前端输入为字符串类型，数据库为date类型，通过datetime.datetime.strptime将字符串类型转为datetime类型
        _str = datetime.strptime(str,'%Y-%m-%d')
    except:
        raise ValueError("{} is invalid".format(str))
    else:
        return _str

def check_channel_name(str1):
    if isinstance(str1,str):
        return str1
    raise ValueError("{} is invalid".format(str1))

