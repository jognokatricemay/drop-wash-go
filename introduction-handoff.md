# Hand-off: Drop, Wash, Go IMRAD Introduction

Use this file as context for writing the **Introduction** of our IMRAD paper. It includes everything decided so far about the project: the problem, interview findings, requirements, MVP scope, design, use case diagram and tech stack.

> **For the assistant in the next session:** the paper is written in **formal academic English**. I chat in Taglish. Do **not** invent citations, authors, years, statistics or URLs. Every source in the RRL, RRS and RRSys must be real and verifiable, so search the web and give me the link. If you can't verify a source, mark it `[VERIFY]`. Ask me for anything listed under "Missing info" instead of guessing.

---

## 1. What the Introduction must contain

| Section | What goes in it |
|---|---|
| **Background of the Study** | Context of the laundry service industry, how customers and shops coordinate today, the problem, and why a booking and tracking app helps |
| **Purpose and Objectives** | A general objective plus specific objectives that map to the MVP features (see §5) |
| **Significance of the Study** | Benefits to customers, laundry shop owners and staff, students, future researchers and developers |
| **Scope and Limitations** | What the MVP covers and what it doesn't (see §6) |
| **RRL**: Review of Related Literature | Concepts and theories: digitalization of small service businesses, online booking and scheduling, order tracking, usability, and on-demand / pickup-and-delivery services |
| **RRS**: Review of Related Studies | Prior research and theses (local and foreign) on laundry management systems, booking systems and order tracking |
| **RRSys**: Review of Related Systems | Existing apps and systems (local and foreign laundry apps, booking platforms), compared feature by feature with Drop, Wash, Go |

Suggested extras: a **synthesis** paragraph at the end of the RRL/RRS/RRSys showing the gap Drop, Wash, Go fills, and a **feature comparison table** in the RRSys.

---

## 2. Project overview

- **Name:** Drop, Wash, Go
- **Type:** a laundry booking and order-tracking app with a customer side and a shop staff side. Phone and PC (web) UI designs are done in Figma.
- **Team:** 5 student members.
- **Timeline (as of Oct 24, 2026):** week 1 (UI design) is ending. Week 2 is coding. Week 3 is the presentation.
- **One-line description:** Drop, Wash, Go lets customers find participating laundry shops, see their services, rates and fees, book a drop-off, pickup, or pickup-and-delivery laundry service, and track the order's status. Shop staff can accept or reject bookings, confirm laundry weight, update order status, and record payment.

### Core idea / value
- Customers can see shop info, prices and status **without visiting the shop or contacting it repeatedly**.
- Shops get **organized booking records, unique order IDs, clear customer instructions, and manageable schedules**.
- **Different shops work differently.** Some shops offer pickup and delivery, and some are drop-off only. The app supports these differences rather than forcing one process on every shop.
- **Requested vs confirmed schedule.** The customer requests a schedule and the shop confirms it or changes it.
- **Booking is optional.** Walk-in customers still exist outside the app. Even for drop-off-only shops the app adds value through information (prices, services, fees), a reserved slot and coordination, an order ID, and status tracking (e.g., knowing when the laundry is ready to collect).

---

## 3. Interview findings (basis of the Background and Significance sections)

We interviewed customers and laundry shop staff/owners. Summary of the findings:

**Customers**
- Commonly want to know the **price, the expected completion time, and the current status** of their laundry without visiting or contacting the shop repeatedly.
- Have different reasons for using laundry services. Some want **convenience because of work, school, transportation, or time constraints**, and so value pickup and delivery. Others are satisfied dropping off their laundry personally.

**Staff and owners**
- Emphasize **organized order records, correct order identification, manageable booking schedules, clear customer instructions**, and the need to account for **shop capacity and equipment availability**.
- Workflows differ. Some shops use **POS systems and barcode labels**, while others rely on **face-to-face transactions and claim stubs/receipts**.
- **Pickup and delivery are not feasible for every shop** because of resources or need.

**Overall analysis**
- Customers and staff share an interest in **better access to order information and clearer communication**.
- The most consistently supported priorities are shop and price information, booking coordination, order identification, status updates, and clear communication.
- The app should support variations in shop services and distinguish the customer's **requested** schedule from the **shop-confirmed** schedule.

**Missing info (ask me):** number of interviewees, how many were customers vs staff/owners, the location (city/barangay), the dates, and the names or count of the shops interviewed.

---

## 4. Requirements

### Core MVP functional requirements
- **FR-01 Laundry Shop Listing:** display participating shops and their basic info.
- **FR-02 Service and Price Information:** display each shop's services and rates.
- **FR-03 Booking Submission:** customers submit a booking with order details, a preferred schedule, and pickup/delivery info where applicable.
- **FR-04 Shop Booking Management:** authorized staff view incoming bookings and accept or reject them.
- **FR-05 Booking and Order Identification:** generate a unique order ID for each accepted booking.
- **FR-06 Order Status Management:** staff update order status: Pending → Accepted → Processing → Ready for Pickup / Ready for Delivery → Completed (Rejected also exists).
- **FR-07 Customer Order Tracking:** customers view the latest recorded status.
- **FR-08 Schedule Coordination:** record the preferred pickup, drop-off, or collection schedule. The schedule is subject to shop confirmation.
- **FR-09 Booking Information Management:** record the customer name, contact, service, estimated quantity, address and schedule, and special instructions.
- **FR-10 Price and Fee Disclosure:** show rates and known fees before the customer confirms. Tell the customer when the price is only an estimate because it depends on the actual weight.
- **FR-11 Shop Service Availability:** indicate whether a shop offers pickup and delivery, and don't offer booking options the shop doesn't support.
- **FR-12 Collection Information:** staff record or confirm the expected collection or delivery schedule.

### Future requirements (not in the MVP)
- FR-13 Customer Notifications. A basic in-app notification list is in the UI, but push/SMS/email notifications are future work.
- FR-14 Shop Availability and Capacity.
- FR-15 Ratings and Reviews.
- FR-16 Customer Communication (in-app chat with photo upload).
- FR-17 Promotions and Loyalty Rewards.
- FR-18 Payment Integration (online payment / automated verification). It must not be presented as working unless it is actually implemented and tested.

### Non-functional requirements
- **NFR-01 Usability:** a clear interface for users with different levels of tech familiarity.
- **NFR-02 Data Consistency:** booking details, order IDs and statuses stay consistent between the customer and staff sides.
- **NFR-03 Access Control:** functions are restricted by role (customer vs shop staff).
- **NFR-04 Privacy:** contact info and addresses are visible only to authorized users who need them.
- **NFR-05 Reliability:** required fields are validated, and invalid submissions don't lose saved data.
- **NFR-06 Practicality:** the system fits the staff, internet access, and devices that shops can realistically support.

### MVP priorities (in order)
1. Shop information (shops, services, prices)
2. Booking with a preferred schedule
3. Staff booking management (accept/reject)
4. Order ID and order details
5. Status updates and customer tracking
6. Schedule and fee clarity (fees shown, schedule needs shop confirmation)
7. Pickup/delivery only for shops that offer it
8. Special instructions

---

## 5. Draft objectives (refine in the paper)

**General objective:** To design and develop Drop, Wash, Go, a web-based laundry booking and order-tracking application that improves coordination between customers and participating laundry shops.

**Specific objectives (draft):**
1. Display participating laundry shops with their services, rates, applicable fees, and offered handling options (drop-off, pickup, delivery).
2. Allow customers to submit bookings with a handling option, a preferred schedule, and special instructions, subject to shop confirmation.
3. Allow shop staff to view, accept, or reject bookings, confirm or adjust schedules, and confirm the actual laundry weight.
4. Automatically generate a unique Order ID for every accepted booking.
5. Allow staff to update order status and customers to track the latest status and view collection or delivery schedules.
6. Record payment status (paid/unpaid) and the payment method (cash or GCash paid directly to the shop).
7. Evaluate the system's usability. **Ask me** whether we're doing an evaluation (e.g., SUS or an ISO 25010 survey) and with how many respondents.

---

## 6. Scope and limitations (decisions already made)

**Scope (included)**
- Two user roles: **Customer** and **Shop Staff** (one shop account per shop in the MVP).
- **Guest browsing:** shops, services and rates can be viewed **without logging in**. Login is required only when booking. Staff functions always require login.
- Customer: create an account / log in, browse shops, view services, rates and fees, book (Drop-off, Pickup, or Pickup + Delivery, only if the shop offers it), add special instructions, track status, view order details and how to pay, view notifications, manage the profile.
- Staff: register the shop, log in, view booking requests, accept or reject (with a reason the customer can see), confirm or change the schedule, confirm the actual weight, update the status, set the collection or delivery schedule, mark as paid (recording cash or GCash), manage shop info, services, rates, handling toggles and accepted payment methods.
- Order ID is generated **only when the booking is accepted**. Before that, the customer sees it as a "Booking request".
- Status flow: Pending, Accepted, Processing, Ready for Pickup / Ready for Delivery, Completed, plus Rejected. Payment tags: Unpaid / Paid.
- Phone and PC (web browser) layouts.

**Limitations (excluded / constraints)**
- **No online payment.** Customers pay the shop directly (cash or GCash, on collection or on delivery). The app only records the payment status and method.
- No in-app chat or photo upload, no ratings and reviews, no promotions or loyalty rewards, no capacity management, and no live machine availability. These are future scope.
- No multi-staff accounts per shop, no owner/admin role, no walk-in order entry, no QR codes or printed tags. These were removed from the earlier design.
- Delivery logistics (riders, routing, live GPS tracking) are handled by the shop outside the app.
- The final price can differ from the estimate because it depends on the actual weight confirmed by the staff.
- Development time is about 1 week of coding (student project). Testing is limited to sample/seed data and participating shops. **Ask me** for the locality/target shops.
- Notifications are in-app only (no SMS or push) in the MVP.

---

## 7. System design summary (for the Background, Scope, and RRSys comparison)

- **Figma file:** https://www.figma.com/design/f9YPqdFByHc4p9Z3adJytf/Drop--Wash--Go. It has phone screens (`##-phone-customer-…`, `##-phone-staff-…`) and PC screens (`##-PC-customer-…`, `##-PC-staff-…`), prototype flows, and a components library.
- **Visual identity:** a droplet logo with a shine. The customer side uses the Primary (blue) color and the staff side uses ink (dark navy). Fonts are Bricolage Grotesque (headings) and Plus Jakarta Sans (body).
- **Key screens:** Welcome, Login (with "Browse shops" as a guest), Create account, Shop list (tags: Drop-off / Pickup / Delivery), Shop details (services and rates, accepted payments), Book laundry (with validation errors), Review booking, Booking request sent, My orders, Order tracking, Order details, Notifications, Profile. Staff screens: Register shop, Dashboard, Booking requests, Booking details (change the schedule), Accept/Reject, Orders, Order details (confirm weight), Update status (delivery schedule), Mark as paid (payment method), Shop info (handling toggles, services and rates, accepted payments).
- **Sample data:** shops include Mama Fe Laundry (pickup + delivery), Clean & Fresh, and Wash Hub (drop-off only). Sample orders: #DWG-00483 (Juan), #DWG-00481, #DWG-00480 (Pedro Reyes).

### Tech stack (planned)
- **Backend:** Python with Flask
- **Database:** MySQL (XAMPP locally)
- **Frontend:** HTML/CSS with Jinja templates and a little JavaScript (responsive for phone and PC)
- **Hosting:** PythonAnywhere
- Firebase was considered but not chosen. The team already knows MySQL, Python and HTML/CSS, and Firebase is NoSQL and JS-heavy.

---

## 8. Use case diagram (Figure 1)

The diagram is in Figma, frame "30-use-case-diagram". It has 2 actors (Customer and Staff). Log in is at the top, and use cases are listed in app order.

- **Customer:** Log in, Create account, Browse laundry shops (no login needed), View services, rates & fees (no login needed), Submit booking, Track order status, View order details & how to pay, View notifications, Manage profile.
- **Staff:** Log in, Register shop, View booking requests, Accept or reject booking, Confirm actual weight, Update order status, Mark order as paid, Manage shop info, services & payments.
- **Include / extend:**
  - Submit booking «include» Log in. Accept/reject «include» Generate unique order ID. Accept/reject «include» Confirm or change schedule.
  - Add special instructions «extend» Submit booking. Set collection/delivery schedule «extend» Update order status.
- **Future scope (dashed):** Chat with shop & send photos (FR-16), Rate & review shop (FR-15), Pay online (FR-18).

**Figure 1 description (final text):**
> Figure 1 shows the high-level use case diagram of Drop, Wash, Go. It has two actors: the Customer, who creates an account and logs in, browses participating laundry shops and views their services, rates, and fees, submits a booking by choosing a handling option the shop offers (drop-off, pickup, or pickup and delivery) and a preferred schedule, optionally adds special instructions, tracks the order status, views order details and how to pay, views notifications, and manages the profile; and the Staff, who registers the shop, logs in using the shop account, views booking requests, accepts or rejects bookings, confirms the actual laundry weight, updates the order status, marks orders as paid, and manages the shop information, services, rates, and accepted payment methods. When the Staff accepts a booking, the system confirms or adjusts the requested schedule and automatically generates a unique Order ID, so the Customer can view and track the order in the app. When updating the status, the Staff may also set the collection or delivery schedule. Payments are made directly to the shop in cash or GCash, and the system only records them. Browsing shops and viewing their services do not require an account, but booking and all staff functions require logging in. In-app chat, ratings and reviews, and online payment are shown as future scope and are not part of the MVP.

---

## 9. Ideas for RRL / RRS / RRSys (all must be verified with real sources)

**RRL topics to look for**
- The growth of the laundry service industry and laundromats (Philippines, if possible).
- Digital transformation of MSMEs (micro, small and medium enterprises) and small service businesses in the Philippines.
- Online booking/reservation systems and how they reduce waiting and coordination problems.
- Order tracking and status transparency and how they affect customer satisfaction.
- On-demand and pickup-and-delivery services, convenience for students and workers.
- Usability and UI design principles (e.g., Nielsen's heuristics, ISO 9241-11 / ISO 25010). Technology acceptance (TAM) can serve as a framework.
- Cash and e-wallet (GCash) payment behavior in the Philippines, to support why payment stays offline.

**RRS:** local theses and journal articles on laundry management systems, laundry booking/tracking apps, and web-based reservation systems (local and foreign). Look in Google Scholar, ResearchGate and Philippine university repositories.

**RRSys: candidate systems to research and verify**
- Foreign laundry apps (e.g., Laundryheap, Rinse, Washmen, Cleanly).
- Local Philippine laundry shops/chains that take online or Facebook Messenger bookings, and general delivery apps that offer laundry.
- Laundry POS/management software that shops already use (since some interviewed shops use POS and barcodes).
- Build a **comparison table** with these columns: shop listing, price display, booking, schedule confirmation, order ID, status tracking, pickup/delivery option per shop, drop-off-only support, online payment, chat, reviews. Then show how Drop, Wash, Go differs: a multi-shop listing, flexible handling per shop, a requested-vs-confirmed schedule, suitability for small local shops without POS, and guest browsing.

**Research gap to argue:** most existing apps are single-company, delivery-focused services, or POS tools for one shop. Few platforms let **small local shops with different workflows** (drop-off only or with delivery) list their services, take bookings with **shop-confirmed schedules**, and give customers **status tracking** without requiring online payment.

---

## 10. Format reminders

- IMRAD; Introduction subsections in the order listed in §1.
- Citation style: **ask me** (probably APA 7th). Include a reference list.
- Formal English, third person, and future tense for what the study *will* do unless I say otherwise.
- Keep the scope and limitations consistent with §6, and don't claim features that are future scope.
