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

    return app

