"""Quick check that every page opens and the main flow works.

Run:  python tests/smoke_test.py
WARNING: this resets the database to the sample data first (same as `flask --app app init-db`).
"""
import re
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app  # noqa: E402
from app.db import init_db_command, query  # noqa: E402
from app.helpers import schedule_label, time_input_value, time_label  # noqa: E402
from app.staff import order_code  # noqa: E402

app = create_app()
app.config["TESTING"] = True
failures = []


def check(label, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + label + (f"  ({detail})" if detail and not ok else ""))
    if not ok:
        failures.append(label)


check("shop-based order ID prefixes",
      [order_code(name, 12) for name in ("Clean & Fresh", "Mama Fe Laundry", "Wash Hub")] ==
      ["CNF-00012", "MFL-00012", "WH-00012"])
check("time picker handles current and legacy values",
      [time_input_value(value) for value in ("13:30", "9-11 AM", "1-3 PM")] ==
      ["13:30", "09:00", "13:00"] and time_label("13:30") == "1:30 PM")
check("delivery schedule date and time formatting",
      schedule_label("2026-11-04T15:30") == "Nov 4 · 3:30 PM"
      and schedule_label("Tomorrow · 3-6 PM") == "Tomorrow · 3-6 PM")


def get(client, url, expect=200, contains=None):
    r = client.get(url)
    ok = r.status_code == expect and (contains is None or contains in r.get_data(as_text=True))
    check(f"GET {url}", ok, f"status {r.status_code}")
    return r


with app.app_context():
    app.test_cli_runner().invoke(init_db_command)

guest = app.test_client()
get(guest, "/", contains="How will you use")
get(guest, "/login", contains="Welcome back")
get(guest, "/create-account", contains="Create your account")
get(guest, "/shop/login", contains="Shop login")
get(guest, "/shop/register", contains="Register your shop")
get(guest, "/shops", contains="browsing as a guest")
get(guest, "/shops/1", contains="Mama Fe Laundry")
r = guest.get("/shops/1/book")
check("guest booking asks to log in", r.status_code == 302 and "/login" in r.headers["Location"])
get(guest, "/login?next=/shops/1/book", contains="Log in to book")
check("customer page blocked for guest", guest.get("/orders").status_code == 302)

# ---------- customer ----------
c = app.test_client()
r = c.post("/login", data={"mobile": "09171234567", "password": "wrong"})
check("wrong password rejected", "Wrong mobile number or password" in r.get_data(as_text=True))
r = c.post("/login", data={"mobile": "0917 123 4567", "password": "password123"})
check("customer login", r.status_code == 302 and r.headers["Location"].endswith("/home"))
check("unread notification dot shown in navigation",
      "nav-unread-dot" in c.get("/home").get_data(as_text=True))
for url, text in [("/home", "Hi, Juan"), ("/shops", "Wash Hub"), ("/shops/3", "No pickup"), ("/shops/1/book", "Review booking"),
                  ("/shops/3/book", "only offers drop-off"), ("/orders", "#DWG-00483"), ("/orders?tab=past", "Booking request"),
                  ("/orders/483", "Pay on delivery"), ("/orders/484", "could not accept"), ("/notifications", "Booking accepted"),
                  ("/profile", "Juan Dela Cruz")]:
    get(c, url, contains=text)
check("customer can't open staff pages", c.get("/shop/dashboard").status_code == 302)
check("customer can't open other's order", c.get("/orders/482").status_code == 302)  # 404 -> redirect home

r = c.post("/shops/1/book", data={"service_id": "1", "handling": "pickup-delivery", "est_weight": "", "requested_date": "",
                                  "requested_time": "", "address": ""})
html = r.get_data(as_text=True)
check("booking validation errors shown", "Please fix 4 fields" in html, re.findall(r"Please fix \d+ \w+", html))
tomorrow = (date.today() + timedelta(days=1)).isoformat()
r = c.post("/shops/1/book", data={"service_id": "1", "handling": "pickup-delivery", "est_weight": "4", "requested_date": tomorrow,
                                  "requested_time": "13:30", "address": "123 Mabini St., Balete", "notes": "No softener"})
check("valid booking goes to review", r.status_code == 302 and r.headers["Location"].endswith("/book/review"))
get(c, "/book/review", contains="₱190")  # 35 x 4 + 50
r = c.post("/book/review")
check("booking submitted", r.status_code == 302 and "/book/sent/" in r.headers["Location"])
new_id = int(r.headers["Location"].rsplit("/", 1)[1])
get(c, f"/book/sent/{new_id}", contains="Request sent")
r = c.post("/shops/3/book", data={"service_id": "7", "handling": "pickup", "est_weight": "3", "requested_date": tomorrow,
                                  "requested_time": "09:00", "address": "x"})
check("unsupported handling rejected (FR-11)", "offer that option" in r.get_data(as_text=True))

# ---------- staff ----------
s = app.test_client()
r = s.post("/shop/login", data={"username": "fe.reyes", "password": "password123"})
check("staff login", r.status_code == 302 and r.headers["Location"].endswith("/shop/dashboard"))
for url, text in [("/shop/dashboard", "Needs attention"), ("/shop/requests", "Juan Dela Cruz"), ("/shop/requests?tab=Rejected", None),
                  ("/shop/orders", "#DWG-00482"), ("/shop/orders?q=Maria", "Maria Santos"), ("/shop/orders/483", "Confirm weight"),
                  ("/shop/orders/482/status", "Ready for Delivery"), ("/shop/orders/482/paid", "Amount due"),
                  ("/shop/profile", "Mama Fe Laundry"), ("/shop/shop-info", "Save changes")]:
    get(s, url, contains=text)
get(s, "/shop/dashboard", contains="Pickups today")
pickup_page = get(s, "/shop/pickups/today", contains="Juan Dela Cruz").get_data(as_text=True)
check("pickup details are scoped to this shop", "123 Mabini St." in pickup_page
      and "#DWG-00482" not in pickup_page)
for username in ("cf.staff", "washhub"):
    shop_staff = app.test_client()
    shop_staff.post("/shop/login", data={"username": username, "password": "password123"})
    dashboard = shop_staff.get("/shop/dashboard").get_data(as_text=True)
    check(f"{username} has a shop-specific pickup counter", "Pickups today" in dashboard)
    check(f"{username} sees only their own today's pickups",
          "Juan Dela Cruz" not in shop_staff.get("/shop/pickups/today").get_data(as_text=True))
get(s, "/shop/requests/486", contains='name="confirmed_schedule" type="time"')
check("staff can't see other shop's booking", s.get("/shop/orders/481").status_code == 302)

r = s.post(f"/shop/requests/{new_id}", data={"action": "accept", "confirmed_schedule": "14:00"})
check("accept booking", r.status_code == 302 and r.headers["Location"].endswith(f"/requests/{new_id}/accepted"))
code = f"MFL-{new_id:05d}"
get(s, f"/shop/requests/{new_id}/accepted", contains=code)
get(c, f"/orders/{new_id}", contains="2:00 PM")
r = s.post("/shop/requests/486", data={"action": "reject", "reason": ""})
check("reject needs a reason", "Give the customer a reason" in r.get_data(as_text=True))
r = s.post("/shop/requests/486", data={"action": "reject", "reason": "Fully booked"})
check("reject booking", r.status_code == 302)

r = s.post(f"/shop/orders/{new_id}/weight", data={"actual_weight": "4.5"}, follow_redirects=True)
check("confirm weight -> processing", "Processing" in r.get_data(as_text=True) and "₱207.50" in r.get_data(as_text=True))
r = s.post(f"/shop/orders/{new_id}/status", data={"status": "Ready for Delivery", "delivery_date": tomorrow,
                                                 "delivery_time": "15:30"}, follow_redirects=True)
check("update status", "is now Ready for Delivery" in r.get_data(as_text=True))
check("customer sees delivery date and time", "3:30 PM" in c.get(f"/orders/{new_id}").get_data(as_text=True))
r = s.post(f"/shop/orders/{new_id}/paid", data={"method": "cash", "amount_received": "100"})
check("paid amount too small rejected", "less than" in r.get_data(as_text=True))
r = s.post(f"/shop/orders/{new_id}/paid", data={"method": "cash", "amount_received": "250"}, follow_redirects=True)
check("mark as paid", "marked as paid" in r.get_data(as_text=True))
r = s.post("/shop/shop-info", data={"name": "Mama Fe Laundry", "contact_number": "0917 123 4567", "address": "Mabini St., Balete",
                                    "opening_hours": "8:00 AM - 8:00 PM", "offers_dropoff": "1", "offers_delivery": "1",
                                    "delivery_fee": "60", "accepts_cash": "1", "rate_1": "35", "next": "/shop/orders"})
check("shop info saved and goes to next page", r.status_code == 302 and r.headers["Location"].endswith("/shop/orders"))

# customer sees the updates
r = c.get(f"/orders/{new_id}")
html = r.get_data(as_text=True)
check("customer sees order ID, status and paid", code in html and "Ready for Delivery" in html and "Paid" in html)
get(c, "/notifications", contains="Your laundry is being processed")

# ---- forgot password (customer + shop), by security question
get(guest, "/forgot-password", contains="Reset your password")
get(guest, "/shop/forgot-password", contains="Reset your password")
get(guest, "/login", contains="Forgot password?")
get(guest, "/shop/login", contains="Forgot password?")

fp = app.test_client()
r = fp.post("/forgot-password", data={"identifier": "09999999999"})
check("forgot: unknown number is refused", "No account found" in r.get_data(as_text=True))
r = fp.post("/forgot-password", data={"identifier": "0917 123 4567"})
check("forgot: shows the security question", "What is your favorite food?" in r.get_data(as_text=True))
r = fp.post("/forgot-password", data={"answer": "pizza", "new_password": "newpass123", "confirm_password": "newpass123"})
check("forgot: wrong answer is refused", "doesn" in r.get_data(as_text=True) and "match" in r.get_data(as_text=True))
r = fp.post("/forgot-password", data={"answer": "adobo", "new_password": "short", "confirm_password": "short"})
check("forgot: short password is refused", "at least 8" in r.get_data(as_text=True))
r = fp.post("/forgot-password", data={"answer": " ADOBO ", "new_password": "newpass123", "confirm_password": "newpass123"})
check("forgot: right answer (any case) changes the password", r.status_code == 302 and r.headers["Location"].endswith("/login"))
r = app.test_client().post("/login", data={"mobile": "09171234567", "password": "newpass123"})
check("forgot: can log in with the new password", r.status_code == 302 and r.headers["Location"].endswith("/home"))
r = app.test_client().post("/login", data={"mobile": "09171234567", "password": "password123"})
check("forgot: old password no longer works", r.status_code == 200)

fs = app.test_client()
r = app.test_client().post("/shop/forgot-password", data={"identifier": "FE.REYES"})
check("forgot (shop): username is case-sensitive", "No account found" in r.get_data(as_text=True))
r = fs.post("/shop/forgot-password", data={"identifier": "fe.reyes"})
check("forgot (shop): shows the security question", "What is your favorite food?" in r.get_data(as_text=True))
r = fs.post("/shop/forgot-password", data={"answer": "adobo", "new_password": "shoppass123", "confirm_password": "shoppass123"})
check("forgot (shop): changes the password", r.status_code == 302 and r.headers["Location"].endswith("/shop/login"))
r = app.test_client().post("/shop/login", data={"username": "fe.reyes", "password": "shoppass123"})
check("forgot (shop): can log in with the new password", r.status_code == 302)

# a customer id can't be used on the shop page (and the other way around)
fx = app.test_client()
fx.post("/forgot-password", data={"identifier": "09181112222"})
r = fx.post("/shop/forgot-password", data={"answer": "adobo", "new_password": "hacked1234", "confirm_password": "hacked1234"})
check("forgot: customer session can't reset on the shop page", r.status_code == 302 and "/shop/forgot-password" in r.headers["Location"])

# too many wrong answers locks that attempt
fl = app.test_client()
fl.post("/forgot-password", data={"identifier": "09181112222"})
for _ in range(5):
    fl.post("/forgot-password", data={"answer": "wrong", "new_password": "x", "confirm_password": "x"})
r = fl.post("/forgot-password", data={"answer": "adobo", "new_password": "letmein123", "confirm_password": "letmein123"})
check("forgot: locked after 5 wrong answers", "Too many wrong answers" in r.get_data(as_text=True))

# sign-up now asks for a security question
r = app.test_client().post("/create-account", data={"full_name": "Ana Test", "mobile": "09170001111", "password": "password123",
                                                    "confirm_password": "password123"})
check("sign-up: security question is required", "Choose a security question" in r.get_data(as_text=True))
nc = app.test_client()
r = nc.post("/create-account", data={"full_name": "Ana Test", "mobile": "09170001111", "password": "password123",
                                     "confirm_password": "password123", "security_question": "What town were you born in?",
                                     "security_answer": "Balete"})
check("sign-up: works with a security question", r.status_code == 302)
r = app.test_client().post("/forgot-password", data={"identifier": "09170001111"})
check("sign-up: new account can use forgot password", "What town were you born in?" in r.get_data(as_text=True))
r = app.test_client().post("/shop/register", data={"shop_name": "Test Shop", "contact_number": "09170002222", "address": "Somewhere",
                                                   "owner_name": "Owner", "username": "test.shop", "password": "password123",
                                                   "confirm_password": "password123"})
check("shop register: security question is required", "Choose a security question" in r.get_data(as_text=True))

with app.app_context():
    shop = query("SELECT offers_pickup, delivery_fee FROM shops WHERE id=1", one=True)
    check("shop info toggles saved", shop["offers_pickup"] == 0 and shop["delivery_fee"] == 60)
    app.test_cli_runner().invoke(init_db_command)  # back to the sample data

print(f"\n{len(failures)} failed" if failures else "\nAll checks passed.")
sys.exit(1 if failures else 0)
