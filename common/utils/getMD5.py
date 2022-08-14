import hashlib
from flask import current_app

def getMd5(str,secret=None):
    if not secret:
        secret = current_app.config.get("JWT_SECRET")

    md5 = hashlib.md5(secret.encode("utf8"))
    md5.update(str.encode("utf8"))
    res = md5.hexdigest()
    return res