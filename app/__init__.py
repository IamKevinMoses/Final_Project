# Adding the Flask application factory
from pathlib import Path

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

from app.database import db

bcrypt = Bcrypt()
login_manager = LoginManager()

def create_app():

    app = Flask(__name__)

    app.config["SECRET_KEY"] = "development-secret-key"

    BASE_DIR = Path(__file__).resolve().parent.parent
    DATABASE_PATH = BASE_DIR / "database" / "project.db"

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DATABASE_PATH.as_posix()}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    #Initialize SQLAlchemy
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "main.login"
    # Import models BEFORE creating tables
    from app import models

    #Import routes
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    #Create database tables
    with app.app_context():
        db.create_all()

    return app
#How to load a user from the database
from app.models import User

@login_manager.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))