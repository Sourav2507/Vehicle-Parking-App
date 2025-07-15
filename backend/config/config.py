from datetime import timedelta

class Config():
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class LocalDevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///database.sqlite3"
    SECRET_KEY = "vehicle_parking_app_IITM_MAD2"
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=3600)
    SESSION_PERMANENT = True
    WTF_CSRF_ENABLED = False

    CACHE_TYPE = "RedisCache"
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_REDIS_PORT = 6379
