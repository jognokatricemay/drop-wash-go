"""Welcome, customer login / sign up, shop register / login, logout.  Owner: Member 1"""
import re
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .db import execute, query

bp = Blueprint("auth", __name__)

USERNAME_RULE = re.compile(r"^[A-Za-z0-9._]{4,30}$") #letters, numbers, . and _ only
EMAIL_RULE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$") #smthing@smthing.something

def valid_mobile(number):
    return number.isdigit() and len(number) == 11 and number.startswith("09")

def home_for(user):
    return url_for("staff.dashboard" if user["role"] == "staff" else "customer.home")


def safe_next(default):
    nxt = request.values.get("next", "")
    # only allow paths inside this site
    return nxt if nxt.startswith("/") and not nxt.startswith("//") else default


@bp.route("/")
def welcome():
    if g.user:
        return redirect(home_for(g.user))
    return render_template("auth/welcome.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    errors, form = {}, {}
    # "Log in to book at <shop>" when coming from a shop's Book button
    booking_shop = None
    nxt = request.values.get("next", "")
    if "/shops/" in nxt and "/book" in nxt:
        try:
            shop_id = int(nxt.split("/shops/")[1].split("/")[0])
            booking_shop = query("SELECT id, name FROM shops WHERE id=%s", [shop_id], one=True)
        except ValueError:
            pass

    if request.method == "POST":
        form = request.form
        mobile = form.get("mobile", "").replace(" ", "")
        password = form.get("password", "")
        user = query("SELECT * FROM users WHERE role='customer' AND mobile=%s", [mobile], one=True)
        if not mobile or not password:
            errors["login"] = "Enter your mobile number and password."
        elif not user or not check_password_hash(user["password_hash"], password):
            errors["login"] = "Wrong mobile number or password."
        else:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(safe_next(url_for("customer.home")))
    return render_template("auth/login.html", errors=errors, form=form, booking_shop=booking_shop, next=nxt)


@bp.route("/create-account", methods=["GET", "POST"])
def create_account():
    errors, form = {}, {}
    if request.method == "POST":
        form = request.form
        name = form.get("full_name", "").strip()
        mobile = form.get("mobile", "").replace(" ", "")
        email = form.get("email", "").strip() or None
        password = form.get("password", "")
        if not name:
            errors["full_name"] = "Enter your full name."
        if not valid_mobile(mobile):
            errors["mobile"] = "Enter an 11-digit mobile number, e.g. 09171234567."
        elif query("SELECT id FROM users WHERE mobile=%s", [mobile], one=True):
            errors["mobile"] = "This mobile number already has an account."
        if email and not EMAIL_RULE.match(email):
            errors["email"] = "Enter a valid email, e.g. juan@gmail.com"
        if len(password) < 8:
            errors["password"] = "Use at least 8 characters."
        elif password != form.get("confirm_password"):
            errors["confirm_password"] = "Passwords don't match."
        if not errors:
            uid = execute("INSERT INTO users (role, full_name, mobile, email, password_hash) VALUES ('customer',%s,%s,%s,%s)",
                          [name, mobile, email, generate_password_hash(password)])
            session.clear()
            session["user_id"] = uid
            return redirect(safe_next(url_for("customer.home")))
    return render_template("auth/create_account.html", errors=errors, form=form, next=request.values.get("next", ""))


@bp.route("/shop/login", methods=["GET", "POST"])
def staff_login():
    errors, form = {}, {}
    if request.method == "POST":
        form = request.form
        username = form.get("username", "").strip()
        password = form.get("password", "")
        # BINARY = exact match, so "FE.REYES" is not the same as "fe.reyes"
        user = query("SELECT * FROM users WHERE role='staff' AND BINARY username=%s", [username], one=True)
        if not username or not password:
            errors["login"] = "Enter your username and password."
        elif not user or not check_password_hash(user["password_hash"], password):
            errors["login"] = "Wrong username or password."
        else:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("staff.dashboard"))
    return render_template("auth/staff_login.html", errors=errors, form=form)


@bp.route("/shop/register", methods=["GET", "POST"])
def staff_register():
    errors, form = {}, {}
    if request.method == "POST":
        form = request.form
        required = ["shop_name", "contact_number", "address", "owner_name", "username"]
        for key in required:
            if not form.get(key, "").strip():
                errors[key] = "This field is required."
        username = form.get("username", "").strip()
        if username and not USERNAME_RULE.match(username):
            errors["username"] = "Use 4-30 letters, numbers, . or _ (no spaces)."
        elif username and query("SELECT id FROM users WHERE username=%s", [username], one=True):
            errors["username"] = "This username is taken."
        contact = form.get("contact_number", "").replace(" ", "")
        if contact and not valid_mobile(contact):
            errors["contact_number"] = "Enter an 11-digit mobile number, e.g. 09171234567."
        password = form.get("password", "")
        if len(password) < 8:
            errors["password"] = "Use at least 8 characters."
        elif password != form.get("confirm_password"):
            errors["confirm_password"] = "Passwords don't match."
        if not errors:
            shop_id = execute("INSERT INTO shops (name, address, contact_number, owner_name) VALUES (%s,%s,%s,%s)",
                              [form["shop_name"].strip(), form["address"].strip(), contact,
                               form["owner_name"].strip()])
            execute("INSERT INTO users (role, full_name, username, password_hash, shop_id) VALUES ('staff',%s,%s,%s,%s)",
                    [form["owner_name"].strip(), username, generate_password_hash(password), shop_id])
            flash("Shop registered. Log in to set your services, rates and payments.")
            return redirect(url_for("auth.staff_login"))
    return render_template("auth/staff_register.html", errors=errors, form=form)


@bp.route("/logout")
def logout():
    was_staff = g.user and g.user["role"] == "staff"
    session.clear()
    return redirect(url_for("auth.staff_login" if was_staff else "auth.login"))
