from flask import Flask
from utils.constants import GLOBAL_SETTING_ENV_NAME

def _createApp(DefaultSet,enableSet):
    app = Flask(__name__)
    app.config.from_object(DefaultSet)
    if enableSet:
        app.config.from_envvar(GLOBAL_SETTING_ENV_NAME)
    return app

def createAPP(DefaultSet,enableSet):
    app = _createApp(DefaultSet,enableSet)

    #应用注册
    #用户登录
    from .resources.users import user_bp
    app.register_blueprint(user_bp)

    #加载数据
    from models import db
    db.init_app(app)

    #redis主从
    from redis.sentinel import Sentinel
    _sentinel = Sentinel(app.config.get("REDIS_SENTINELS"))
    app.redis_master = _sentinel.master_for(app.config.get("REDIS_SENTINEL_SERVICE_NAME"))
    app.redis_slave = _sentinel.slave_for(app.config.get("REDIS_SENTINEL_SERVICE_NAME"))

    #redis集群
    from rediscluster import RedisCluster
    app.redis_cluster = RedisCluster(startup_nodes=app.config.get("REDIS_CLUSTER"))


    return app

