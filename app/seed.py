"""Sample data matching the Figma design (Mama Fe Laundry, Juan Dela Cruz, #DWG-00483...).

Demo accounts (password for all: password123)
  Customer: 09171234567   (Juan Dela Cruz)
  Staff:    fe.reyes      (Mama Fe Laundry)
            cf.staff      (Clean & Fresh)
            washhub       (Wash Hub)
"""
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

from .db import get_db

PASSWORD = "password123"


def seed():
    db = get_db()
    pw = generate_password_hash(PASSWORD)
    today = date.today()
    with db.cursor() as cur:
        shops = [
            # name, address, contact, owner, dropoff, pickup, delivery, fee, cash, gcash, gcash no, gcash name
            ("Mama Fe Laundry", "Mabini St., Balete", "0917 123 4567", "Fe Reyes", 1, 1, 1, 50, 1, 1, "0917 123 4567", "Fe Reyes"),
            ("Clean & Fresh", "Poblacion, Balete", "0918 555 0101", "Ana Cruz", 1, 1, 0, 0, 1, 1, "0918 555 0101", "Ana Cruz"),
            ("Wash Hub", "Brgy. San Juan, Balete", "0919 777 0202", "Ben Lim", 1, 0, 0, 0, 1, 0, None, None),
        ]
        cur.executemany(
            """INSERT INTO shops (name, address, contact_number, owner_name, offers_dropoff, offers_pickup,
               offers_delivery, delivery_fee, accepts_cash, accepts_gcash, gcash_number, gcash_name)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            shops,
        )
        services = []
        for shop_id in (1, 2, 3):
            services += [(shop_id, "Wash & Fold", 35, "kg"), (shop_id, "Wash, Dry & Fold", 50, "kg"),
                         (shop_id, "Comforter / Bedsheet", 150, "piece")]
        cur.executemany("INSERT INTO services (shop_id, name, rate, unit) VALUES (%s,%s,%s,%s)", services)

        cur.executemany(
            """INSERT INTO users (id, role, full_name, mobile, email, username, password_hash, address, shop_id)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            [
                (1, "customer", "Juan Dela Cruz", "09171234567", "juan@gmail.com", None, pw, "123 Mabini St., Balete", None),
                (2, "customer", "Maria Santos", "09181112222", "maria@gmail.com", None, pw, "45 Rizal St., Balete", None),
                (3, "customer", "Pedro Reyes", "09183334444", None, None, pw, "Poblacion, Balete", None),
                (4, "customer", "Carlo Mendoza", "09185556666", None, None, pw, "Brgy. San Juan, Balete", None),
                (10, "staff", "Fe Reyes", None, None, "fe.reyes", pw, None, 1),
                (11, "staff", "Ana Cruz", None, None, "cf.staff", pw, None, 2),
                (12, "staff", "Ben Lim", None, None, "washhub", pw, None, 3),
            ],
        )

        d = lambda days: today + timedelta(days=days)
        # id, code, customer, shop, service, rate, unit, handling, fee, est, actual, date, time,
        # confirmed, delivery, address, notes, status, reason, payment, method
        bookings = [
            (478, "DWG-00478", 4, 1, "Wash & Fold", 35, "kg", "drop-off", 0, 6, 6, d(-6), "9-11 AM", "9-11 AM", None, None, None, "Completed", None, "Paid", "cash"),
            (480, "DWG-00480", 3, 1, "Wash & Fold", 35, "kg", "drop-off", 0, 7, 7, d(-1), "8-10 AM", "8-10 AM", None, None, None, "Processing", None, "Unpaid", None),
            (481, "DWG-00481", 1, 2, "Wash & Fold", 35, "kg", "drop-off", 0, 7, 7, d(-1), "1-3 PM", "1-3 PM", None, None, None, "Processing", None, "Unpaid", None),
            (482, "DWG-00482", 2, 1, "Wash & Fold", 35, "kg", "pickup-delivery", 50, 3, 3.5, d(-2), "1-3 PM", "1-3 PM", "3-6 PM", "45 Rizal St., Balete", None, "Ready for Delivery", None, "Unpaid", None),
            (483, "DWG-00483", 1, 1, "Wash & Fold", 35, "kg", "pickup-delivery", 50, 3, None, d(0), "9-11 AM", "9-11 AM", None, "123 Mabini St., Balete", "Separate whites, no fabric softener", "Accepted", None, "Unpaid", None),
            (484, None, 1, 3, "Wash & Fold", 35, "kg", "drop-off", 0, 3, None, d(-3), "9-11 AM", None, None, None, None, "Rejected", "Fully booked on that day.", "Unpaid", None),
            (485, None, 1, 2, "Wash & Fold", 35, "kg", "drop-off", 0, 3, None, d(1), "9-11 AM", None, None, None, None, "Pending", None, "Unpaid", None),
            (486, None, 2, 1, "Wash & Fold", 35, "kg", "pickup-delivery", 50, 3, None, d(1), "1-3 PM", None, None, "45 Rizal St., Balete", None, "Pending", None, "Unpaid", None),
            (487, None, 3, 1, "Wash, Dry & Fold", 50, "kg", "drop-off", 0, 7, None, d(2), "8-10 AM", None, None, None, "Hang dry the polo shirts", "Pending", None, "Unpaid", None),
        ]
        cur.executemany(
            """INSERT INTO bookings (id, order_code, customer_id, shop_id, service_name, rate, unit, handling,
               delivery_fee, est_weight, actual_weight, requested_date, requested_time, confirmed_schedule,
               delivery_schedule, address, notes, status, reject_reason, payment_status, payment_method)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            bookings,
        )
        # next new booking gets id 488 -> DWG-00488
        cur.execute("ALTER TABLE bookings AUTO_INCREMENT = 488")

        cur.executemany(
            "INSERT INTO notifications (user_id, booking_id, kind, title, body, is_read) VALUES (%s,%s,%s,%s,%s,%s)",
            [
                (1, 483, "success", "Booking accepted", "#DWG-00483 · Pickup confirmed, 9-11 AM", 1),
                (1, 481, "info", "Your laundry is being processed", "#DWG-00481 · Final total ₱245.00 (7 kg)", 1),
                (1, 484, "error", "Booking not accepted", "Wash Hub · Fully booked on that day.", 0),
            ],
        )
    db.commit()
