from flask import Flask,render_template
from backend.config.config import LocalDevelopmentConfig
from backend.config.create_initial_data import setup_initial_data
from backend.config.extensions import db,cache
from backend.celery.celery_setup import celery_init_app
from backend.routes.auth_routes import auth as auth_bp
from backend.routes.user_routes import user as user_bp
from backend.routes.admin_routes import admin as admin_bp

def createApp():
    app = Flask(
        __name__,
        template_folder="frontend/templates",
        static_folder="frontend",
        static_url_path="/static"
    )

    # Load config
    app.config.from_object(LocalDevelopmentConfig)

    # Initialize SQLAlchemy
    db.init_app(app)
    cache.init_app(app)

    # Push app context for initial DB setup
    with app.app_context():
        # Create tables and default admin user
        setup_initial_data(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)

    return app

# Create app instance
app = createApp()

celery_app = celery_init_app(app)
app.celery = celery_app

@app.errorhandler(404)
def page_not_found(e):
    return render_template('notfound.html'), 404


# Run server
if __name__ == '__main__':
    app.run(debug=True, port=7070)
