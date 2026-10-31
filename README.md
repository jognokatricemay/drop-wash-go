# Drop, Wash, Go

A laundry booking and order-tracking web app for participating laundry shops.
It is built with **Python Flask + MySQL + HTML/CSS (Jinja templates) + a little JavaScript**.
The same website works on PC and phone, because the layout is responsive.

```
Drop, Wash, Go/
├── app/
│   ├── __init__.py        creates the Flask app, registers the blueprints
│   ├── db.py              MySQL connection + query() / execute() helpers + `init-db` command
│   ├── schema.sql         tables: shops, users, services, bookings, notifications
│   ├── seed.py            sample data that matches the Figma design
│   ├── helpers.py         login checks, prices, template filters (peso, pill, ...)
│   ├── auth.py            welcome, login, sign up, shop register / login, logout   (Member 1)
│   ├── customer.py        shops, booking, my orders, notifications, profile        (Members 3, 4)
│   ├── staff.py           dashboard, requests, orders, weight, status, paid, shop info (Members 5, 6)
│   ├── templates/         base.html (sidebar + bottom nav), _macros.html, auth/, customer/, staff/
│   └── static/            css/style.css, js/app.js
├── tests/smoke_test.py    opens every page and runs the whole booking flow (55 checks)
├── web/                   the original static HTML mockup (reference only)
├── run.py                 starts the app locally
└── requirements.txt
```

## 1. Run it on your laptop

You need **Python 3.10+** and **XAMPP** (for MySQL).

1. Open XAMPP and **Start MySQL**.
2. In a terminal, inside the project folder:

```bash
python -m venv .venv
```

```bash
.venv\Scripts\activate
```

```bash
pip install -r requirements.txt
```

```bash
copy .env.example .env
```

```bash
flask --app app init-db
```

```bash
python run.py
```

3. Open **http://localhost:5000**. To test on your phone, connect it to the same Wi-Fi and run `flask --app app run --host=0.0.0.0`, then open `http://<your-laptop-IP>:5000`.

`flask --app app init-db` **deletes everything** and loads the sample data again. Run it whenever you change `schema.sql` or want a clean demo.

### Demo accounts (password: `password123`)

| Role | Log in with |
|---|---|
| Customer (Juan Dela Cruz) | mobile `09171234567` |
| Shop staff (Mama Fe Laundry) | username `fe.reyes` |
| Shop staff (Clean & Fresh) | username `cf.staff` |
| Shop staff (Wash Hub, drop-off only) | username `washhub` |

### Check that nothing is broken

```bash
python tests/smoke_test.py
```

Run this before every pull request. It resets the database to the sample data.

## 2. How the app works

- **Booking → Order.** A customer submits a booking, and it is saved as `Pending`. When the shop **accepts** it, the app creates the Order ID (`DWG-00488`, …) (FR-05). If the shop rejects it, the customer sees the reason.
- **Prices.** `rate × weight` + delivery fee (Pickup & Delivery only). The estimate uses the customer's weight. After **Confirm weight**, the actual weight is used. Rates and fees are copied into the booking, so changing Shop info only affects new bookings.
- **Payment** happens outside the app (cash or GCash to the shop). Staff only record it with **Mark as paid**.
- **Notifications** are created when a booking is accepted or rejected, the weight is confirmed, or the status changes.
- **Roles.** `@login_required("customer")` / `@login_required("staff")` protect every page. Staff only see their own shop's bookings.

## 3. Deploy for free on PythonAnywhere

1. Make a free account at pythonanywhere.com. Your site will be `yourname.pythonanywhere.com`.
2. **Databases** tab → set a MySQL password → note the host (`yourname.mysql.pythonanywhere-services.com`) and the database name (`yourname$default`).
3. **Consoles** → Bash:

```bash
git clone https://github.com/<your-team>/<repo>.git dropwashgo
```

```bash
cd dropwashgo && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

4. Create `.env` in that folder (`nano .env`):

```
SECRET_KEY=<any long random text>
DB_HOST=yourname.mysql.pythonanywhere-services.com
DB_USER=yourname
DB_PASSWORD=<the MySQL password you set>
DB_NAME=yourname$default
```

5. Run `flask --app app init-db`. The database already exists on PythonAnywhere, and the command only creates the tables.
6. **Web** tab → *Add a new web app* → *Manual configuration* → choose the same Python version.
   - **Virtualenv:** `/home/yourname/dropwashgo/.venv`
   - **WSGI file:** replace its contents with:

```python
import sys
path = "/home/yourname/dropwashgo"
if path not in sys.path:
    sys.path.insert(0, path)
from dotenv import load_dotenv
load_dotenv(path + "/.env")
from app import create_app
application = create_app()
```

   - **Static files:** URL `/static/` → directory `/home/yourname/dropwashgo/app/static`
7. Click **Reload**.
8. **To update the site later:** `git pull` in the console, then **Reload** in the Web tab.
9. Free sites stop after 3 months unless you click **"Run until 3 months from today"** on the Web tab, so check it before the presentation.

## 4. Who does what (6 members)

Each part has its own Python file and template folder, so you rarely edit the same file.
Only **Member 1** changes `app/__init__.py`, `base.html` and `helpers.py`; ask them first.

| # | Part | Files | Still to do |
|---|---|---|---|
| 1 | Lead: setup, login, deploy | `auth.py`, `templates/auth/`, `base.html` | GitHub repo + branch rules, deploy to PythonAnywhere on day 1 and after every merge, "forgot password" note, PWA (add-to-home-screen icon) |
| 2 | Database + testing | `schema.sql`, `seed.py`, `db.py`, `tests/` | More realistic sample data, run the smoke test on every pull request, test on real phones, write the test results for the paper |
| 3 | Customer: booking | `customer.py` (shops → request sent), `templates/customer/shops, shop_details, book, review, request_sent` | Server-side shop search/filter, block booking past closing time, clearer messages |
| 4 | Customer: tracking | `customer.py` (home, orders, notifications, profile), `templates/customer/...` | **Edit personal info**, **saved address** pages, cancel a Pending booking |
| 5 | Staff: bookings | `staff.py` (dashboard, requests, accept/reject), `templates/staff/dashboard, requests, booking_details, booking_accepted` | Change the requested date (not just time), show today's pickups on the dashboard |
| 6 | Staff: orders + shop | `staff.py` (orders, weight, status, paid, shop info, profile), `templates/staff/...` | **"+ Add service"** form, **change password**, remove a service |

Search the code for `TODO (Member N)` to find each person's spots.

### Git rules
- Make one branch per person (`member3-booking`, …), and never work directly on `main`.
- Commit small and often. Open a **pull request**, and let one other member review it before merging.
- Pull `main` every morning so your branch doesn't drift.

## 5. Notes
- Never put passwords in the code. They go in `.env`, which is ignored by git.
- Always use `query("... WHERE id=%s", [value])`. Never build SQL with f-strings and user input.
- VS Code: `.vscode/settings.json` turns off auto-format for templates, because Prettier breaks Jinja tags.
