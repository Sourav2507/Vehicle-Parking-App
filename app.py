from flask import Flask
from backend.config.config import LocalDevelopmentConfig
from backend.models import db, User, Role
from flask_security import Security, SQLAlchemyUserDatastore
from backend.config.create_initial_data import setup_initial_data

# Import blueprints
from backend.routes.auth_routes import auth as auth_bp
from backend.routes.user_routes import user as user_bp
from backend.routes.admin_routes import admin as admin_bp

def createApp():
    app = Flask(__name__,template_folder="frontend/templates",static_folder="frontend",static_url_path="/static")
    app.config.from_object(LocalDevelopmentConfig)
    db.init_app(app)

    # Setup Flask-Security
    datastore = SQLAlchemyUserDatastore(db, User, Role)
    app.security = Security(app, datastore=datastore, register_blueprint=False)

    # Register Blueprints
    app.register_blueprint(auth_bp)                        # /login, /protected, /
    app.register_blueprint(user_bp, url_prefix="/user")    # /user/...
    app.register_blueprint(admin_bp, url_prefix="/admin")  # /admin/...

    app.app_context().push()
    return app

# Create app
app = createApp()

# Initialize default roles and admin user
setup_initial_data(app)

if __name__ == '__main__':
    app.run(debug=True, port=7000)
