import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .config import Config

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Blueprints
    from app.controllers.auth import auth_bp
    from app.controllers.store import store_bp
    from app.controllers.paypal import paypal_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(store_bp)
    app.register_blueprint(paypal_bp, url_prefix="/paypal")

    # Stripe keys in app.config for controllers
    app.config['STRIPE_PUBLIC_KEY'] = Config.STRIPE_PUBLIC_KEY
    app.config['STRIPE_SECRET_KEY'] = Config.STRIPE_SECRET_KEY

    return app
