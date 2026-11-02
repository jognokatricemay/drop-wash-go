"""Drop, Wash, Go — Flask app.

Blueprints (one file per part of the app, so team members don't edit the same file):
  auth.py      welcome, login, sign up, shop register / login, logout
  customer.py  shops, booking, my orders, notifications, profile
  staff.py     dashboard, booking requests, orders, shop info
"""
import os

from dotenv import load_dotenv
from flask import Flask, g


def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-change-me"),
        DB_HOST=os.getenv("DB_HOST", "localhost"),
        DB_PORT=int(os.getenv("DB_PORT", "3306")),
        DB_USER=os.getenv("DB_USER", "root"),
        DB_PASSWORD=os.getenv("DB_PASSWORD", ""),
        DB_NAME=os.getenv("DB_NAME", "dropwashgo"),
        DB_SSL=os.getenv("DB_SSL", "0") == "1",
        DB_SSL_CA=os.getenv("DB_SSL_CA", ""),
    )

    from . import auth, customer, db, helpers, staff

    db.init_app(app)
    if os.getenv("AUTO_INIT_DB") == "1":
        db.init_if_empty(app)
    helpers.init_app(app)

    @app.before_request
    def load_unread_count():
        if g.get("user"):
            res = db.query(
                "SELECT COUNT(*) AS unread_count FROM notifications WHERE user_id = %s AND is_read = 0",
                [g.user["id"]],
                one=True,
            
            )

            g.unread_count = res["unread_count"] if res else 0
        else: 
            g.unread_count = 0
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(customer.bp)
    app.register_blueprint(staff.bp)
    return app
