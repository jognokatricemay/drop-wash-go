# Drop, Wash, Go — HTML/CSS pages

Static HTML/CSS version of the **PC screens** in Figma (`##-PC-customer-…` and `##-PC-staff-…`).
It is responsive: PC layout with sidebar, and on tablet/phone (≤1024px) the sidebar becomes a top bar + bottom nav like the phone design.

## Open it

Open `index.html` in a browser. Or run a local server from this folder:

```bash
python -m http.server 5500
```

then go to http://localhost:5500.

## Files

- `css/style.css` — all styles. Colors are the Figma library variables (`--primary`, `--ink`, status colors...). Staff pages use `<body class="staff">`, which switches the brand color to ink (same as the Figma "Role" variables).
- `js/app.js` — small helpers only (shop filter/search, booking summary update, mark-as-paid change, clickable table rows). Nothing is saved.

## Pages

| Figma frame | File |
|---|---|
| 01 welcome / choose role | `index.html` |
| 02 create account | `create-account.html` |
| 03 login | `login.html` |
| 03a login to book | `login-to-book.html` |
| 04 home | `home.html` |
| 05 / 05a shop list (guest) | `shops.html` / `shops-guest.html` |
| 06 / 06a shop details (guest) | `shop-details.html` / `shop-details-guest.html` |
| 07 book laundry | `book.html` |
| 07b book, drop-off only | `book-drop-off.html` |
| 08 book, validation errors | `book-errors.html` |
| 09 review booking | `review-booking.html` |
| 10 request sent | `request-sent.html` |
| 11 my orders | `my-orders.html` |
| 12 order details | `order-details.html` |
| 13 booking rejected | `booking-rejected.html` |
| 14 notifications | `notifications.html` |
| 15 profile | `profile.html` |
| 16 register shop | `staff-register.html` |
| 17 shop login | `staff-login.html` |
| 18 dashboard | `staff-dashboard.html` |
| 19 booking requests | `staff-requests.html` |
| 20 booking details | `staff-booking-details.html` |
| 21 booking accepted | `staff-booking-accepted.html` |
| 22 orders | `staff-orders.html` |
| 23 order details | `staff-order-details.html` |
| 24 confirm weight | pop-up inside `staff-order-details.html` (also opens from `staff-order-details.html#confirm-weight`) |
| 25 update status | `staff-update-status.html` |
| 26 mark as paid | `staff-mark-paid.html` |
| 27 profile | `staff-profile.html` |
| 28 shop info | `staff-shop-info.html` |

## Turning these into Flask templates (week 2)

1. Move the `.html` files to `templates/`, and `css/` + `js/` to `static/`.
2. Make a `base.html` with the `<head>`, top bar, sidebar and bottom nav (they're the same on every page), and put `{% block content %}{% endblock %}` where `<div class="main-inner">` content goes. Each page then `{% extends "base.html" %}`.
3. Change `href="css/style.css"` to `href="{{ url_for('static', filename='css/style.css') }}"` and page links like `href="home.html"` to `href="{{ url_for('home') }}"`.
4. Replace the sample data (Juan Dela Cruz, #DWG-00483, ₱172.50…) with values from MySQL, e.g. `{% for order in orders %}` for table rows.
