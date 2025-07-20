from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "send_daily_reminder": {
        "task": "backend.celery.tasks.send_daily_reminder",
        "schedule": crontab(hour=10, minute=0)  # Runs daily at 6:06 AM IST/server time
    }
}