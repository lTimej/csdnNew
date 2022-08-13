import os
import sys
from flask import jsonify

BASIC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,BASIC_DIR)
sys.path.insert(0,os.path.join(BASIC_DIR,"common"))

from settings.defaultSettings import DefaultSettings
from . import createAPP

app = createAPP(DefaultSettings,False)

@app.route('/')
def route_map():
    """
    主视图，返回所有视图网址
    """
    rules_iterator = app.url_map.iter_rules()
    return jsonify({rule.endpoint: rule.rule for rule in rules_iterator if rule.endpoint not in ('route_map', 'static')})

