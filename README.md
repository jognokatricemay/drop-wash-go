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

## 3. Deploy for free: Vercel (website) + TiDB Cloud (MySQL)

The website runs on **Vercel** and the database on **TiDB Cloud Starter**, which is MySQL-compatible, so the app uses PyMySQL as usual. Vercel only hosts the website, so the database lives on TiDB. Both have free plans, and you can sign up with GitHub.

### A. Database on TiDB Cloud
1. Go to **tidbcloud.com** → sign up → **Create** a **Starter** instance (the MySQL one, not PostgreSQL). Pick a name and a region, and remember the region (you will match it in Vercel).
2. When it is **Active**, open the instance and click **Connect** (top right). Note the **Host**, **Port** (usually `4000`), and **User** (it has a prefix, like `abc123.root`), then **Generate Password** and copy it right away.
3. Make sure the public endpoint allows connections from anywhere (`0.0.0.0/0`), because Vercel's IP addresses change.
4. Create the tables and sample data once, from your laptop (see "Create or reset the data" below).

### B. Website on Vercel
1. Push the latest code to GitHub. It must include `index.py` (it exposes the Flask `app` that Vercel runs).
2. Go to **vercel.com** → sign up with GitHub → **Add New… → Project** → import the `drop-wash-go` repo.
3. **Framework Preset:** `Flask`. Leave the build and output settings empty.
4. Open **Environment Variables** and add these (copy the database values from TiDB). Tick **Production** and **Preview**.

| Key | Value |
|---|---|
| `SECRET_KEY` | any long random text (for example 40 random characters) |
| `DB_HOST` | TiDB host, e.g. `gateway01.xxxx.prod.aws.tidbcloud.com` |
| `DB_PORT` | `4000` |
| `DB_USER` | TiDB user **with its prefix**, e.g. `abc123.root` |
| `DB_PASSWORD` | TiDB password |
| `DB_NAME` | `test` (TiDB's default database) or `dropwashgo`, but use the same name everywhere |
| `DB_SSL` | `1` |
| `DB_SSL_CA` | leave empty (encrypted, certificate not checked), or paste the text of the CA certificate from TiDB's Connect dialog |

   Do **not** add `AUTO_INIT_DB`. The database already has its tables, and a serverless site should not try to create them.

5. Click **Deploy**. When it finishes, Vercel shows your link (`https://<project>.vercel.app`). Put that link at the top of this README.
6. In Vercel → **Settings → Functions → Function Region**, choose the region that matches your TiDB region (for example Singapore `sin1` for AWS `ap-southeast-1`), then **Redeploy**. Otherwise every query crosses an ocean and pages are slow.

### Updating the live site
Every push or merge to `main` on GitHub **deploys automatically**. Watch it in Vercel → **Deployments**. Every pull request also gets its own preview link. After you change an environment variable, **Redeploy**, because an old deployment does not see the new value.

### Create or reset the data
`init-db` creates the tables and loads the sample data, and it **deletes everything first**. Run it from your laptop with the TiDB values set for that terminal only (PowerShell, use single quotes around the password):

```powershell
$env:DB_HOST='gateway01.xxxx.prod.aws.tidbcloud.com'; $env:DB_PORT='4000'; $env:DB_USER='abc123.root'; $env:DB_PASSWORD='...'; $env:DB_NAME='test'; $env:DB_SSL='1'; $env:DB_SSL_CA=''
```

```powershell
flask --app app init-db
```

If `CREATE DATABASE` is denied, use `DB_NAME` = `test`. Close that terminal afterwards, so you don't accidentally wipe the live database later (the smoke test also resets the data).

### Good to know
- **Vercel runs the app as a serverless function.** There is no long "sleeping" like on a free web service, but the first visit after a quiet period can be a bit slower (cold start). Open the site a few minutes before the presentation.
- **TiDB Starter scales to zero when idle**, so the first query after a quiet period can also be slower. Check [TiDB's pricing page](https://www.pingcap.com/products/tidbcloud/pricing/) for the current free limits.
- **Connection limit.** Each running copy of the site opens its own connection to MySQL. The free plan is meant for small projects, which is fine for a demo but not for many visitors at once.
- **The region cannot be changed after creating the instance** (as far as we could find). If you pick the wrong one, create a new instance, change the environment variables, and run `init-db` again. The data is only sample data.
- **Never commit the TiDB password or any `.pem` certificate to GitHub.** They only go into Vercel's environment settings and your own `.env`.
- **`render.yaml`** is the old Render setup. Vercel does not use it, and it can be deleted.

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
