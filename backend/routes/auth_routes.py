from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from backend.config.extensions import db,cache
from backend.models import *

from celery.result import AsyncResult

auth = Blueprint('auth', __name__)

@auth.route('/')
def home():
    return render_template('landing.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'username' in session:
            if session['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('user.dashboard'))
        else:
            return render_template("login.html")

    elif request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data received"}), 400

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"message": "Username and password required"}), 400

        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):
                session.permanent = True
                session['user_id'] = user.id
                session['role'] = user.role
                session['username'] = user.username
                session['email'] = user.email

                if user.role == 'admin':
                    redirect_url = url_for('admin.dashboard')
                else:
                    redirect_url = url_for('user.dashboard')

                return jsonify({
                    "message": "Login successful",
                    "redirect": redirect_url,
                    "role": user.role
                }), 200
            else:
                return jsonify({"message": "Wrong password"}), 401
        else:
            return jsonify({"message": "Username doesn't exist"}), 404

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        if 'username' in session:
            return redirect(url_for('auth.login'))
        return render_template("register.html")

    elif request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({"message": "No data received"}), 400

        username = data.get('username')
        email = data.get('email')

        if User.query.filter_by(username=username).first():
            return jsonify({"message": "Username already exists"}), 409

        if User.query.filter_by(email=email).first():
            return jsonify({"message": "Email already exists"}), 409

        password = data.get('password')
        confirm_password = data.get('confirm_password')

        if not password or password != confirm_password:
            return jsonify({"message": "Passwords do not match or are empty"}), 400

        user = User(
            username=username,
            password=generate_password_hash(password),
            fname=data.get('fname'),
            lname=data.get('lname'),
            email=email,
            phone=data.get('ph_no'),
            age=data.get('age'),
            gender=data.get('gender'),
            reg_no=data.get('reg_no'),
            address=f"{data.get('city')}, {data.get('state')}",
            role='user',
            profile_image='images/person.png'
        )

        db.session.add(user)
        db.session.commit()

        session.permanent = True
        session['user_id']=user.id
        session['username'] = username
        session['email'] = email
        session['role'] = 'user'

        return jsonify({
            "message": "Registration successful",
            "redirect": url_for('user.dashboard')
        }), 200

@auth.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect('/')

@auth.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
