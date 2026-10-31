"""Welcome, customer login / sign up, shop register / login, logout.  Owner: Member 1"""
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from .db import execute, query

bp = Blueprint("auth", __name__)


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
        user = query("SELECT * FROM users WHERE role='customer' AND mobile=%s", [mobile], one=True)
        if not user or not check_password_hash(user["password_hash"], form.get("password", "")):
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
        if not (mobile.isdigit() and len(mobile) == 11 and mobile.startswith("09")):
            errors["mobile"] = "Enter an 11-digit mobile number, e.g. 09171234567."
        elif query("SELECT id FROM users WHERE mobile=%s", [mobile], one=True):
            errors["mobile"] = "This mobile number already has an account."
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
        user = query("SELECT * FROM users WHERE role='staff' AND username=%s", [form.get("username", "").strip()], one=True)
        if not user or not check_password_hash(user["password_hash"], form.get("password", "")):
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
        if username and query("SELECT id FROM users WHERE username=%s", [username], one=True):
            errors["username"] = "This username is taken."
        if len(form.get("password", "")) < 8:
            errors["password"] = "Use at least 8 characters."
        if not errors:
            shop_id = execute("INSERT INTO shops (name, address, contact_number, owner_name) VALUES (%s,%s,%s,%s)",
                              [form["shop_name"].strip(), form["address"].strip(), form["contact_number"].strip(),
                               form["owner_name"].strip()])
            execute("INSERT INTO users (role, full_name, username, password_hash, shop_id) VALUES ('staff',%s,%s,%s,%s)",
                    [form["owner_name"].strip(), username, generate_password_hash(form["password"]), shop_id])
            flash("Shop registered. Log in to set your services, rates and payments.")
            return redirect(url_for("auth.staff_login"))
    return render_template("auth/staff_register.html", errors=errors, form=form)


@bp.route("/logout")
def logout():
    was_staff = g.user and g.user["role"] == "staff"
    session.clear()
    return redirect(url_for("auth.staff_login" if was_staff else "auth.welcome"))
