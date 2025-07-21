from celery import shared_task
from flask_mail import Message
from backend.config.extensions import mail
from flask import current_app,render_template_string
from datetime import datetime
from weasyprint import HTML
import time
import os
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
        subject = "Daily Reminder from Parksy"
        for user in users:
            if is_valid_email(user.email):
                name = user.fname or user.username or "Valued Customer"
                greeting = f"Hello {name},"
                body = (
                    f"{greeting}\n\n"
                    "We hope this message finds you well. This is your daily reminder from the Parksy team to make the most of our convenient parking services!\n\n"
                    "With Parksy, you can easily reserve your parking spot in advance, manage your current bookings, and enjoy a more seamless commuting experience.\n\n"
                    "Thank you for choosing Parksy. Your trust inspires us to keep improving every day.\n\n"
                    "Wishing you a smooth and stress-free journey.\n"
                    "The Parksy Team"
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

            # Customized notification message
            notif = Notification(
                customer_id=booking.customer_id,
                role="user",
                heading="Your Parking Booking Has Been Cancelled",
                message=(
                    f"Dear customer,\n\n"
                    f"Your booking for \"{lot_name}\" has been cancelled because we did not receive your payment within the required time frame of 6 hours.\n\n"
                    "If this was an oversight or if you need the spot, please feel free to make a new booking at your convenience. "
                    "We recommend completing your payment promptly in the future to secure your parking spot without any interruptions.\n\n"
                    "We appreciate your understanding and thank you for being a valued member of Parksy.\n\n"
                    "Best regards,\n"
                    "The Parksy Team"
                ),
                date_sent=datetime.utcnow().date()
            )
            db.session.add(notif)
            db.session.commit()
            return f"Booking {booking_id} rejected, payment {payment_id} expired, notification sent."
        return f"Booking {booking_id} already paid, nothing done."

    

@shared_task
def notify_users_new_parking_lot(lot_id):

    with current_app.app_context():
        lot = ParkingLot.query.get(lot_id)
        if not lot:
            print("[Celery] No parking lot found with id:", lot_id)
            return

        users = User.query.filter_by(role='user', active=True).all()
        subject = f"New Parking Lot Now Open: {lot.name}"
        for user in users:
            if is_valid_email(user.email):
                # Use user's first name if available, then username, then a fallback
                name = user.fname or user.username or "Customer"
                greeting = f"Hello invaluable customer {name},\n"
                body = (
                    f"{greeting}\n"
                    "With your continuous support, we're pleased to inform you that we have opened a new parking lot just for you!\n\n"
                    f"Parking Lot: {lot.name}\n"
                    f"Address: {lot.address}\n"
                    f"Capacity: {lot.capacity} vehicles\n"
                    f"Price: ₹{lot.price} per use\n\n"
                    "Your feedback and trust motivate us to make Parksy better every day. We invite you to try our new facility and experience more efficient parking. Thank you for being a valued member of our community.\n\n"
                    "Best regards,\n"
                    "The Parksy Team"
                )
                try:
                    msg = Message(
                        subject=subject,
                        sender=current_app.config["MAIL_USERNAME"],
                        recipients=[user.email],
                        body=body
                    )
                    mail.send(msg)
                    print(f"[Celery] Notification sent to {user.email}")
                except Exception as e:
                    print(f"[Celery] Error sending to {user.email}: {e}")
            else:
                print(f"[Celery] Skipped syntactically invalid email: {user.email}")

@shared_task
def generate_report_pdf(report_data):
    """
    Generate a PDF report for Parksy using report_data (dict) sent from frontend.
    The PDF is rendered from an inline HTML Jinja template using WeasyPrint.
    """

    # Formatting the current date in the requested format, e.g., "Monday, July 21, 2025, 9:31 PM IST"
    now_str = datetime.now().strftime("%A, %B %d, %Y, %I:%M %p IST")

    template = """
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Parksy Reports</title>
      <style>
        body { font-family: "DejaVu Sans", Arial, sans-serif; }
        h1, h2 { margin-top: 2em; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 2em; }
        th, td { border: 1px solid #ccc; padding: 5px; text-align: left; }
        th { background: #f7f7f7; }
        .users-table { font-size: 9px; }
      </style>
    </head>
    <body>
      <h1>Parksy Reports</h1>
      <p><strong>Current date:</strong> {{ now }}</p>

      <h2>Monthly Bookings Trend</h2>
      <table>
        <thead>
          <tr>
            <th>Month and Year</th>
            <th>Bookings</th>
            <th>Accomplishment Rate</th>
            <th>Revenue Generated</th>
            <th>Top Parking Spot</th>
          </tr>
        </thead>
        <tbody>
        {% for row in trend %}
          <tr>
            <td>{{ row.month_and_year }}</td>
            <td>{{ row.bookings }}</td>
            <td>{{ row.accomplishment_rate }}</td>
            <td>{{ row.revenue }}</td>
            <td>{{ row.top_parking_spot }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>

      <h2>Bookings Analytics</h2>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Capacity</th>
            <th>Location</th>
            <th>Bookings (till now)</th>
            <th>Accomplishment Rate</th>
            <th>Cancellation Rate</th>
          </tr>
        </thead>
        <tbody>
        {% for row in lots_analytics %}
          <tr>
            <td>{{ row.name }}</td>
            <td>{{ row.capacity }}</td>
            <td>{{ row.location }}</td>
            <td>{{ row.bookings_total }}</td>
            <td>{{ row.accomplishment_rate }}</td>
            <td>{{ row.cancellation_rate }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>

      <h2>Parking Lots</h2>
      <table>
        <thead>
          <tr>
            <th>Parking Lot</th>
            <th>Capacity</th>
            <th>Price/Hour</th>
            <th>Total Revenue</th>
          </tr>
        </thead>
        <tbody>
        {% for row in lots_table %}
          <tr>
            <td>{{ row.lot }}</td>
            <td>{{ row.capacity }}</td>
            <td>{{ row.price }}</td>
            <td>{{ row.total_revenue }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>

      <h2>Current Parking Lot Status</h2>
      <table>
        <thead>
          <tr>
            <th>Parking Lot</th>
            <th>Capacity</th>
            <th>Occupied</th>
          </tr>
        </thead>
        <tbody>
        {% for row in status_table %}
          <tr>
            <td>{{ row.lot }}</td>
            <td>{{ row.capacity }}</td>
            <td>{{ row.occupied }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>

      <h2>Users Analytics</h2>
      <table class="users-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Email Id</th>
            <th>Address</th>
            <th>Bookings Availed</th>
            <th>Bookings Accomplished</th>
            <th>Booking Cancelled</th>
            <th>Revenue Spent</th>
            <th>Revenue Unpaid</th>
          </tr>
        </thead>
        <tbody>
        {% for row in users_table %}
          <tr>
            <td>{{ row.name }}</td>
            <td>{{ row.email }}</td>
            <td>{{ row.address }}</td>
            <td>{{ row.bookings_availed }}</td>
            <td>{{ row.bookings_accomplished }}</td>
            <td>{{ row.bookings_cancelled }}</td>
            <td>{{ row.revenue_spent }}</td>
            <td>{{ row.revenue_unpaid }}</td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    </body>
    </html>
    """

    pdf_filename = os.path.join(
        current_app.config.get('REPORTS_DIR', '/tmp'),
        "Parksy_Reports.pdf"
    )

    # Render the full HTML with all data
    html_str = render_template_string(
        template,
        now=now_str,
        trend=report_data["trend"],
        lots_analytics=report_data["lots_analytics"],
        lots_table=report_data["lots_table"],
        status_table=report_data["status_table"],
        users_table=report_data["users_table"]
    )
    HTML(string=html_str).write_pdf(pdf_filename)
    return pdf_filename