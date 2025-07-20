from celery import shared_task
from flask_mail import Message
from backend.config.extensions import mail
from flask import current_app
import time

@shared_task(ignore_results = False)
def add(x,y):
    time.sleep(10)
    return x+y

# @shared_task(ignore_results=False)
@shared_task
def send_hello_email(to_email):
    with current_app.app_context():
        msg = Message(
            subject="Hello from Celery!",
            sender=current_app.config["MAIL_USERNAME"],
            recipients=[to_email],
            body="Hi Sourav! This email was sent via a scheduled Celery task. ✉️"
        )
        mail.send(msg)
        print(f"[Celery] Email sent to {to_email}")