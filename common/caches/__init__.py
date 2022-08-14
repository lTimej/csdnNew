"""
缓存策略

1、先查缓存，缓存存在直接返回数据
2、缓存不存在，在查数据库
3、数据库不存在，返回None，并在redis存入-1，代表数据不存在
4、数据库存在，返回数据，并将数据做缓存
"""

"""
user_basic_caches:
    格式：key:value
        key为user:basic:info:user_id
        value为字符串里包着字典
            字典里：
                user_name、head_photo、introduce、career、year_code
"""

"""
user_profile_caches:
    格式:key:value
        key为user:basic:info:user_id
        value为字符串里包着字典
            字典里：
                user_name、head_photo、introduce、career、year_code
"""