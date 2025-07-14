from flask_security import SQLAlchemyUserDatastore, hash_password
from backend.models import db, User, Role
import uuid

def setup_initial_data(app):
    with app.app_context():
        db.create_all()

        userdatastore: SQLAlchemyUserDatastore = app.security.datastore

        userdatastore.find_or_create_role(name='admin', description='superuser')
        userdatastore.find_or_create_role(name='user', description='general user')

        if not userdatastore.find_user(email='admin@study.iitm.ac.in'):
            userdatastore.create_user(
                email='admin@study.iitm.ac.in',
                password=hash_password('cupcake/mad@007_admin'),
                username='admin',
                fs_uniquifier=str(uuid.uuid4()),
                roles=['admin']
            )

        db.session.commit()
