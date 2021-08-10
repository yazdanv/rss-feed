import hashlib

from app.core.config import settings


def make_password(password):
    salt = settings.SECRET_KEY.encode()
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return str(key)
