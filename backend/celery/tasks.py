from celery import shared_task
from flask_mail import Message
from backend.config.extensions import mail
from flask import current_app,render_template_string
from datetime import datetime,timedelta
from weasyprint import HTML
from sqlalchemy import func
from zoneinfo import ZoneInfo
import time,re,os,uuid
from backend.models import *

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
        if payment.status == "unpaid":
            booking.status = "Rejected"
            payment.status = "expired"
            
            lot = ParkingLot.query.get(booking.parking_lot_id)
            lot_name = lot.name if lot else "the parking lot"

            # Customized notification message
            notif = Notification(
                customer_id=booking.customer_id,
                role="user",
                heading="Your Parking Booking Has Been Rejected",
                message=(
                    f"Dear customer,\n\n"
                    f"Your booking for \"{lot_name}\" has been rejected because we did not receive your payment within the required time frame of 30 Minutes.\n\n"
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

@shared_task
def send_monthly_activity_report():
    with current_app.app_context():
        now = datetime.utcnow()

        # Last Month validation
        tomorrow = now + timedelta(days=1)
        if tomorrow.day != 1:
            print("Not the last day of the month, skipping monthly report generation.")
            return
        


        first_of_month = datetime(now.year, now.month, 1)
        if now.month == 12:
            first_of_next_month = datetime(now.year + 1, 1, 1)
        else:
            first_of_next_month = datetime(now.year, now.month + 1, 1)
        month_year_str = first_of_month.strftime("%B %Y")

        now_str = datetime.now().strftime("%A, %B %d, %Y, %I:%M %p IST")

        users = User.query.filter_by(role='user', active=True).all()
        for user in users:
            report_id = str(uuid.uuid4())

            bookings = Booking.query.filter(
                Booking.customer_id == user.id,
                Booking.start_time >= first_of_month,
                Booking.start_time < first_of_next_month
            ).all()
            payments = Payments.query.filter(
                Payments.customer_id == user.id,
                Payments.due_date >= first_of_month.date(),
                Payments.due_date < first_of_next_month.date()
            ).all()

            # Stats for summary
            parking_lot_counts = {}
            total_spent = 0
            for booking in bookings:
                lotname = booking.parking_lot.name if booking.parking_lot else "Unknown"
                parking_lot_counts[lotname] = parking_lot_counts.get(lotname, 0) + 1
                payment = Payments.query.filter_by(booking_id=booking.id, status="paid").first()
                if payment: total_spent += payment.amount or 0
            most_used = (
                max(parking_lot_counts, key=parking_lot_counts.get)
                if parking_lot_counts else "N/A"
            )

            email_body = (
                f"Hi {user.fname or user.username or 'User'},\n\n"
                "Thanks for keeping up with PARKSY! We appreciate your trust and loyalty.\n"
                "Please find your monthly activity report attached as a PDF.\n\n"
                "Stay smart, commute happy!\n"
                "Team Parksy"
            )

            pdf_template = """
            <html>
            <head>
              <style>
                body { font-family: DejaVu Sans, Arial, sans-serif; }
                h2 { margin-top: 1.4em; color: #537eda; }
                table { width: 100%; border-collapse: collapse; margin-bottom: 2em; font-size: 11px; }
                th, td { border: 1px solid #bbb; padding: 5px; text-align: left; }
                th { background: #f0f0f0; }
              </style>
            </head>
            <body>
              <h2>Bookings Summary - {{ month_year }}</h2>
              <table>
                <tr><th>Total Bookings</th><td>{{ total_bookings }}</td></tr>
                <tr><th>Most Used Parking Lot</th><td>{{ most_used }}</td></tr>
                <tr><th>Total Amount Spent</th><td>₹{{ total_spent }}</td></tr>
              </table>

              <h2>Bookings Details</h2>
              {% if bookings %}
              <table>
                <tr>
                  <th>Date</th>
                  <th>Parking Lot</th>
                  <th>Status</th>
                  <th>Paid Amount</th>
                </tr>
                {% for bk in bookings %}
                <tr>
                  <td>{{ bk.start_time.strftime('%Y-%m-%d') }}</td>
                  <td>{{ bk.parking_lot.name if bk.parking_lot else '' }}</td>
                  <td>{{ bk.status }}</td>
                  <td>
                    {% set payment = (payments|selectattr('booking_id', 'equalto', bk.id)|selectattr('status', 'equalto', 'paid')|list) %}
                    {{ payment[0].amount if payment else 0 }}
                  </td>
                </tr>
                {% endfor %}
              </table>
              {% else %}
              <p>No bookings in this period.</p>
              {% endif %}

              <h2>Payment History</h2>
              {% if payments %}
              <table>
                <tr>
                  <th>Payment Date</th>
                  <th>Booking</th>
                  <th>Status</th>
                  <th>Amount</th>
                </tr>
                {% for pay in payments %}
                <tr>
                  <td>{{ pay.payment_date.strftime('%Y-%m-%d') if pay.payment_date else '' }}</td>
                  <td>{{ pay.booking_id }}</td>
                  <td>{{ pay.status }}</td>
                  <td>₹{{ pay.amount }}</td>
                </tr>
                {% endfor %}
              </table>
              {% else %}
              <p>No payment history for this period.</p>
              {% endif %}
            </body>
            </html>
            """


            pdf_dir = current_app.config.get('REPORTS_DIR', '/tmp')
            os.makedirs(pdf_dir, exist_ok=True)
            pdf_filename = os.path.join(pdf_dir, f"{report_id}.pdf")

            pdf_html_str = render_template_string(
                pdf_template,
                month_year=month_year_str,
                total_bookings=len(bookings),
                most_used=most_used,
                total_spent=total_spent,
                bookings=bookings,
                payments=payments
            )
            HTML(string=pdf_html_str).write_pdf(pdf_filename)

            subject = f"Your Monthly Activity Report ({month_year_str})"
            recipient = user.email
            msg = Message(
                subject=subject,
                sender=current_app.config['MAIL_USERNAME'],
                recipients=[recipient],
                body=email_body,
            )
            with open(pdf_filename, "rb") as fp:
                msg.attach(
                    f"{report_id}.pdf",
                    "application/pdf",
                    fp.read()
                )

            try:
                mail.send(msg)
                print(f"Monthly report sent to {recipient}")
            except Exception as e:
                print(f"Error sending to {recipient}: {e}")

            try:
                os.remove(pdf_filename)
            except Exception:
                pass

@shared_task
def reject_unoccupied_booking(booking_id):
    booking = Booking.query.get(booking_id)
    if not booking:
        return

    if booking.status == "Confirmed":
        booking.status = "Rejected"
        db.session.add(booking)

        parking = ParkingLot.query.get(booking.parking_lot_id)
        if parking and hasattr(parking, "occupied") and parking.occupied > 0:
            parking.occupied -= 1  # Decrement occupied count
            db.session.add(parking)

        # Create Notification
        notif = Notification(
            customer_id=booking.customer_id,
            role="user",
            heading="Booking Rejected",
            message=f"Your booking for {booking.parking_lot.name} was rejected because it was not occupied within 30 minutes of start time."
        )
        db.session.add(notif)

        # Commit DB changes first
        db.session.commit()

        # Send Email to user
        user = User.query.get(booking.customer_id)
        if user and user.email:
            msg = Message(
                subject="Booking Rejected Due to No-Show",
                recipients=[user.email],
                body=(
                    f"Dear {user.fname or user.username},\n\n"
                    f"Your booking for the parking lot '{booking.parking_lot.name}' scheduled from "
                    f"{booking.start_time.strftime('%Y-%m-%d %H:%M')} was rejected because you did not occupy the slot within 30 minutes of the start time.\n\n"
                    "If this is a mistake or you have any questions, please contact support.\n\n"
                    "Thank you."
                )
            )
            mail.send(msg)

@shared_task
def check_overtime_bookings():
    local_tz = ZoneInfo("Asia/Kolkata")
    now_utc = datetime.utcnow().replace(tzinfo=ZoneInfo("UTC"))
    now = now_utc.astimezone(local_tz)  # Current time in IST as aware datetime

    print(f"[check_overtime_bookings] Current Kolkata local time: {now}")

    # Debug: Print all bookings in DB
    all_bookings = Booking.query.all()

    # Filter bookings with 'occupied' status and end_time < now (aware comparison)
    bookings = Booking.query.filter(
        func.lower(Booking.status) == "occupied",
        Booking.end_time < now,
    ).all()

    print(f"[check_overtime_bookings] Bookings found for overtime processing: {len(bookings)}")

    for booking in bookings:
        parking = booking.parking_lot
        user = booking.user

        if not parking or not user:
            
            continue

        # Make booking.end_time tz-aware if naive, using IST
        if booking.end_time.tzinfo is None:
            end_time_aware = booking.end_time.replace(tzinfo=local_tz)
        else:
            end_time_aware = booking.end_time.astimezone(local_tz)

        # Calculate overtime in minutes
        overtime_minutes = (now - end_time_aware).total_seconds() // 60
        intervals = int(overtime_minutes // 30)

        if intervals < 1:
            print(f"  Booking ID={booking.id} overtime less than 30 mins, skipping.")
            continue

        interval_charge = parking.price // 2  # price charged per 30min overtime
        total_overtime_amount = interval_charge * intervals

        # Query unpaid payment for overtime if exists
        payment = Payments.query.filter_by(
            booking_id=booking.id,
            status="unpaid"
        ).order_by(Payments.id.desc()).first()

        if payment:
            if payment.amount < total_overtime_amount:
                payment.amount = total_overtime_amount
                db.session.add(payment)
                print(f"  Updated payment ID={payment.id}, new amount {payment.amount}")
            else:
                print(f"  Payment ID={payment.id} amount already up-to-date: {payment.amount}")
        else:
            # Create overtime payment record
            payment = Payments(
                customer_id=booking.customer_id,
                booking_id=booking.id,
                due_date=now.date(),
                amount=total_overtime_amount,
                status="unpaid"
            )
            db.session.add(payment)
            print(f"  Created new payment for booking ID={booking.id}, amount {payment.amount}")

        db.session.commit()

        # Send email to user notifying overtime charges
        if user.email:
            msg = Message(
                subject="Parking Overtime Warning",
                recipients=[user.email],
                body=(
                    f"Dear {user.fname or user.username},\n\n"
                    f"Your booking for the parking lot '{parking.name}' ended at "
                    f"{booking.end_time.strftime('%Y-%m-%d %H:%M')} but your spot is still occupied.\n"
                    f"You are being charged {interval_charge} currency units every 30 minutes for overtime.\n"
                    f"Current due for overtime: {total_overtime_amount} currency units.\n\n"
                    "Please release the spot immediately to avoid further charges.\n\n"
                    "Thank you."
                )
            )
            mail.send(msg)
            print(f"  Sent overtime warning email to {user.email}")

    print("[check_overtime_bookings] Task completed.")




