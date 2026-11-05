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
            ("Mary's Laundromat", "172 Leviste Hwy, Balete", "0905 223 4412", "Mary Magsaysay", 1, 1, 0, 0, 1, 1, "0905 223 4412", "Mary Magsaysay"),
            ("Clean Queen Laundry", "Bagumbayan Rd, Balete", "0917 888 3344", "Queen Santos", 1, 1, 1, 75, 1, 1, "0917 888 3344", "Queen Santos"),
            ("Wash Express", "Brgy. Magapi, Balete", "0913 582 0081", "Jerry Manaluan", 1, 1, 1, 85, 1, 0, None, None)
        ]
        cur.executemany(
            """INSERT INTO shops (name, address, contact_number, owner_name, offers_dropoff, offers_pickup,
               offers_delivery, delivery_fee, accepts_cash, accepts_gcash, gcash_number, gcash_name)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            shops,
        )
        services = []
        for shop_id in (1, 2, 3, 4, 5, 6):
            services += [(shop_id, "Wash & Fold", 35, "kg"), (shop_id, "Wash, Dry & Fold", 50, "kg"),
                        (shop_id, "Comforter / Bedsheet", 150, "piece")]
            # Dry Clean is only offered by Mary's Laundromat (shop 4) and Wash Express (shop 6)
            services += [(4, "Dry Clean", 120, "piece"), (6, "Dry Clean", 120, "piece")]
        cur.executemany("INSERT INTO services (shop_id, name, rate, unit) VALUES (%s,%s,%s,%s)", services)

        cur.executemany(
            """INSERT INTO users (id, role, full_name, mobile, email, username, password_hash, address, shop_id)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            [
                (1, "customer", "Juan Dela Cruz", "09171234567", "juan@gmail.com", None, pw, "123 Mabini St., Balete", None),
                (2, "customer", "Maria Santos", "09181112222", "maria@gmail.com", None, pw, "45 Rizal St., Balete", None),
                (3, "customer", "Pedro Reyes", "09183334444", None, None, pw, "Poblacion, Balete", None),
                (4, "customer", "Carlo Mendoza", "09185556666", None, None, pw, "Brgy. San Juan, Balete", None),
                (5, "customer", "Annie Recaldo", "09187628028", None, None, pw, "Brgy. Magapi, Balete", None),
                (6, "customer", "John Dela Cueva", "09189990000", None, None, pw, "Brgy. Bagumbayan, Balete", None),
                (7, "customer", "Bob Manuan", "09110642312", None, None, pw, "Leviste, Balete", None),
                (8, "customer", "Christian Cait", "09227623112", None, None, pw, "Brgy. Makina, Balete", None),
                (9, "customer", "Luis Manaupa", "09289910932", None, None, pw, "Kinalaglagan, Balete", None),
                (10, "staff", "Fe Reyes", None, None, "fe.reyes", pw, None, 1),
                (11, "staff", "Ana Cruz", None, None, "cf.staff", pw, None, 2),
                (12, "staff", "Ben Lim", None, None, "washhub", pw, None, 3),
                (13, "staff", "Grace Manaimtim", None, None, "grace.manaimtim", pw, None, 4),
                (14, "staff", "Dominic Reyes", None, None, "dominic.reyes", pw, None, 5),
                (15, "staff", "Sofia Garcia", None, None, "sofia.garcia", pw, None, 6),
            ],
        )

        # Demo security question for every account, so "Forgot password?" can be tried
        cur.execute("UPDATE users SET security_question=%s, security_answer_hash=%s",
                    ["What is your favorite food?", generate_password_hash("adobo")])

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
            (488, "MYL-00488", 2, 4, "Wash, Dry & Fold", 50, "kg", "drop-off", 0, 7, 7, d(-4), "11-12 PM", "2-5 PM", None, None, None, "Completed", None, "Paid", "gcash"),
            (489, "MYL-00489", 4, 4, "Dry Clean", 120, "piece", "drop-off", 0, 3, 3, d(-3), "10-12 PM", "10-12 PM", None, None, "Handle with care - suit jacket", "Completed", None, "Paid", "cash"),
            (490, "CQL-00490", 1, 5, "Wash & Fold", 35, "kg", "pickup-delivery", 50, 4, 4, d(-2), "9-11 AM", "9-11 AM", "2-5 PM", "153 Mabini St., Balete", None, "Completed", None, "Paid", "gcash"),
            (491, "WE-00491", 3, 6, "Comforter / Bedding", 150, "piece", "drop-off", 0, 5, 5, d(-2), "3-4 PM", "11-1 PM", None, None, "Use hypoallergenic detergent", "Completed", None, "Paid", "cash"),
            (492, "CQL-00492", 2, 5, "Wash & Fold", 35, "kg", "pickup-delivery", 50, 3, 3, d(-1), "9-11 AM", "8-10 AM", "1-4 PM", "45 Rizal St., Balete", None, "Ready for Delivery", None, "Paid", "gcash"),
            (493, "WE-00493", 4, 6, "Wash, Dry & Fold", 50, "kg", "drop-off", 0, 6, 6, d(-1), "11-1 AM", "11-1 AM", None, None, None, "Processing", None, "Unpaid", None),
            (494, "WE-00494", 1, 6, "Dry Clean", 120, "piece", "pickup-delivery", 60, 4, 4, d(0), "1-3 PM", "1-3 PM", "5-7 PM", "172 Mabini St., Balete", "Press pleats on skirt", "Ready for Delivery", None, "Unpaid", None),
            (495, "CQL-00495", 3, 5, "Wash & Fold", 35, "kg", "drop-off", 0, 3, None, d(0), "9-11 AM", "9-11 AM", None, None, None, "Accepted", None, "Unpaid", None),
            (496, "WE-00496", 2, 6, "Wash, Dry & Fold", 50, "kg", "pickup-delivery", 50, 4, None, d(0), "2-4 PM", "2-4 PM", None, "45 Rizal St., Balete", "No fabric softener please", "Accepted", None, "Unpaid", None),
            (497, "MYL-00497", 4, 4, "Comforter / Bedding", 150, "piece", "drop-off", 0, 5, None, d(1), "11-1 PM", None, None, None, None, "Pending", None, "Unpaid", None),
            (498, "MYL-00498", 1, 4, "Wash & Fold", 35, "kg", "pickup", 0, 3, None, d(1), "9-11 AM", None, None, "23 Mabini St., Balete", None, "Pending", None, "Unpaid", None),
            (499, "MYL-00499", 3, 4, "Dry Clean", 120, "piece", "drop-off", 0, 4, None, d(2), "1-3 PM", None, None, None, "Winter coat - dry clean only", "Pending", None, "Unpaid", None),
            (500, "CQL-00500", 2, 5, "Wash & Fold", 35, "kg", "drop-off", 0, 3, None, d(2), "3-5 PM", None, None, None, None, "Pending", None, "Unpaid", None),
            (501, "WE-00501", 4, 6, "Wash, Dry & Fold", 50, "kg", "pickup-delivery", 50, 4, None, d(3), "9-11 AM", None, None, "789 Laurel St., Tanauan", "Separate dark colors", "Pending", None, "Unpaid", None),
            (502, None, 1, 4, "Comforter / Bedding", 150, "piece", "drop-off", 0, 5, None, d(3), "3-5 PM", None, None, None, None, "Pending", None, "Unpaid", None),
        ]
        cur.executemany(
            """INSERT INTO bookings (id, order_code, customer_id, shop_id, service_name, rate, unit, handling,
               delivery_fee, est_weight, actual_weight, requested_date, requested_time, confirmed_schedule,
               delivery_schedule, address, notes, status, reject_reason, payment_status, payment_method)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            bookings,
        )
        # next new booking gets id 503 -> DWG-00503
        cur.execute("ALTER TABLE bookings AUTO_INCREMENT = 503")

        cur.executemany(
            "INSERT INTO notifications (user_id, booking_id, kind, title, body, is_read) VALUES (%s,%s,%s,%s,%s,%s)",
            [
                (1, 483, "success", "Booking accepted", "#DWG-00483 · Pickup confirmed, 9-11 AM", 1),
                (1, 481, "info", "Your laundry is being processed", "#DWG-00481 · Final total ₱245.00 (7 kg)", 1),
                (1, 484, "error", "Booking not accepted", "Wash Hub · Fully booked on that day.", 0),
                (1, 488, "success", "Booking accepted", "#MYL-00488 · Pick-up confirmed, 11-12 PM", 1),
                (1, 491, "success", "Booking accepted", "#WE-00491 · Pick-up confirmed, 2-4 PM", 1),
                
            ],
        )
    db.commit()
