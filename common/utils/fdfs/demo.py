from fdfs_client.client import Fdfs_client
# # #
client = Fdfs_client('/home/time/csdnNew/csdnNew/common/utils/fdfs/client.conf')
ret = client.upload_by_filename('/home/time/csdnNew/csdnNew/common/utils/fdfs/t3.png')
#{'Group name': 'group1', 'Remote file_id': 'group1/M00/00/00/wKiZA2L4ThiATR41AAEwN58xN6E785.png', 'Status': 'Upload successed.', 'Local file name':
print(ret)
import json
import time
# d = {"id":1,"channel_name":"python"}
# c = {"id":1,"channel_name":"python"}
# a = [
#     {"id":1,"channel_name":"python"},
#     {"id":2,"channel_name":"python1"},
#     {"id":3,"channel_name":"python2"},
#     {"id":4,"channel_name":"python3"},
#     {"id":5,"channel_name":"python4"},
#     {"id":6,"channel_name":"python5"},
# ]
# b = [
#     {"id":1,"channel_name":"python"},
#     {"id":3,"channel_name":"python2"},
#     {"id":4,"channel_name":"python3"},
#     {"id":5,"channel_name":"python4"},
# ]
# for i in a:
#     if i not in b:
#         print(i)
# a = "2021-05-10 17:07:49"
# b = a[:a.find(' ')]
# print(b)
# l = [1391913784997576704, 1391913701547704320, 1391913700885004288, 1391913696153829376]
# # ll = 1391913696153829376
# # c = ll in l
# # print(c)
# class A:
#     def __init__(self,a):
#         self.a = a
#         self.b = self.set()
#     def set(self):
#         return 0
#     def post(self):
#         print("A_post")
#     def get(self):
#         print("A")
#         self.post()
# class B(A):
#     def post(self):
#         print(self.b)
#         print("B_post")
#     def set(self):
#         return 90
#
# class C(A):
#     def post(self):
#         print("C_post")
#     def set(self):
#         return 20
#
def outer(func):
    def wrapper(a):
        print("前")
        func()
        print("后")
    return wrapper