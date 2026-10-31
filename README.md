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

## 3. Deploy for free: Render (website) + Aiven (MySQL)

Free PythonAnywhere accounts no longer include MySQL, so the site runs on **Render** and the database on **Aiven**. Both are free, and you can sign up with GitHub.
The link will be **https://dropwashgo.onrender.com** (if the name is free).

### A. Database on Aiven
1. Go to **aiven.io** → sign up → **Create service** → **MySQL** → choose the **Free** plan → **Create**.
2. Wait until the service says **Running**. In **Overview → Connection information**, note the **Host**, **Port**, **User** (`avnadmin`) and **Password**.
3. Download the **CA certificate** (`ca.pem`) from the same page. Keep it; you'll paste its text into Render.

### B. Website on Render
1. Push the latest code to GitHub. It must include `render.yaml`.
2. Go to **render.com** → sign up with GitHub → **New** → **Blueprint** → pick the `drop-wash-go` repo.
3. Render reads `render.yaml` and asks for these values (copy them from Aiven):

| Key | Value |
|---|---|
| `DB_HOST` | Aiven host, e.g. `mysql-xxxx.aivencloud.com` |
| `DB_PORT` | Aiven port, e.g. `12345` (not 3306) |
| `DB_USER` | `avnadmin` |
| `DB_PASSWORD` | Aiven password |
| `DB_SSL_CA` | open `ca.pem` in Notepad and paste **all** of its text |

4. Click **Apply**. The first deploy takes a few minutes.
   - On first start, the app sees the empty database and **creates the tables and sample data by itself** (`AUTO_INIT_DB=1`).
   - Later deploys keep the data.
5. Open **https://dropwashgo.onrender.com**. Render shows your exact link at the top of the service page.

### Updating the live site
Every merge to `main` on GitHub **deploys automatically**. Watch it in Render → **Events**.

### Good to know
- **The free site sleeps** after 15 minutes without visitors. The first visit after that takes about a minute to load. **Open the site 5 minutes before the presentation.**
- **To reset the live data to the sample data**, run `init-db` from your laptop with the Aiven values set for that terminal only (PowerShell):

```powershell
$env:DB_HOST="mysql-xxxx.aivencloud.com"; $env:DB_PORT="12345"; $env:DB_USER="avnadmin"; $env:DB_PASSWORD="..."; $env:DB_SSL="1"; $env:DB_SSL_CA="C:\Users\you\Downloads\ca.pem"; flask --app app init-db
```

  Close that terminal afterwards, so you don't accidentally wipe the live database later.
- **Never commit the Aiven password or `ca.pem` to GitHub.** They only go into Render's environment settings.

## 4. Who does what (6 members)

Each part has its own Python file and template folder, so you rarely edit the same file.
Only **Member 1** changes `app/__init__.py`, `base.html` and `helpers.py`; ask them first.

| # | Part | Files | Still to do |
|---|---|---|---|
| 1 | Lead: setup, login, deploy | `auth.py`, `templates/auth/`, `base.html` | GitHub repo + branch rules, deploy to Render + Aiven on day 1 (then it auto-deploys on every merge), "forgot password" note, PWA (add-to-home-screen icon) |
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
