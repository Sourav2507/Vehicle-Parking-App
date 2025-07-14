from flask import Blueprint, current_app as app
from flask_security import auth_required

user = Blueprint('user', __name__)