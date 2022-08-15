from flask import Flask
from utils.constants import GLOBAL_SETTING_ENV_NAME
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor

def _createApp(DefaultSet,enableSet):
    app = Flask(__name__)
    app.config.from_object(DefaultSet)
    if enableSet:
        app.config.from_envvar(GLOBAL_SETTING_ENV_NAME,silent=True)
    return app

def createAPP(DefaultSet,enableSet):
    app = _createApp(DefaultSet,enableSet)

    #配置日志
    from utils.logging import create_logger
    create_logger(app)

    # 注册url转换器
    from utils.converter import registerConverter
    registerConverter(app)
    
    #请求钩子，判断是否登录
    from utils.middleware import authVerify
    app.before_request(authVerify)
    
    #启动定时任务
    executors = {  # 10个线程
        'default': ThreadPoolExecutor(10)
    }
    # 负责管理定时任务
    #  BackgroundScheduler 在框架程序（如Django、Flask）中使用
    app.scheduler = BackgroundScheduler(executors=executors)
    # 添加"静态的"定时任务
    from .schedules.stastics import setSchedule
    app.scheduler.add_job(setSchedule, 'cron', hour=3, args=[app])
    # 启动定时任务调度器
    app.scheduler.start()

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

    #雪花算法
    from utils.snowflake.id_worker import  IdWorker
    app.idWorker = IdWorker(app.config['DATACENTER_ID'],
                             app.config['WORKER_ID'],
                             app.config['SEQUENCE'])

    #fastdfs存储图片
    from fdfs_client.client import Fdfs_client
    app.client = Fdfs_client('/home/time/csdnNew/csdnNew/common/utils/fdfs/client.conf')

    return app

