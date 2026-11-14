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


QUESTIONS = [
    "What is your favorite food?",
    "What was the name of your first pet?",
    "What is your mother's maiden name?",
    "What town were you born in?",
]
QUESTION_OPTIONS = [(q, q) for q in QUESTIONS]  # for the <select> in the sign-up forms
MAX_RESET_TRIES = 5


def clean_answer(text):
    """Ignore capital letters and extra spaces, so "Adobo " matches "adobo"."""
    return " ".join(text.lower().split())


def check_security(form, errors):
    if form.get("security_question") not in QUESTIONS:
        errors["security_question"] = "Choose a security question."
    if len(clean_answer(form.get("security_answer", ""))) < 2:
        errors["security_answer"] = "Enter your answer (at least 2 characters)."

def home_for(user):
    return url_for("staff.dashboard" if user["role"] == "staff" else "customer.home")


def safe_next(default):
    nxt = request.values.get("next", "")
    # only allow paths inside this site
    return nxt if nxt.startswith("/") and not nxt.startswith("//") else default


@bp.route("/")
def welcome():
    """The landing page. Logged-in people go straight to their own home page."""
    if g.user:
        return redirect(home_for(g.user))
    shops = query("""SELECT s.*, MIN(CASE WHEN v.unit='kg' THEN v.rate END) AS from_rate
                     FROM shops s LEFT JOIN services v ON v.shop_id = s.id
                     GROUP BY s.id ORDER BY s.id LIMIT 6""")
    return render_template("auth/landing.html", shops=shops)


@bp.route("/get-started")
def get_started():
    """Choose customer or shop owner (this used to be the first page)."""
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
        check_security(form, errors)
        if not errors:
            uid = execute("""INSERT INTO users (role, full_name, mobile, email, password_hash, security_question, security_answer_hash)
                             VALUES ('customer',%s,%s,%s,%s,%s,%s)""",
                          [name, mobile, email, generate_password_hash(password), form["security_question"],
                           generate_password_hash(clean_answer(form["security_answer"]))])
            session.clear()
            session["user_id"] = uid
            return redirect(safe_next(url_for("customer.home")))
    return render_template("auth/create_account.html", errors=errors, form=form, next=request.values.get("next", ""),
                           question_options=QUESTION_OPTIONS)


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
        check_security(form, errors)
        if not errors:
            shop_id = execute("INSERT INTO shops (name, address, contact_number, owner_name) VALUES (%s,%s,%s,%s)",
                              [form["shop_name"].strip(), form["address"].strip(), contact,
                               form["owner_name"].strip()])
            execute("""INSERT INTO users (role, full_name, username, password_hash, shop_id, security_question, security_answer_hash)
                       VALUES ('staff',%s,%s,%s,%s,%s,%s)""",
                    [form["owner_name"].strip(), username, generate_password_hash(password), shop_id,
                     form["security_question"], generate_password_hash(clean_answer(form["security_answer"]))])
            flash("Shop registered. Log in to set your services, rates and payments.")
            return redirect(url_for("auth.staff_login"))
    return render_template("auth/staff_register.html", errors=errors, form=form, question_options=QUESTION_OPTIONS)


def forgot_password(role):
    """Step 1: find the account.  Step 2: answer the security question, then choose a new password."""
    errors, user = {}, None
    if request.method == "POST":
        if "identifier" in request.form:  # ---- step 1
            ident = request.form["identifier"].replace(" ", "")
            # BINARY = exact match for shop usernames, same as the shop login ("FE.REYES" is not "fe.reyes")
            column = "mobile" if role == "customer" else "BINARY username"
            user = query(f"SELECT * FROM users WHERE role=%s AND {column}=%s", [role, ident], one=True)
            if not user or not user["security_question"]:
                user = None
                errors["identifier"] = "No account found. Check the spelling and try again."
            else:
                session["reset_uid"], session["reset_tries"] = user["id"], 0
        else:  # ---- step 2
            user = query("SELECT * FROM users WHERE id=%s AND role=%s", [session.get("reset_uid"), role], one=True)
            if not user:
                return redirect(request.path)
            password = request.form.get("new_password", "")
            if session.get("reset_tries", 0) >= MAX_RESET_TRIES:
                session.pop("reset_uid", None)
                user, errors["identifier"] = None, "Too many wrong answers. Start again."
            elif not check_password_hash(user["security_answer_hash"], clean_answer(request.form.get("answer", ""))):
                session["reset_tries"] = session.get("reset_tries", 0) + 1
                errors["answer"] = "That answer doesn't match."
            elif len(password) < 8:
                errors["new_password"] = "Use at least 8 characters."
            elif password != request.form.get("confirm_password"):
                errors["confirm_password"] = "Passwords don't match."
            else:
                execute("UPDATE users SET password_hash=%s WHERE id=%s", [generate_password_hash(password), user["id"]])
                session.pop("reset_uid", None)
                flash("Password changed. You can log in now.")
                return redirect(url_for("auth.login" if role == "customer" else "auth.staff_login"))
    return render_template("auth/forgot_password.html", role=role, user=user, errors=errors, form=request.form)


@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_customer():
    return forgot_password("customer")


@bp.route("/shop/forgot-password", methods=["GET", "POST"])
def forgot_staff():
    return forgot_password("staff")


@bp.route("/logout")
def logout():
    was_staff = g.user and g.user["role"] == "staff"
    session.clear()
    return redirect(url_for("auth.staff_login" if was_staff else "auth.login"))
