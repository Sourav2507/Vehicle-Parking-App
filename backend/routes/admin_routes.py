from flask import Blueprint, current_app as app
from flask_security import auth_required

admin = Blueprint('admin', __name__)