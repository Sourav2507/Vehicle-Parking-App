from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "send-hello-email-daily-6am": {
        "task": "backend.celery.tasks.send_hello_email",
        "schedule": crontab(minute=6, hour=4),  # every day at 6:00 AM
        "args": ["souravdebnath9838@gmail.com"]
    }
}
