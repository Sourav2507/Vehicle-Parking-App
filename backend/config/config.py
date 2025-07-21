from datetime import timedelta
from backend.celery.celery_scheduler import CELERY_BEAT_SCHEDULE

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
    CACHE_DEFAULT_TIMEOUT = 30
    CACHE_REDIS_PORT = 6379

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'developersouravdebnath@gmail.com'
    MAIL_PASSWORD = ''
    MAIL_DEFAULT_SENDER = 'developersouravdebnath@gmail.com'

    CELERY = dict(
        broker_url="redis://localhost:6379/0",
        result_backend="redis://localhost:6379/1",
        task_ignore_result=False,
        timezone='Asia/Kolkata',
        beat_schedule=CELERY_BEAT_SCHEDULE
    )

