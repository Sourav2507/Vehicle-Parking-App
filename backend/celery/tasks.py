from backend.celery.celery_setup import celery_init_app
from celery import shared_task
import time

@shared_task(ignore_results = False)
def add(x,y):
    time.sleep(10)
    return x+y