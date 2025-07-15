from flask import Blueprint, session, redirect, url_for

admin = Blueprint('admin', __name__)

@admin.get("/dashboard")
def dashboard():
    return "Hello, this is Admin Dashboard"
