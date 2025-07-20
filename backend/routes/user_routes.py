from flask import Blueprint,render_template,redirect,url_for,session,jsonify,request,current_app
from werkzeug.utils import secure_filename
import os
from sqlalchemy import func,extract
from backend.config.extensions import db,cache
from backend.models import *
from datetime import datetime, time
from pytz import timezone

IST = timezone('Asia/Kolkata')
now = datetime.now(IST)

user = Blueprint('user', __name__)


@user.route('/user/dashboard')
def dashboard():
    if ("username" in session):
        user = User.query.filter_by(username=session['username']).first()
        return render_template('customer_db.html')
    return render_template("notfound.html")

@cache.cached(timeout=5)
@user.route('/user/dashboard_data')
def dashboard_data():
    if ("username" in session):
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401

        user_obj = User.query.get(session['user_id'])
        if not user_obj:
            return jsonify({"error": "User not found"}), 404

        user_data = {
            "username": user_obj.username,
            "email": user_obj.email,
            "fname": user_obj.fname,
            "lname": user_obj.lname,
            "phone": user_obj.phone,
            "age": user_obj.age,
            "gender": user_obj.gender,
            "reg_no": user_obj.reg_no,
            "address": user_obj.address,
            "profile_image": url_for('static', filename=user_obj.profile_image) if user_obj.profile_image else url_for('static', filename='images/person.png')
        }

        notifications = Notification.query.filter_by(customer_id=user_obj.id).order_by(Notification.date_sent.desc()).limit(5).all()
        notification_data = [
            {
                "heading": n.heading,
                "message": n.message,
                "date": n.date_sent.strftime('%b %d, %Y')
            }
            for n in notifications
        ]

        bookings = Booking.query.filter_by(customer_id=user_obj.id).order_by(Booking.start_time.desc()).limit(5).all()
        booking_data = [
            {
                "location": b.parking_lot.name if b.parking_lot else "",
                "slot": b.slot_id,
                "start_time": b.start_time.strftime('%Y-%m-%d %H:%M'),
                "end_time": b.end_time.strftime('%Y-%m-%d %H:%M'),
                "status": b.status
            }
            for b in bookings
        ]

        payments = Payments.query.filter_by(customer_id=user_obj.id).order_by(Payments.due_date.desc()).limit(5).all()
        payment_data = [
            {
                "amount": p.amount,
                "due_date": p.due_date.strftime('%Y-%m-%d'),
                "status": p.status,
                "location": p.booking.parking_lot.name if p.booking else "N/A"
            }
            for p in payments
        ]

        # Ensure all statuses are included, even if count is 0
        all_statuses = [
        "Requested", "Accepted", "Confirmed",
        "Occupied", "Cancelled", "Rejected", "Accomplished"
        ]
        booking_status = {status: 0 for status in all_statuses}

        booking_status_counts = (
            db.session.query(Booking.status, func.count(Booking.id))
            .filter_by(customer_id=user_obj.id)
            .group_by(Booking.status)
            .all()
        )
        for status, count in booking_status_counts:
            booking_status[status] = count

        payment_status_sums = (
        db.session.query(Payments.status, func.sum(Payments.amount))
        .filter_by(customer_id=user_obj.id)
        .group_by(Payments.status)
        .all()
        )
        
        payment_status = {status: total or 0 for status, total in payment_status_sums}


        total_expenditure = (
            db.session.query(func.sum(Payments.amount))
            .filter_by(customer_id=user_obj.id, status="paid")
            .scalar() or 0
        )

        monthly_counts = (
            db.session.query(extract('month', Booking.date_booked), func.count(Booking.id))
            .filter_by(customer_id=user_obj.id)
            .group_by(extract('month', Booking.date_booked))
            .all()
        )
        monthly_dict = {int(month): count for month, count in monthly_counts}
        monthly_bookings = [monthly_dict.get(m, 0) for m in range(1, 13)]

        return jsonify({
            "user": user_data,
            "notifications": notification_data,
            "bookings": booking_data,
            "payments": payment_data,
            "booking_status": booking_status,
            "payment_status": payment_status,
            "total_expenditure": total_expenditure,
            "monthly_bookings": monthly_bookings
        })

@user.route('/user/find_parking')
def find_parking():
    if ("username" in session):
        return render_template('find_parking.html')
    return render_template("notfound.html")

@cache.cached(timeout=5)
@user.route('/user/find_parking_data')
def find_parking_data():
    if ("username" in session):
        parking_lots = ParkingLot.query.filter_by(active=True).all()

        user_id = session.get('user_id')
        result = []

        for lot in parking_lots:
            booking = None
            if user_id:
                booking = Booking.query.filter(
                    Booking.customer_id == user_id,
                    Booking.parking_lot_id == lot.id,
                    Booking.status.in_(["Requested", "Accepted", "Confirmed", "Occupied"])
                    ).first()


            available_spots = lot.capacity - lot.occupied

            result.append({
                'id': lot.id,
                'name': lot.name,
                'address': lot.address,
                'capacity': lot.capacity,
                'occupied': lot.occupied,
                'available_spots': available_spots,
                'price': lot.price,
                'date_of_registration': lot.date_of_registration.strftime('%Y-%m-%d'),
                'requested': booking is not None,
                'start_time': booking.start_time.isoformat() if booking else None,
                'end_time': booking.end_time.isoformat() if booking else None
            })

        return jsonify(result)

@user.route('/user/book_spot', methods=['POST'])
def book_spot():
    if ("username" in session):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        data = request.get_json()
        lot_id = data.get('lot_id')
        start_time_str = data.get('start_time')
        end_time_str = data.get('end_time')

        if not lot_id or not start_time_str or not end_time_str:
            return jsonify({'success': False, 'message': 'Missing booking time'}), 400

        try:
            start_time = datetime.fromisoformat(start_time_str)
            end_time = datetime.fromisoformat(end_time_str)
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format'}), 400

        lot = ParkingLot.query.get(lot_id)
        if not lot:
            return jsonify({'success': False, 'message': 'Parking lot not found'})

        available = lot.capacity - lot.occupied
        if available <= 0:
            return jsonify({'success': False, 'message': 'No spots available'})

        # Find used slots
        used_slots = db.session.query(Booking.slot_id).filter_by(
            parking_lot_id=lot_id,
            status='Requested'
        ).all()
        used_slot_ids = set(slot[0] for slot in used_slots)

        # Find first available slot
        available_slot = next((i for i in range(1, lot.capacity + 1) if i not in used_slot_ids), None)
        if available_slot is None:
            return jsonify({'success': False, 'message': 'No slots free'})

        # Create new booking
        booking = Booking(
            customer_id=session['user_id'],
            parking_lot_id=lot.id,
            slot_id=available_slot,
            status='Requested',
            date_booked=datetime.utcnow(),
            start_time=start_time,
            end_time=end_time,
        )

        lot.occupied += 1
        db.session.add(booking)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Booking successful', 'slot': available_slot})

@user.route('/user/cancel_booking', methods=['POST'])
def cancel_booking():
    if ("username" in session):
        if 'user_id' not in session:
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        data = request.get_json()
        lot_id = data.get('lot_id')

        if not lot_id:
            return jsonify({"success": False, "message": "Invalid request"}), 400

        user_id = session['user_id']

        # Only cancel the active requested booking
        booking = Booking.query.filter_by(
            customer_id=user_id,
            parking_lot_id=lot_id,
            status='Requested'
        ).first()

        if not booking:
            return jsonify({"success": False, "message": "Booking not found"}), 404

        try:
            parking_lot = ParkingLot.query.get(lot_id)
            if parking_lot.occupied > 0:
                parking_lot.occupied -= 1

            db.session.delete(booking)
            db.session.commit()

            return jsonify({"success": True})

        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "message": str(e)}), 500

@user.route('/user/bookings')
def bookings():
    if ("username" in session):
        return render_template('bookings.html')
    return render_template("notfound.html")

@cache.cached(timeout=5)
@user.route('/user/my_bookings')
def my_bookings():
    if ("username" in session):
        if 'user_id' not in session:
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        user_id = session['user_id']
        now = datetime.utcnow()

        bookings = (
            Booking.query
            .filter_by(customer_id=user_id)
            .join(ParkingLot)
            .add_entity(ParkingLot)
            .order_by(Booking.start_time.asc())
            .all()
        )

        upcoming, past, cancelled = [], [], []

        for booking, lot in bookings:
            data = {
                'id': booking.id,
                'location': lot.name,
                'address': lot.address,
                'start_time': booking.start_time.isoformat(),
                'end_time': booking.end_time.isoformat(),
                'status': booking.status
            }

            if booking.status in ["Cancelled", "Rejected"]:
                cancelled.append(data)
            elif booking.status == "Accomplished" or booking.end_time < now:
                past.append(data)
            else:
                upcoming.append(data)

        return jsonify({
            "success": True,
            "upcoming": upcoming,
            "past": past,
            "cancelled": cancelled
        })

@user.route('/user/cancel_existing_booking/<int:booking_id>', methods=['POST'])
def cancel_existing_booking(booking_id):
    if ("username" in session):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        booking = Booking.query.filter_by(id=booking_id, customer_id=session['user_id']).first()

        if not booking:
            return jsonify({'success': False, 'message': 'Booking not found'}), 404

        try:
            lot = ParkingLot.query.get(booking.parking_lot_id)
            if lot and lot.occupied > 0:
                lot.occupied -= 1

            Payments.query.filter_by(booking_id=booking.id).delete()

            db.session.delete(booking)
            db.session.commit()

            return jsonify({'success': True, 'message': 'Booking deleted successfully'})

        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500


@user.route("/user/occupy_spot/<int:booking_id>", methods=["POST"])
def occupy_spot(booking_id):
    if ("username" in session):
        if "user_id" not in session:
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        booking = Booking.query.filter_by(id=booking_id, customer_id=session["user_id"]).first()
        if not booking:
            return jsonify({"success": False, "message": "Booking not found"}), 404

        now = datetime.now(IST)

        if booking.start_time.tzinfo is None:
            start_time = IST.localize(booking.start_time)
        else:
            start_time = booking.start_time.astimezone(IST)

        if booking.end_time.tzinfo is None:
            end_time = IST.localize(booking.end_time)
        else:
            end_time = booking.end_time.astimezone(IST)

        if not (start_time <= now <= end_time):
            return jsonify({"success": False, "message": "It's not the right time to occupy the spot."}), 400

        if booking.status not in ["Accepted", "Confirmed"]:
            return jsonify({"success": False, "message": "Cannot occupy this booking"}), 400

        booking.status = "Occupied"
        db.session.commit()
        return jsonify({"success": True})

@user.route("/user/release_spot/<int:booking_id>", methods=["POST"])
def release_spot(booking_id):
    if ("username" in session):
        if "user_id" not in session:
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        booking = Booking.query.filter_by(id=booking_id, customer_id=session["user_id"]).first()
        if not booking:
            return jsonify({"success": False, "message": "Booking not found"}), 404

        if booking.status != "Occupied":
            return jsonify({"success": False, "message": "Spot not currently occupied"}), 400

        booking.status = "Accomplished"

        lot = ParkingLot.query.get(booking.parking_lot_id)
        if lot and lot.occupied > 0:
            lot.occupied -= 1

        db.session.commit()
        return jsonify({"success": True})

@user.route('/user/payments')
def payments():
    if ("username" in session):
        return render_template('payments.html')
    return render_template("notfound.html")

@user.route("/user/pay/<int:payment_id>", methods=["POST"])
def mark_payment_paid(payment_id):
    if ("username" in session):
        if "user_id" not in session:
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        payment = Payments.query.get(payment_id)
        if not payment:
            return jsonify({"success": False, "message": "Payment not found"}), 404

        if payment.status == "paid":
            return jsonify({"success": False, "message": "Already paid"}), 400

        payment.status = "paid"
        payment.payment_date = datetime.today().date()
        payment.payment_by = "Self"

        booking = Booking.query.get(payment.booking_id)
        if booking and booking.status == "Accepted":
            booking.status = "Confirmed"

            notif = Notification(
                customer_id=booking.customer_id,
                role="user",
                heading="Payment Confirmed",
                message=f"Your payment for booking at {booking.parking_lot.name} has been confirmed. You're all set!"
            )
            db.session.add(notif)

        db.session.commit()
        return jsonify({"success": True})

@cache.cached(timeout=5)
@user.route("/user/payments-data")
def user_payments_data():
    if ("username" in session):
        if "user_id" not in session:
            return jsonify({"error": "Unauthorized"}), 401

        user_id = session["user_id"]

        history = (
            db.session.query(Payments, Booking, ParkingLot)
            .join(Booking, Payments.booking_id == Booking.id)
            .join(ParkingLot, Booking.parking_lot_id == ParkingLot.id)
            .filter(Payments.customer_id == user_id)
            .all()
        )

        paid = []
        unpaid = []

        for p, b, lot in history:
            if p.status == "paid":
                paid.append({
                    "id": p.id,
                    "parking_lot": lot.name,
                    "amount": p.amount,
                    "payment_date": p.payment_date.strftime('%Y-%m-%d') if p.payment_date else None,
                    "payment_by": p.payment_by,
                    "status": "paid"
                })
            elif p.status == "unpaid":
                due_time = datetime.combine(p.due_date, time(12))

                unpaid.append({
                    "id": p.id,
                    "parking_lot": lot.name,
                    "booking_date": b.start_time.strftime('%Y-%m-%d'),
                    "amount": p.amount,
                    "due_by": due_time.strftime('%Y-%m-%d %H:%M')
                })

        return jsonify({"history": paid, "unpaid": unpaid})

@user.get('/user/help_and_support')
def help_and_support():
    if ("username" in session):
        return render_template('help_and_support.html')
    return render_template("notfound.html")

@user.post('/user/post_query')
def post_query():
    if ("username" in session):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        data = request.get_json()
        title = data.get('title')
        description = data.get('description')

        if not title or not description:
            return jsonify({'error': 'Missing fields'}), 400

        new_query = Query(
            user_id=session['user_id'],
            title=title,
            description=description
        )
        db.session.add(new_query)
        db.session.commit()

        return jsonify({'message': 'Query posted successfully'}), 200

@user.route('/user/notifications')
def notifications():
    if ("username" in session):
        return render_template('notifications.html')
    return render_template("notfound.html")

@cache.cached(timeout=5)
@user.route('/user/notifications/data')
def get_user_notifications():
    if ("username" in session):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"success": False, "message": "Unauthorized"}), 401

        notifications = Notification.query.filter_by(customer_id=user_id).order_by(Notification.date_sent.desc()).all()

        result = [
            {
                "heading": n.heading,
                "message": n.message,
                "date_sent": n.date_sent.strftime('%b %d, %Y')
            }
            for n in notifications
        ]
        
        return jsonify({"success": True, "notifications": result})

@user.route('/user/profile')
def profile():
    if ("username" in session):
        return render_template('profile.html')
    return render_template("notfound.html")

@cache.cached(timeout=5)
@user.route("/user/data", methods=["GET", "POST"])
def handle_user_data():
    if ("username" in session):
        username = session.get("username")
        if not username:
            return jsonify(error="Unauthorized"), 401

        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify(error="User not found"), 404

        if request.method == "GET":
            return jsonify({
                "fname": user.fname,
                "lname": user.lname,
                "phone": user.phone,
                "age": user.age,
                "gender": user.gender,
                "reg_no": user.reg_no,
                "address": user.address,
                "email": user.email,
                "role": user.role,
                "profile_image": user.profile_image or "/static/images/person.png"
            })

        elif request.method == "POST":
            data = request.get_json()

            user.fname = data.get("fname", user.fname)
            user.lname = data.get("lname", user.lname)
            user.phone = data.get("phone", user.phone)
            user.age = data.get("age", user.age)
            user.reg_no = data.get("reg_no", user.reg_no)
            user.address = data.get("address", user.address)

            db.session.commit()
            return jsonify(message="Profile updated successfully.")

@user.route('/user/upload-image', methods=['POST'])
def upload_image():
    if ("username" in session):
        username = session.get("username")
        if not username:
            return jsonify({"error": "Not logged in"}), 401

        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ['.png', '.jpg', '.jpeg']:
            return jsonify({"error": "Unsupported file format"}), 400

        filename = secure_filename(f"{username}{ext}")
        
        image_folder = os.path.join(current_app.static_folder, 'images')
        if not os.path.exists(image_folder):
            os.makedirs(image_folder)

        save_path = os.path.join(image_folder, filename)
        file.save(save_path)

        user = User.query.filter_by(username=username).first()
        user.profile_image = f"images/{filename}"
        db.session.commit()

        return jsonify({
            "message": "Image uploaded successfully.",
            "image_url": f"/static/images/{filename}"
        })