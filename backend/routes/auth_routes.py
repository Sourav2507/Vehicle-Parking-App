from flask import Blueprint, current_app as app,request,jsonify,render_template
from flask_security import auth_required,verify_password,hash_password
from backend.models import *
import uuid

auth = Blueprint('auth', __name__)

@auth.route("/")
def home():
    return render_template("index.html")

@auth.get("/protected")
@auth_required()
def protected():
    return "This message is visible only to Authenticated User."

@auth.post("/login")
def login():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message" : "Invalid Inputs"}),404
    
    datastore = app.security.datastore
    
    user = datastore.find_user(email=email)
    if not user:
        return jsonify({"message" : "User not found"}),404
    
    if verify_password(password,user.password):
        return jsonify({"token" : user.get_auth_token(),
                        "email" : user.email,
                        "roles": [role.name for role in user.roles],
                        "id" : user.id}), 200
    return jsonify({"message" : "Invalid Password"}),404

@auth.post("/register")
def register():
    data = request.get_json()

    required_fields = ['username', 'email', 'password']
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"{field} is required"}), 400

    # Check if user already exists
    datastore = app.security.datastore
    if datastore.find_user(email=data['email']):
        return jsonify({"error": "User with this email already exists"}), 409
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Username already taken"}), 409

    try:
        # Create user
        new_user = datastore.create_user(
            username=data['username'],
            email=data['email'],
            password=hash_password(data['password']),
            fs_uniquifier=str(uuid.uuid4()),
            fname=data.get('fname'),
            lname=data.get('lname'),
            age=data.get('age'),
            gender=data.get('gender'),
            phone=data.get('phone'),
            reg_no=data.get('reg_no'),
            address=data.get('address'),
            profile_image=data.get('profile_image'),
            roles=['user']
        )

        db.session.commit()
        return jsonify({
            "token": new_user.get_auth_token(),
            "email": new_user.email,
            "roles": [role.name for role in new_user.roles],
            "id": new_user.id
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500