from flask import Blueprint, session, redirect, url_for, render_template, jsonify, request,current_app,send_file
from backend.models import *
from backend.config.extensions import db,cache
from sqlalchemy import func, extract,case, desc
from backend.celery.tasks import expire_booking_if_unpaid,notify_users_new_parking_lot,generate_report_pdf
from datetime import datetime
import os

admin = Blueprint('admin', __name__)

@admin.get("/admin/dashboard")
def dashboard():
    if ("username" in session) and (session['role'] == 'admin'):
        return render_template("admin_db.html")
    return render_template("notfound.html")

@cache.cached(timeout=5)
@admin.route("/admin/dashboard_data")
def dashboard_data():
    if ("username" in session) and (session['role'] == 'admin'):
        users = User.query.all()
        bookings = Booking.query.all()
        payments = Payments.query.all()

        total_users = len(users) - 1
        total_bookings = len(bookings)
        active_slots = len(set(b.slot_id for b in bookings if b.slot_id))
        total_revenue = sum(p.amount for p in payments if p.status == "paid")

        revenue_by_month = [0] * 12
        for p in payments:
            if p.status == "paid" and p.payment_date:
                month = p.payment_date.month
                revenue_by_month[month - 1] += p.amount

        bookings_by_month = [0] * 12
        for b in bookings:
            if b.date_booked:
                month = b.date_booked.month
                bookings_by_month[month - 1] += 1

        bookings_by_lot = {}
        for b in bookings:
            if b.parking_lot and b.parking_lot.name:
                lot_name = b.parking_lot.name
                bookings_by_lot[lot_name] = bookings_by_lot.get(lot_name, 0) + 1

        booking_status = {}
        for b in bookings:
            status = b.status
            booking_status[status] = booking_status.get(status, 0) + 1

        revenue_status = {"Received": 0, "Pending": 0}
        for p in payments:
            if p.status == "paid":
                revenue_status["Received"] += p.amount
            else:
                revenue_status["Pending"] += p.amount

        return jsonify({
            "cards": [
                {"label": "Total Users", "value": total_users},
                {"label": "Total Bookings", "value": total_bookings},
                {"label": "Active Parking Lots", "value": active_slots},
                {"label": "Total Revenue", "value": f"₹{total_revenue:,}"}
            ],
            "activities": [
                {"user": "sourav", "action": "Logged in", "timestamp": "2025-07-15 14:30"},
                {"user": "nidhi", "action": "Booked slot A1", "timestamp": "2025-07-15 13:05"},
            ],
            "revenue": revenue_by_month,
            "bookings_over_time": bookings_by_month,
            "bookings_by_slot": bookings_by_lot,
            "booking_status": booking_status,
            "revenue_status": revenue_status
        })

@admin.get("/admin/manage-lots")
def manage_lots():
    if ("username" in session) and (session['role'] == 'admin'):
        return render_template("manage_lots.html")
    return render_template("notfound.html")

@cache.cached(timeout=5)
@admin.route("/admin/manage-lots/data")
def get_lots_data():
    if ("username" in session) and (session['role'] == 'admin'):
        lots = ParkingLot.query.order_by(ParkingLot.id).all()
        lots_data = []
        for lot in lots:
            lots_data.append({
                "id": lot.id,
                "name": lot.name,
                "address": lot.address,
                "capacity": lot.capacity,
                "occupied": lot.occupied,
                "price": lot.price,
                "active": lot.active,
            })
        return jsonify(lots_data)

@admin.route("/admin/manage-lots/toggle-active/<int:lot_id>", methods=["POST"])
def toggle_lot_active(lot_id):
    if ("username" in session) and (session['role'] == 'admin'):
        lot = ParkingLot.query.get_or_404(lot_id)
        data = request.get_json()
        new_status = data.get("active")

        if new_status is None:
            return jsonify(success=False, error="Missing active status"), 400
        
        if not new_status and lot.occupied > 0:
            return jsonify(
                success=False,
                error=f"Cannot mark Lot #{lot.id} as unavailable. {lot.occupied} spot(s) still occupied."
            ), 400

        lot.active = bool(new_status)
        db.session.commit()
        return jsonify(success=True, active=lot.active)


@admin.route("/admin/manage-lots/add", methods=["POST"])
def add_lot():
    if ("username" in session) and (session['role'] == 'admin'):
        data = request.get_json()
        name = data.get("name", "").strip()
        address = data.get("address", "").strip()
        capacity = data.get("capacity")
        price = data.get("price")

        if not name or not address or capacity is None or price is None:
            return jsonify(success=False, error="Missing required fields"), 400

        try:
            capacity = int(capacity)
            price = int(price)
        except ValueError:
            return jsonify(success=False, error="Capacity and price must be numbers"), 400

        new_lot = ParkingLot(
            name=name,
            address=address,
            capacity=capacity,
            occupied=0,
            price=price,
            active=True,
            owner_id=1
        )
        db.session.add(new_lot)
        db.session.commit()

        # Trigger Celery task in background
        notify_users_new_parking_lot.delay(new_lot.id)

        return jsonify(success=True, lot_id=new_lot.id)

@cache.cached(timeout=5)
@admin.route('/admin/manage-lots/bookings/<int:lot_id>', methods=['GET'])
def get_lot_bookings(lot_id):
    lot = ParkingLot.query.get(lot_id)
    if not lot:
        return jsonify({'success': False, 'error': 'Parking lot not found'}), 404

    bookings = Booking.query.filter_by(parking_lot_id=lot_id).all()

    bookings_data = []
    for b in bookings:
        user = b.user
        bookings_data.append({
            'booking_id': b.id,
            'customer_name': f"{user.fname} {user.lname}" if user else "N/A",
            'car_reg_no': user.reg_no if user else "N/A",
            'slot_id': b.slot_id,
            'status': b.status,
            'start_time': b.start_time.strftime("%Y-%m-%d %H:%M"),
            'end_time': b.end_time.strftime("%Y-%m-%d %H:%M")
        })

    return jsonify({'success': True, 'bookings': bookings_data})




@admin.get("/admin/manage-users")
def manage_users():
    if ("username" in session) and (session['role'] == 'admin'):
        return render_template("manage_users.html")
    return render_template("notfound.html")

@cache.cached(timeout=5)
@admin.route("/admin/users_data")
def get_users_data():
    if ("username" in session) and (session['role'] == 'admin'):
        users = User.query.filter(User.role != 'admin').all()
        users_list = []
        for u in users:
            users_list.append({
                "id": u.id,
                "username": u.username,
                "full_name": f"{u.fname or ''} {u.lname or ''}".strip(),
                "email": u.email,
                "role": u.role,
                "phone": u.phone,
                "reg_no": u.reg_no,
                "active": u.active
            })
        return jsonify(users_list)

@admin.route("/admin/delete_user/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    if ("username" in session) and (session['role'] == 'admin'):
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return jsonify({"success": True})

@admin.route("/admin/toggle_user_active/<int:user_id>", methods=["POST"])
def toggle_user_active(user_id):
    if ("username" in session) and (session['role'] == 'admin'):
        user = User.query.get_or_404(user_id)
        user.active = not user.active
        db.session.commit()
        return jsonify({"success": True, "active": user.active})

@admin.get("/admin/bookings")
def bookings():
    if ("username" in session) and (session['role'] == 'admin'):
        return render_template("admin_bookings.html")
    return render_template("notfound.html")

@cache.cached(timeout=5)
@admin.route('/admin/bookings_data')
def bookings_data():
    if ("username" in session) and (session['role'] == 'admin'):
        bookings = (
            Booking.query
            .join(User, Booking.customer_id == User.id)
            .join(ParkingLot, Booking.parking_lot_id == ParkingLot.id)
            .add_columns(
                Booking.id,
                User.email,
                Booking.slot_id,
                Booking.start_time,
                Booking.end_time,
                Booking.status,
                ParkingLot.name.label('parking_lot'),
                ParkingLot.capacity,
                ParkingLot.occupied,
                ParkingLot.price.label('price_per_hour')
            )
            .order_by(Booking.start_time.desc())
            .all()
        )

        result = []
        for b in bookings:
            available_slots = b.capacity - b.occupied
            result.append({
                "id": b.id,
                "email": b.email,
                "slot": b.slot_id,
                "start_time": b.start_time.strftime('%Y-%m-%d %H:%M'),
                "end_time": b.end_time.strftime('%Y-%m-%d %H:%M'),
                "status": b.status,
                "parking_lot": b.parking_lot,
                "available_slots": available_slots,
                "price_per_hour": b.price_per_hour
            })

        return jsonify(result)

@admin.route('/admin/accept_booking/<int:booking_id>', methods=['POST'])
def accept_booking(booking_id):
    if ("username" in session) and (session['role'] == 'admin'):
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({"success": False, "message": "Booking not found"}), 404

        if booking.status != 'Requested':
            return jsonify({"success": False, "message": "Already processed"}), 400

        lot = ParkingLot.query.get(booking.parking_lot_id)
        if not lot:
            return jsonify({"success": False, "message": "Parking lot not found"}), 404

        hours = (booking.end_time - booking.start_time).total_seconds() / 3600
        amount = round(hours * lot.price)

        payment = Payments(
            customer_id=booking.customer_id,
            booking_id=booking.id,
            due_date=booking.end_time.date(),
            amount=amount,
            status="unpaid"
        )
        db.session.add(payment)

        booking.status = "Accepted"

        notif = Notification(
            customer_id=booking.customer_id,
            role="user",
            heading="Booking Accepted",
            message=f"Your booking for {lot.name} (Slot ID: {booking.slot_id}) has been accepted. Amount due: ₹{amount}. Please pay it within 6 hours to confirm your booking."
        )
        db.session.add(notif)

        db.session.commit()

        expire_booking_if_unpaid.apply_async(
        args=[booking.id, payment.id],
        countdown=6*60*60
        )
        return jsonify({"success": True})

@admin.route('/admin/reject_booking/<int:booking_id>', methods=['POST'])
def reject_booking(booking_id):
    if ("username" in session) and (session['role'] == 'admin'):
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({"success": False, "message": "Booking not found"}), 404

        if booking.status not in ['Requested', 'Accepted']:
            return jsonify({"success": False, "message": "Already processed"}), 400

        # ---- Expire active payment request if exists ----
        active_payments = Payments.query.filter_by(
            booking_id=booking.id,
            status="unpaid"
        ).all()
        for payment in active_payments:
            payment.status = "expired"

        lot = ParkingLot.query.get(booking.parking_lot_id)
        if lot and lot.occupied > 0:
            lot.occupied -= 1

        booking.status = "Rejected"

        notif = Notification(
            customer_id=booking.customer_id,
            role="user",
            heading="Booking Rejected",
            message=f"Your booking for {lot.name} has been rejected."
        )
        db.session.add(notif)
        db.session.commit()

        return jsonify({"success": True})

@admin.route('/admin/confirm_booking/<int:booking_id>', methods=['POST'])
def confirm_booking(booking_id):
    if ("username" in session) and (session['role'] == 'admin'):
        booking = Booking.query.get(booking_id)
        if not booking or booking.status != "Accepted":
            return jsonify({"success": False, "message": "Booking not eligible for confirmation."}), 400

        payment = Payments.query.filter_by(booking_id=booking.id).first()
        if payment and payment.status != "paid":
            payment.status = "paid"
            payment.payment_by = "Admin"
            payment.payment_date = datetime.utcnow().date()

        booking.status = "Confirmed"

        lot = ParkingLot.query.get(booking.parking_lot_id)
        notif = Notification(
            customer_id=booking.customer_id,
            role="user",
            heading="Booking Confirmed",
            message=f"Your booking for {lot.name} has been confirmed. Payment marked as paid by admin."
        )
        db.session.add(notif)

        db.session.commit()
        return jsonify({"success": True})

@admin.get("/admin/reports")
def reports():
    if ("username" in session) and (session['role'] == 'admin'):
        return render_template("reports.html")
    return render_template("notfound.html")

@cache.cached(timeout=5)
@admin.get("/admin/reports_data")
def admin_reports():
    try:
        accomplishment_statuses = ["Accomplished"]

        def get_bookings_trend():
            try:
                bookings_trend = (
                    db.session.query(
                        func.extract('year', Booking.start_time).label('year'),
                        func.extract('month', Booking.start_time).label('month'),
                        func.count(Booking.id).label('bookings'),
                        func.sum(
                            case(
                                (Booking.status.in_(accomplishment_statuses), 1),
                                else_=0,
                            )
                        ).label('accomplished'),
                        func.sum(case((Booking.status == "Cancelled", 1), else_=0)).label('cancelled'),
                        func.sum(func.coalesce(Payments.amount, 0)).label('revenue'),
                    )
                    .outerjoin(Payments, Payments.booking_id==Booking.id)
                    .group_by('year', 'month')
                    .order_by(desc('year'), desc('month'))
                    .limit(6)
                    .all()
                )
                mode = "extract"
            except Exception:
                bookings_trend = (
                    db.session.query(
                        func.strftime('%Y-%m', Booking.start_time).label('month'),
                        func.count(Booking.id).label('bookings'),
                        func.sum(
                            case(
                                (Booking.status.in_(accomplishment_statuses), 1),
                                else_=0,
                            )
                        ).label('accomplished'),
                        func.sum(case((Booking.status == "Cancelled", 1), else_=0)).label('cancelled'),
                        func.sum(func.coalesce(Payments.amount, 0)).label('revenue'),
                    )
                    .outerjoin(Payments, Payments.booking_id==Booking.id)
                    .group_by('month')
                    .order_by(desc('month'))
                    .limit(6)
                    .all()
                )
                mode = "strftime"
            return bookings_trend, mode


        bookings_trend, _mode = get_bookings_trend()
        trend_res = []

        for row in bookings_trend:
            if hasattr(row, "year") and hasattr(row, "month"):
                if row.year and row.month:
                    month_str = f"{int(row.year):04d}-{int(row.month):02d}"
                    month_and_year = datetime(int(row.year), int(row.month), 1).strftime("%B %Y")
                else:
                    month_and_year = "Unknown"
                    month_str = ""
            else:
                month_and_year = datetime.strptime(row.month, "%Y-%m").strftime("%B %Y")
                month_str = row.month

            # Top lot
            if _mode == 'strftime':
                top_lot_q = db.session.query(
                    ParkingLot.name, func.count(Booking.id).label('cnt')
                ).join(
                    Booking, Booking.parking_lot_id==ParkingLot.id
                ).filter(
                    func.strftime('%Y-%m', Booking.start_time)==month_str
                ).group_by(ParkingLot.id).order_by(desc('cnt')).first()
            else:
                top_lot_q = db.session.query(
                    ParkingLot.name, func.count(Booking.id).label('cnt')
                ).join(
                    Booking, Booking.parking_lot_id==ParkingLot.id
                ).filter(
                    func.extract('year', Booking.start_time)==row.year,
                    func.extract('month', Booking.start_time)==row.month
                ).group_by(ParkingLot.id).order_by(desc('cnt')).first()

            bookings = int(row.bookings)
            accomplished = int(getattr(row, "accomplished", 0) or 0)
            accomplishment_rate = f'{round(100 * accomplished / bookings, 1) if bookings else 0}%'

            # Send revenue as numeric for frontend formatting
            trend_res.append({
                'month_and_year': month_and_year,
                'bookings': bookings,
                'accomplishment_rate': accomplishment_rate,
                'revenue': float(row.revenue or 0),
                'top_parking_spot': top_lot_q[0] if top_lot_q else '-'
            })


        # Bookings Analytics Table
        lot_rows = []
        for lot in ParkingLot.query.all():
            bookings = Booking.query.filter_by(parking_lot_id=lot.id).all()
            accomplished = sum(1 for b in bookings if b.status and b.status == "Accomplished")
            cancelled = sum(1 for b in bookings if b.status and b.status == "Cancelled")
            lot_rows.append({
                'name': lot.name,
                'capacity': lot.capacity,
                'location': lot.address,
                'bookings_total': len(bookings),
                'accomplishment_rate': f"{round(100 * accomplished/len(bookings),1) if bookings else 0}%",
                'cancellation_rate': f"{round(100 * cancelled/len(bookings),1) if bookings else 0}%"
            })


        lots_table = []
        for lot in ParkingLot.query.all():
            rev = (
                db.session.query(func.coalesce(func.sum(Payments.amount),0))
                .join(Booking, Booking.id==Payments.booking_id)
                .filter(Booking.parking_lot_id==lot.id, Payments.status=="paid")
                .scalar()
            )
            lots_table.append({
                "lot": lot.name,
                "capacity": lot.capacity,
                "price": float(lot.price),
                "total_revenue": float(rev or 0),
            })


        status_table = []
        for lot in ParkingLot.query.all():
            status_table.append({
                "lot": lot.name,
                "capacity": lot.capacity,
                "occupied": lot.occupied,
            })


        users_table = []
        for user in User.query.filter_by(role='user').all():
            bookings = Booking.query.filter_by(customer_id=user.id).all()
            accomplished = sum(1 for b in bookings if b.status and b.status == "Accomplished")
            cancelled = sum(1 for b in bookings if b.status and b.status == "Cancelled")
            paid = (
                db.session.query(func.sum(Payments.amount))
                .join(Booking)
                .filter(Booking.customer_id==user.id, Payments.status=="paid")
                .scalar() or 0
            )
            unpaid = (
                db.session.query(func.sum(Payments.amount))
                .join(Booking)
                .filter(Booking.customer_id==user.id, Payments.status=="unpaid")
                .scalar() or 0
            )
            users_table.append({
                "name": f"{user.fname or ''} {user.lname or ''}".strip() or user.username,
                "email": user.email,
                "address": user.address,
                "bookings_availed": len(bookings),
                "bookings_accomplished": accomplished,
                "bookings_cancelled": cancelled,
                "revenue_spent": float(paid),
                "revenue_unpaid": float(unpaid),
            })

        return jsonify({
            "trend": trend_res,
            "lots_analytics": lot_rows,
            "lots_table": lots_table,
            "status_table": status_table,
            "users_table": users_table,
        })

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@admin.post("/admin/generate_report_pdf")
def start_pdf_report():
    report_data = request.get_json()
    task = generate_report_pdf.apply_async(args=[report_data])
    return jsonify({"task_id": task.id})

@admin.get("/admin/fetch_report_pdf")
def get_report_pdf():
    pdf_path = os.path.join(current_app.config.get('REPORTS_DIR', '/tmp'), "Parksy_Reports.pdf")
    return send_file(pdf_path, as_attachment=True, download_name="Parksy_Reports.pdf")

@admin.route("/admin/queries")
def queries_page():
    if ("username" in session) and (session['role'] == 'admin'):
        return render_template("queries.html")
    return render_template("notfound.html")

@cache.cached(timeout=5)
@admin.route("/admin/queries_data")
def get_queries():
    if ("username" in session) and (session['role'] == 'admin'):
        queries = Query.query.order_by(Query.date_posted.desc()).all()
        query_data = []

        for q in queries:
            user = User.query.get(q.user_id)
            user_name = user.username if user else f"User #{q.user_id}"

            query_data.append({
                "id": q.id,
                "user_id": q.user_id,
                "user_name": user_name,
                "title": q.title,
                "description": q.description,
                "date_posted": q.date_posted.strftime("%Y-%m-%d %H:%M")
            })

        return jsonify(query_data)

@admin.route("/admin/reply_query/<int:query_id>", methods=["POST"])
def reply_to_query(query_id):
    if ("username" in session) and (session['role'] == 'admin'):
        data = request.get_json()
        reply = data.get("reply", "").strip()

        if not reply:
            return jsonify(success=False, error="Empty reply"), 400

        query = Query.query.get_or_404(query_id)

        notif = Notification(
            customer_id=query.user_id,
            role="customer",
            heading=f"Reply of {(query.title or '')[:50]}",
            message=reply,
            date_sent=datetime.utcnow().date()
        )
        db.session.add(notif)
        db.session.commit()

        return jsonify(success=True)