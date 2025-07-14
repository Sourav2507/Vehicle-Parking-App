class Config():
    DEBUG = False
    SQL_ALCHEMY_TRACK_MODIFICATIONS = False

class LocalDevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///database.sqlite3"
    DEBUG = True
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_PASSWORD_SALT = 'vehicle_parking_app_IITM_MAD2'
    SECRET_KEY = "vehicle_parking_app_IITM_MAD2"
    SECURITY_TOKEN_AUTHENTICATION_HEADER = 'Authentication-Token'
    SECURITY_TOKEN_MAX_AGE = 3600
    WTF_CSRF_ENABLED = False

    CACHE_TYPE =  "RedisCache"
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_REDIS_PORT = 6379