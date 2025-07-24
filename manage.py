from flask_migrate import Migrate
from backend.config.extensions import db
from app import createApp

app = createApp()
migrate = Migrate(app, db)

if __name__ == "__main__":
    app.run(debug=True, port=7000)
