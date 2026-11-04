Proposed Functional Requirements
Based on the interviews collected so far, the following requirements are proposed for consideration.
Core MVP Requirements
FR-01: Laundry Shop Listing
The system shall display participating laundry shops and basic shop information.
FR-02: Service and Price Information
The system shall display the services and corresponding rates provided by each participating shop.
FR-03: Booking Submission
The system shall allow customers to submit a laundry booking by providing the required order details, preferred schedule, and applicable pickup or delivery information.
FR-04: Shop Booking Management
The system shall allow authorized shop staff to view incoming bookings and accept or reject them.
FR-05: Booking and Order Identification
The system shall generate a unique order ID for each accepted booking to support order identification and reduce confusion.
FR-06: Order Status Management
The system shall allow authorized staff to update the status of an order. The proposed status flow may include Pending, Accepted, Processing, Ready for Pickup or Delivery, and Completed, depending on the service selected.
FR-07: Customer Order Tracking
The system shall allow customers to view the latest recorded status of their orders.
FR-08: Schedule Coordination
The system shall record the customer's preferred pickup, drop-off, or collection schedule, as applicable. The selected schedule shall be subject to confirmation by the shop.
FR-09: Booking Information Management
The system shall record the information needed to process an order, such as the customer's name, contact details, service selection, laundry details, and applicable address and schedule.
FR-10: Price and Fee Disclosure
The system shall display the applicable service rates and known additional fees before the customer confirms a booking. Where the final price depends on actual laundry weight or shop assessment, the system shall communicate that the displayed amount may be an estimate.
FR-11: Shop Service Availability
The system shall indicate whether a shop offers pickup and delivery. Shops that do not offer these services shall not be presented as available for unsupported booking options.
FR-12: Finished Laundry Collection Information
The system should allow the shop to record or confirm the expected collection schedule for completed laundry, where applicable.
Potential Future Requirements
FR-13: Customer Notifications
The system may notify customers about booking confirmation and order status changes, depending on the supported notification method and implementation scope.
FR-14: Capacity Management
The system may allow shop staff to manage booking availability or indicate when the shop cannot accept additional orders. More advanced capacity calculations may be considered in a future version.
FR-15: Ratings and Reviews
The system may allow customers to rate or review participating shops after using their services.
FR-16: Customer Communication
The system may provide a communication feature for customers and shops to clarify booking details and coordinate schedules.
FR-17: Promotions and Loyalty Rewards
The system may allow shops to publish discounts, coupons, or loyalty rewards for repeat customers.
FR-18: Payment Integration
Online payment or automated payment verification may be considered in a future version if feasible. It should not be presented as a working feature unless a suitable payment service is actually implemented and tested.
7. Preliminary Non-Functional Requirements
NFR-01: Usability
The application should provide a clear and straightforward interface for customers and shop staff with different levels of technical familiarity.
NFR-02: Data Consistency
Booking details, order IDs, and order statuses should remain consistent between the customer and staff interfaces.
NFR-03: Access Control
The system should restrict functions and information according to user roles, such as customer and shop staff.
NFR-04: Privacy
The application should handle customer contact information and pickup or delivery addresses responsibly and only make them available to authorized users who need them to process the order.
NFR-05: Reliability
The system should validate required booking details and handle invalid or incomplete submissions without losing previously saved order information.
8. Preliminary Analysis and Implications for the MVP
The interviews suggest that Drop, Wash, Go should focus on making laundry information easier to access, coordinating bookings, and providing clear order status updates. Customers have different reasons for using laundry services: some want convenience because of work or school, while others are already satisfied with dropping off their laundry personally.
The interviews also show that laundry shops have different operating conditions. Some already use POS systems and barcode labels, while others rely on face-to-face transactions and receipts. Some offer pickup and delivery, while others do not have the resources or need to provide these services.
For this reason, the application should support differences between shops rather than assume every shop follows the same process.
For the initial version, the recommended priorities are:
Display participating shops, services, and prices.
Allow customers to submit a booking with a preferred schedule.
Allow shop staff to review and confirm bookings.
Assign a unique order ID and maintain order details.
Allow staff to update order status and customers to view it.
Clearly display applicable fees and communicate that schedules require shop confirmation.
Support pickup and delivery only for shops that offer those services.

Na-revise ko na ang phone flow, nasa dwg-phone-revised-svg.zip: 28 screens at ang flow map (29). Hindi ko pa nakikita ang itsura ng bawat isa, kaya tingnan mo muna. Ang PC version ay hindi ko pa ginagalaw, kaya luma pa ang dwg-all-screens.zip.

### Ano ang nagbago

**Tinanggal**

- Lahat ng payment screens: Payment method, Online payment, Payment submitted, Payment on Delivery set, E-Receipt, Payment history, Payment records, at Record payment.
- Walk-in order at Print tag, Join shop at Shop code, Staff accounts, at QR.
- Washing at Drying, na pinagsama bilang Processing.

**Nadagdag**

- Shop list at Shop details: may tags na Drop-off / Pickup / Delivery at listahan ng services at rates. Ang Wash Hub ay drop-off lang, kaya hindi ito nag-aalok ng pickup (FR-11).
- Book laundry: pipili ang customer ng Drop-off, Pickup, o Pickup + Delivery. May note na subject to shop confirmation (FR-08), at may version na may validation errors (NFR-05).
- Booking details (staff): puwedeng baguhin ng staff ang schedule bago i-accept.
- Booking accepted: dito pa lang ginagawa ang Order ID (FR-05). Pagka-submit, "Booking request" lang ang makikita ng customer.
- Booking rejected: may reason na nakikita ng customer.
- Update status: may Delivery schedule field, kaya alam ng customer kung kailan makukuha ang labada (FR-12).
- Order details ng staff: ang Confirm weight ang pangunahing button kapag Accepted pa ang order.
- Shop info: may toggles para sa Drop-off, Pickup, at Delivery, at editable na services at rates.
- Register shop: diretso na sa login. Isang shop account na lang ang gamit sa MVP.

**Pinanatili:** ang customer Notifications, at ang staff Mark as paid (cash lang), kasi kailangan pa ring malaman ng shop kung bayad na.

### Kung may magtanong kung paano magbabayad

Ito ang puwede mong sabihin sa presentation:

- **Sa shop direkta ang bayad.** Kita sa Review booking at Order details ang note na *Pay the shop directly when you collect or receive your laundry.* Booking at order tracking ang sakop ng app, hindi ang pagbabayad.
- **Nasa future requirements ang online payment (FR-18).** Ayon sa requirement doc ninyo, hindi ito dapat ipakita bilang gumaganang feature hangga't hindi ito naiimplementa at natetest.
- **Practical na dahilan:** kailangan ng merchant account, security review, at testing ng payment gateway, na hindi kakayanin sa apat na linggo.
- **Iba-iba ang shops ayon sa interviews.** May gumagamit ng POS, may face-to-face lang, kaya hindi puwedeng isang payment process para sa lahat.
- **Next version:** payment integration, tulad ng GCash na magbabayad sa loob ng app.

Kung itanong kung paano malalaman ng shop na bayad na ang customer, sagot: minamarkahan ito ng staff bilang Paid (Mark as paid).