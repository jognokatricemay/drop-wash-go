# Drop, Wash, Go

A web-based laundry booking and order-tracking system for participating local laundry shops.
Customers browse shops, book (drop-off, pick-up, or pick-up and delivery), and track their order.
Shop staff accept or reject bookings, confirm schedules and weight, update the order status one step at a time, and record payment.

Built with **Python Flask + MySQL + HTML/CSS (Jinja templates) + a little JavaScript**.
The same website works on a phone and on a PC, because the layout is responsive.

- **Live site:** https://YOUR-PROJECT.vercel.app *(replace with your Vercel link)*
- **Course:** CSSE101 Software Engineering 1, BS Computer Science, Faith Colleges (BSCS 3A, Group 4)

```
Drop, Wash, Go/
├── app/
│   ├── __init__.py        creates the Flask app, registers the blueprints
│   ├── db.py              MySQL connection + query() / execute() helpers + `init-db` command
│   ├── schema.sql         tables: shops, users, services, bookings, notifications
│   ├── seed.py            sample data (6 shops, 15 accounts, 30 services, 24 bookings)
│   ├── helpers.py         login checks, prices, notifications, template filters
│   ├── auth.py            landing page, login, sign up, shop register / login, logout
│   ├── customer.py        shops, booking, my orders, notifications, profile
│   ├── staff.py           dashboard, requests, orders, weight, status, paid, notifications, shop info
│   ├── templates/         base.html (sidebar + bottom nav), _macros.html, auth/, customer/, staff/
│   └── static/            css/style.css, css/landing.css, js/app.js
├── index.py               entry point that Vercel runs (it just loads the Flask app)
├── tests/smoke_test.py    opens every page and runs the whole booking flow (183 checks)
├── web/                   the first static HTML/CSS pages made from the Figma design (reference only)
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

Staff log in at `/shop/login`. These accounts hold sample data only; no real personal information.

### Check that nothing is broken

```bash
python tests/smoke_test.py
```

Run this before every pull request. It **resets the database to the sample data**, so never point it at the live database.

## 2. How the app works

- **Booking → Order.** A customer chooses a handling option, a date, and a time, then submits a booking that is saved as `Pending`. When the shop **accepts** it, the app creates a shop-prefixed Order ID (for example `MFL-00488` or `WH-00490`). If the shop rejects it, the customer sees the reason.
- **Status flow.** Staff move an order one step at a time: Accepted → Processing → Ready for Pickup / Ready for Delivery → Completed. They cannot skip a step or go back.
- **Cancelling.** A customer can cancel while the booking is Pending or Accepted, but not after processing starts.
- **Prices.** `rate × weight` + delivery fee (pick-up and delivery only). The estimate uses the customer's weight; after **Confirm weight**, the actual weight is used. Rates and fees are copied into the booking, so changing Shop info only affects new bookings.
- **Payment** happens outside the app (cash or GCash to the shop). Staff only record it with **Mark as paid**, and only after the order is accepted and weighed.
- **Notifications** (in-app only) are created for new requests, cancellations, accepted or rejected bookings, confirmed weight, and status changes.
- **Roles.** `@login_required("customer")` / `@login_required("staff")` protect every page. Staff only see their own shop's bookings.
- **Time zone.** The server runs in UTC, so all booking date and time checks use Philippine time (UTC+8).

## 3. Deploy for free: Vercel (website) + Aiven (MySQL)

The website runs on **Vercel** and the database on **Aiven**. Vercel only hosts the website, so the MySQL database stays on Aiven. Both have free plans, and you can sign up with GitHub.

### A. Database on Aiven (skip this if you already have one)
1. Go to **aiven.io** → sign up → **Create service** → **MySQL** → choose the **Free** plan → **Create**.
2. Wait until the service says **Running**. In **Overview → Connection information**, note the **Host**, **Port**, **User** (`avnadmin`) and **Password**.
3. Download the **CA certificate** (`ca.pem`) from the same page. Keep it; you'll paste its text into Vercel.
4. The tables and sample data are created by running `init-db` once from your laptop (see "Reset the live data" below).

### B. Website on Vercel
1. Push the latest code to GitHub. It must include `index.py` (it exposes the Flask `app` that Vercel runs).
2. Go to **vercel.com** → sign up with GitHub → **Add New… → Project** → import the `drop-wash-go` repo.
3. **Framework Preset:** `Flask`. Leave the build and output settings empty.
4. Open **Environment Variables** and add these (copy the database values from Aiven). Tick **Production** and **Preview**.

| Key | Value |
|---|---|
| `SECRET_KEY` | any long random text (for example 40 random characters) |
| `DB_HOST` | Aiven host, e.g. `mysql-xxxx.aivencloud.com` |
| `DB_PORT` | Aiven port, e.g. `12345` (not 3306) |
| `DB_USER` | `avnadmin` |
| `DB_PASSWORD` | Aiven password |
| `DB_NAME` | `dropwashgo` |
| `DB_SSL` | `1` |
| `DB_SSL_CA` | open `ca.pem` in Notepad and paste **all** of its text |

   Do **not** add `AUTO_INIT_DB`. The database already has its tables, and a serverless site should not try to create them.

5. Click **Deploy**. When it finishes, Vercel shows your link (`https://<project>.vercel.app`). Put that link at the top of this README.

### Updating the live site
Every push or merge to `main` on GitHub **deploys automatically**. Watch it in Vercel → **Deployments**. Every pull request also gets its own preview link.

### Good to know
- **Vercel runs the app as a serverless function.** There is no "sleeping for a minute" like on Render, but the first visit after a quiet period can be a bit slower (cold start). Open the site a few minutes before the presentation.
- **Region.** In Vercel → **Settings → Functions → Function Region**, pick the region closest to your Aiven database. A far region makes every page slower.
- **Connection limit.** Each running copy of the site opens its own connection to MySQL. A free Aiven plan allows only a small number, which is fine for a demo but not for many visitors at once.
- **The free Aiven database may be paused** if it is not used for a long time. If the site shows an error, check that the Aiven service says **Running**.
- **Reset the live data to the sample data.** Run `init-db` from your laptop with the Aiven values set for that terminal only (PowerShell):

```powershell
$env:DB_HOST="mysql-xxxx.aivencloud.com"; $env:DB_PORT="12345"; $env:DB_USER="avnadmin"; $env:DB_PASSWORD="..."; $env:DB_SSL="1"; $env:DB_SSL_CA="C:\Users\you\Downloads\ca.pem"; flask --app app init-db
```

  Close that terminal afterwards, so you don't accidentally wipe the live database later.
- **Never commit the Aiven password or `ca.pem` to GitHub.** They only go into Vercel's environment settings.
- **`render.yaml`** is the old Render setup. Vercel does not use it, and it can be deleted once the Render service is turned off.

## 4. Team

BSCS 3A, Group 4: Neil Ivan O. Ambong, Katrice May Q. Jogno (team lead), Rojan Macasaet, Kristian Siegfreid Mancenon, and Stephanie Joy P. Parangan.
Franchesca Dela Gente (CSHCI group) also contributed to the customer pages, since the project was shared by two subjects.

### Git rules
- Make one branch per person or per feature (`member3-booking`, …), and never work directly on `main`.
- Commit small and often. Open a **pull request**, and let one other member review it before merging.
- Pull `main` every morning so your branch doesn't drift.

## 5. Notes
- Never put passwords in the code. They go in `.env` (on your laptop) or in Vercel's environment settings, never in git.
- Always use `query("... WHERE id=%s", [value])`. Never build SQL with f-strings and user input.
- VS Code: `.vscode/settings.json` turns off auto-format for templates, because Prettier breaks Jinja tags.
