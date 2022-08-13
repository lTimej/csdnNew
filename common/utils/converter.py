from werkzeug.routing import BaseConverter

class MobileConverter(BaseConverter):
    regex = r'1[3-9]\d{9}'

def registerConverter(app):
    app.url_map.converters['mobile'] = MobileConverter
