from flask_restful import Resource
from flask_restful.reqparse import RequestParser

from sqlalchemy.exc import DatabaseError

from flask import g,current_app

from caches import userCaches
from models import db
from models.user import User,UserProfile

from utils import parsers
from utils.getMD5 import getMd5
from utils.loginPrivileges import loginPrivi

class Profile(Resource):
    method_decorators = {
        "get":[loginPrivi],
        "patch":[loginPrivi]
    }
    """
    方法装饰器，判断是否登录，没有登录则不能进入视图
    """
    def get(self):
        user_id = g.user_id
        # userCaches.UserBasicInfoCache(user_id).delete()
        user_dict = userCaches.UserBasicInfoCache(user_id).get()
        user_other_dict = userCaches.UserOtherInfo(user_id).get()
        if not user_dict and not user_other_dict:
            return {"msg":"data not exist"},403
        user_dict.update(user_other_dict)
        return user_dict,201
    def patch(self):
        """
        用户信息修改，patch可实现部分修改
        1、修改数据库
        2、如果有修改，将缓存清除
        3、构造前端所需数据
        :return:user_dict,用户基本信息，跟get返回一致
        """
        parser = RequestParser()
        parser.add_argument("head_photo",type=parsers.check_img,required=False,location="files")
        parser.add_argument("user_name",type=parsers.check_name,required=False,location="json")
        parser.add_argument("gender",type=parsers.check_gender,required=False,location="json")
        parser.add_argument("introduce",type=parsers.regex(r"^.{99}$"),required=False,location="json")
        parser.add_argument("tag",type=parsers.regex(r"^.{16}$"),required=False,location="json")
        parser.add_argument("auth_name",type=parsers.regex(r"^.{2,4}$"),required=False,location="json")
        parser.add_argument("birthday",type=parsers.chech_date,required=False,location="json")
        parser.add_argument("areas",type=parsers.regex(r"^.{99}$"),required=False,location="json")
        parser.add_argument('oldPwd', type=parsers.check_pwd, required=False, location='json')
        parser.add_argument('newPwd', type=parsers.check_pwd, required=False, location='json')
        args = parser.parse_args()

        is_update_userInfo = False
        is_update_userProfileInfo = False

        return_user_dict = {}
        saveData_user_dict = {}
        saveData_userProfile_dict = {}

        if args.head_photo:
            res = current_app.client.upload_by_buffer(args.head_photo.read(), file_ext_name='png')
            if res.get('Status') == 'Upload successed.':
                img_url = res.get('Remote file_id')
                saveData_user_dict['profile_photo'] = img_url
                return_user_dict['head_photo'] = current_app.config['FDFS_DOMAIN'] + img_url
                is_update_userInfo = True
            else:
                return {'message': 'Uploading profile photo image failed.'}, 507
        if args.user_name:
            saveData_user_dict["name"] = args.user_name
            return_user_dict["user_name"] = args.user_name
            is_update_userInfo = True

        if args.gender:
            saveData_userProfile_dict["gender"] = args.gender
            return_user_dict["gender"] = args.gender
            is_update_userProfileInfo = True

        if args.introduce:
            saveData_user_dict["introduction"] = args.introduce
            return_user_dict["introduce"] = args.introduce
            is_update_userInfo = True

        if args.tag:
            saveData_userProfile_dict["tag"] = args.tag
            return_user_dict["tag"] = args.tag
            is_update_userProfileInfo = True

        if args.auth_name:
            saveData_userProfile_dict["real_name"] = args.auth_name
            return_user_dict["auth_name"] = args.auth_name
            is_update_userProfileInfo = True

        if args.birthday:
            saveData_userProfile_dict["birthday"] = args.birthday
            return_user_dict["birthday"] = args.birthday
            is_update_userProfileInfo = True

        if args.areas:
            saveData_userProfile_dict["area"] = args.areas
            return_user_dict["areas"] = args.areas
            is_update_userProfileInfo = True

        if args.newPwd:
            if args.oldPwd:#用户有密码，修改密码
                try:
                    user = User.query.filter(User.password == getMd5(args.oldPwd)).first()
                    if user:#如果用户存在则修改密码
                        saveData_user_dict['password'] = args.newPwd
                        is_update_userInfo = True
                    else:#密码输入错误
                        return {'message': 'password is error.'}, 400
                except DatabaseError as e:
                    current_app.logger.error(e)
                    return {'message': 'database error.'}, 405
            else:#用户没有密码，保存密码
                saveData_user_dict["password"] = args.newPwd
                is_update_userInfo = True

        try:#有数据代表需要修改
            if saveData_user_dict:
                User.query.filter_by(id=g.user_id).update(saveData_user_dict)
            if saveData_userProfile_dict:
                UserProfile.query.filter_by(id=g.user_id).update(saveData_userProfile_dict)
            db.session.commit()
        except DatabaseError as e:
            current_app.logger.error(e)
            db.session.rollback()
            return {'message': 'User name has existed.'}, 405
        if is_update_userInfo:
            userCaches.UserBasicInfoCache(g.user_id).delete()
        if is_update_userProfileInfo:
            userCaches.UserOtherInfo(g.user_id).delete()
        return return_user_dict,201










        args = parser.parse_args()






        return {"msg":"ok"},401




