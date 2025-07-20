from celery import shared_task
from flask_mail import Message
from backend.config.extensions import mail
from flask import current_app
import time
import re
from backend.models import *

@shared_task(ignore_results = False)
def add(x,y):
    time.sleep(10)
    return x+y

def is_valid_email(email):
    pattern = r"^[^@\s]+@[^@\s]+\.[a-zA-Z0-9]+$"
    return email and re.match(pattern, email)

@shared_task
def send_daily_reminder():
    with current_app.app_context():
        users = User.query.filter_by(role='user', active=True).all()
        subject = "👋 Daily Reminder from Parksy!"
        for user in users:
            if is_valid_email(user.email):
                greeting = f"Hello {user.fname}," if user.fname else (f"Hello {user.username}," if user.username else "Hello,")
                body = (
                    f"{greeting}\n\n"
                    "Just a daily friendly reminder from the Parksy team! "
                    "Check out our app today to book your parking spots in advance, "
                    "manage your bookings, and enjoy a hassle-free commuting experience.\n\n"
                    "We're always here to make parking smarter!\n"
                    "Your Parksy Team 🚗"
                )
                try:
                    msg = Message(
                        subject=subject,
                        sender=current_app.config["MAIL_USERNAME"],
                        recipients=[user.email],
                        body=body
                    )
                    mail.send(msg)
                    print(f"[Celery] Daily reminder sent to {user.email}")
                except Exception as e:
                    print(f"[Celery] Error sending to {user.email}: {e}")
            else:
                print(f"[Celery] Skipped syntactically invalid email: {user.email}")

@shared_task
def expire_booking_if_unpaid(booking_id, payment_id):
    with current_app.app_context():
        booking = Booking.query.get(booking_id)
        payment = Payments.query.get(payment_id)
        if not booking or not payment:
            return "No booking or payment found."
        if payment.status != "paid":
            booking.status = "Rejected"
            payment.status = "expired"
            
            lot = ParkingLot.query.get(booking.parking_lot_id)
            lot_name = lot.name if lot else "the parking lot"

            notif = Notification(
                customer_id=booking.customer_id,
                role="user",
                heading="Booking Rejected: Payment Not Received",
                message=f"Your booking for {lot_name} was rejected because the payment was not received within 6 hours.",
                date_sent=datetime.utcnow().date()
            )
            db.session.add(notif)
            db.session.commit()
            return f"Booking {booking_id} rejected, payment {payment_id} expired, notification sent."
        return f"Booking {booking_id} already paid, nothing done."