# **Drop, Wash, Go**

## **Consolidated Requirements Analysis: Customer and Laundry Staff Interviews**

### **1\. Overview**

This document consolidates the findings from interviews conducted for Drop, Wash, Go, a proposed mobile application for laundry service discovery, booking, and order management.

The current dataset consists of **seven customer respondents and four laundry staff/owner respondents**, based on the responses collected and summarized by the research group. The interviews explore current laundry practices, common challenges, access to service information, pickup and delivery needs, and the operational requirements of laundry shops.

The findings serve as the basis for identifying preliminary functional and non-functional requirements. The identified needs do not automatically mean that every suggested feature must be implemented in the initial version. Final feature selection should consider the project's objectives, development schedule, technical feasibility, and the professor's requirements.

### **2\. Customer Interview Findings**

#### **Customer 1**

The customer usually brings laundry to the shop once a week and personally handles drop-off and collection. The customer has experienced lost clothing and occasions when the shop was already closed upon arrival for collection. Prices and services are generally checked inside the shop.

**Key findings:**

* Customers may experience difficulties collecting laundry outside shop operating hours.  
* Lost clothing and unclear order status can cause dissatisfaction.  
* Digital access to prices and services may improve convenience.  
* Notifications are useful, while payment preferences may vary.

#### **Customer 2**

The customer commonly contacts the laundry shop through Messenger and sometimes uses pickup services when unable to do laundry personally. However, the customer cannot easily track laundry progress and sometimes receives unexpected delivery arrivals. Delayed responses from shops can also affect booking decisions.

**Key findings:**

* Messaging-based coordination may involve delayed responses.  
* Customers may lack visibility into laundry progress and delivery schedules.  
* Clear price breakdowns and timely updates can improve the customer experience.  
* Pickup and delivery coordination is an important consideration.

#### **Customer 3 — Weekend Laundry and Machine Availability**

The customer usually brings laundry to the shop once a week, particularly on Sundays. A major inconvenience occurs during peak hours when washing machines are occupied, resulting in waiting time. The customer has also used third-party courier services during busy school or work periods.

The customer expressed interest in checking laundry status, comparing prices, and viewing ratings or reviews through an application.

**Key findings:**

* Peak-hour congestion can inconvenience customers.  
* Third-party couriers can provide an alternative when customers lack time.  
* Customers value transparent per-kilogram or per-load pricing.  
* Ratings and reviews may help customers compare shops.  
* Machine availability is a potential concern, although live machine tracking requires further validation.

#### **Customer 4 — Student and Transportation Constraints**

The customer collects laundry throughout the week and brings it to a nearby shop during weekends. The customer sometimes waits one to two hours while laundry is being processed and uses nearby coffee shops to study or attend online classes. Carrying heavy laundry and dealing with sudden rain are additional inconveniences.

The customer has used third-party courier services during busy periods and expressed interest in shop comparisons, laundry status tracking, and transparent pricing.

**Key findings:**

* Laundry drop-off and waiting can interfere with school or work activities.  
* Carrying heavy laundry may require additional transportation.  
* Pickup and delivery could be useful for students and people with limited time.  
* Laundry status and transparent pricing are important priorities.

#### **Customer 5 — Rodelito P. Roque**

The customer usually washes clothes personally during days off and uses laundry services approximately three times a month when work or other responsibilities limit available time. The customer is a regular at a familiar laundry shop and generally finds it easy to ask about prices and raise concerns in person.

The customer has not used pickup and delivery services because the usual routine is to drop off laundry while travelling to work and collect it on the way home. The customer also noted that delivery services are unavailable in the area.

The customer considers a laundry application potentially helpful, particularly if it allows preferred pickup and delivery schedules. A major concern is laundry being left unattended outside the home when nobody is available to receive it.

**Key findings:**

* Some customers are satisfied with their existing in-person process and do not experience frequent problems.  
* Familiarity with an existing shop can make in-person communication convenient.  
* Scheduled pickup and delivery could help customers with demanding work schedules.  
* Customers may need to specify when someone will be available to hand over or receive laundry.  
* Leaving laundry unattended outside a home creates concerns about theft or loss.  
* Pickup and delivery may not be practical in every location.

#### **Customer 6 — Uncertain Completion Time and Shop Information**

The customer usually brings laundry personally to a shop, where the clothes are weighed and the price is calculated. The customer returns when the laundry is expected to be ready, but completion may depend on the volume of laundry and the number of customers at the shop.

The customer sometimes needs to visit the shop or send a message to ask whether the laundry is ready. Shop information is obtained through direct inquiries, Facebook pages, or recommendations from acquaintances. The customer noted that some shops do not provide complete information online.

The customer expressed interest in an application that allows shop comparison, booking, pickup and delivery scheduling, and order status monitoring.

**Key findings:**

* Uncertain completion times can lead to extra visits or messages.  
* Customers may need to consult several sources to compare shops.  
* Incomplete online information can make it difficult to assess service options.  
* Booking and order status visibility may reduce the need for repeated inquiries.  
* Estimated completion times and customer reviews are potentially useful features.

#### **Customer 7 — Scheduling and Order Reminders**

The customer brings laundry to a nearby shop when free time is available and asks when it can be collected. One inconvenience is forgetting the expected completion date and needing to message or call the shop for confirmation.

The customer obtains prices and service information from shop staff, social media pages, or recommendations from acquaintances. Pickup and delivery are preferred when work or other responsibilities limit the customer's availability.

**Key findings:**

* Customers may forget collection dates when laundry is not ready for immediate pickup.  
* Estimated completion times and notifications may help customers plan collection.  
* Online booking could reduce the need to contact shops just to ask about availability.  
* Customers value access to service prices, order status, and pickup and delivery schedules.

### **3\. Summary of Customer Needs**

| Identified Theme | Interview Findings | Potential System Implication |
| ----- | ----- | ----- |
| Access to shop information | Customers obtain prices and services through signage, staff, social media, messaging applications, or personal recommendations. | Display participating shops, services, and prices. |
| Order status visibility | Customers may need to message, call, or visit shops to check progress. | Allow customers to view the latest recorded order status. |
| Completion and collection schedules | Uncertain completion times and forgotten collection dates can lead to unnecessary inquiries or visits. | Display estimated completion information and support collection scheduling where feasible. |
| Pickup and delivery convenience | Work, school, transportation, and heavy laundry can make drop-off inconvenient. | Provide booking options for shops that offer pickup and delivery. |
| Schedule coordination | Customers may not be home when laundry is collected or delivered. | Let customers select a preferred schedule, subject to shop confirmation. |
| Transparent pricing | Customers want to understand service rates and fees before booking. | Display service rates and applicable fees; clarify when final pricing depends on actual weight or shop assessment. |
| Peak-hour congestion | Some customers experience waiting when machines or shop capacity are occupied. | Consider shop availability indicators if the information can be maintained reliably. |
| Safety and trust | Customers are concerned about lost clothing and laundry left unattended. | Record handover and delivery instructions and coordinate with the customer. |
| Shop comparison | Customers may find it difficult to compare prices, services, and service quality. | Consider shop profiles and ratings or reviews, subject to scope. |
| Different customer preferences | Some customers are satisfied with personal drop-off and do not require delivery. | Support different service options without assuming all customers need pickup and delivery. |

### **4\. Laundry Staff Interview Findings**

#### **Staff 1 — Shop “Taga Norte”**

The staff member explained that the usual process involves receiving laundry, weighing it, asking the customer to select a service, recording the order, and informing the customer when the laundry is ready. Common challenges include customers losing claim stubs and clothing becoming mixed during busy periods.

The shop displays prices at the counter or outside and offers pickup and delivery to nearby residents and regular customers, with additional fees for farther locations. Suggested features included digital order records, booking notifications, and automated customer notifications.

**Key findings:**

* Order identification and recordkeeping are important operational concerns.  
* Manual follow-ups can take additional time.  
* Pickup and delivery require customer addresses, schedules, and coordination.  
* Late cancellations may cause inconvenience, particularly after processing has started.  
* Additional service or platform fees may affect shop earnings.

#### **Staff 2 — Shop Using a POS System**

The staff member described a process that uses a point-of-sale (POS) system, digital weighing scales, printed receipts, barcodes, and laundry basket labels. The shop works with partner riders and an in-house rider for pickup and delivery.

The staff member suggested a real-time order queue, direct customer communication, and a capacity calculator to help determine how much laundry the shop can accept.

**Key findings:**

* Some shops already use digital systems, so the application should not assume all shops rely entirely on paper records.  
* Barcodes and labels help identify orders.  
* Equipment downtime and incomplete customer instructions can affect operations.  
* Capacity information may help shops manage incoming orders.  
* Cancellation policies can help manage costs associated with rider dispatch.

#### **Staff 3 — Laundry Shop Owner Who Requested Anonymity**

The owner explained that customers usually transact face-to-face. Laundry is received, weighed, and recorded through a receipt. The owner personally manages the shop most of the time but delegates to an employee when unavailable.

Confusion can occur during busy periods, particularly on Fridays. Additional staff are assigned during these periods to help manage customers. Prices and service differences are explained when customers bring their laundry, especially for items such as blankets and jackets that may have different rates.

The shop does not currently offer pickup and delivery because it is located in a commercial area and finding a suitable delivery vehicle would be difficult. The owner is interested in recording when customers intend to collect their finished laundry, since some orders remain uncollected for two to three days after completion.

The owner also emphasized storage capacity and avoiding mixed-up laundry orders. Potential future features include shop promotions, discounts, coupons, and loyalty rewards.

**Key findings:**

* Busy periods can lead to confusion when several customers arrive simultaneously.  
* Clear service and pricing information is important, particularly for special items.  
* Not every shop needs or can support pickup and delivery.  
* Expected collection dates may help shops manage finished but unclaimed laundry.  
* Storage capacity and proper order separation are important operational considerations.  
* Promotions and loyalty rewards may be useful for repeat customers.  
* A clear demonstration of the application's practical value may help shop owners assess its usefulness.

#### **Staff 4 — Ate Chellyka, Makati Condo**

The staff member described a process in which customers personally bring laundry to the shop. Staff receive and weigh the clothes, confirm the requested service, calculate the price, and identify the order through a name or claim stub. Customers are contacted through text or phone call when the laundry is ready for collection.

Common challenges include multiple customers arriving simultaneously during weekends or holidays and delays caused by high laundry volume or equipment problems involving washing machines and dryers.

For shops that provide pickup and delivery, arrangements may be made through calls or chat. Staff collect the customer's address, preferred pickup time, and laundry quantity, then check whether personnel are available to handle the request.

The staff member expressed interest in online booking, organized order lists, notifications, status tracking, service prices, and schedule availability. Required booking information includes the customer's name, contact number, requested service, estimated laundry quantity, preferred date and time, relevant address, and special instructions.

The staff member also raised concerns about ease of use, possible usage fees, additional equipment or internet requirements, and the protection of customers' personal information.

**Key findings:**

* Busy periods and equipment problems can affect order processing and completion times.  
* Staff communicate estimated completion times and contact customers when orders are ready.  
* Some shops coordinate pickup and delivery through calls or chats, subject to staff availability.  
* Booking lists, notifications, and order status tracking may help organize daily operations.  
* Complete booking details and special instructions are important for service fulfillment.  
* Ease of use, operating costs, infrastructure requirements, and privacy may affect adoption.

### **5\. Summary of Laundry Staff Needs**

| Identified Theme | Interview Findings | Potential System Implication |
| ----- | ----- | ----- |
| Order records | Shops use different approaches, including manual receipts and POS systems. | Maintain consistent booking and order records. |
| Order identification | Lost claim stubs and possible mixing of laundry can create confusion. | Assign a unique order ID to each booking and display it in order details. |
| Customer updates | Staff contact customers when laundry is ready or when issues arise. | Support order status updates and notifications where technically available. |
| Completion and collection | Finished laundry may remain uncollected for several days. | Record or confirm the expected collection schedule where applicable. |
| Pickup and delivery coordination | Shops differ in their ability to provide delivery services and available staff. | Allow shops to indicate whether pickup and delivery are offered and confirm requests. |
| Capacity management | Storage limitations, equipment problems, and busy periods can affect orders. | Consider a simple availability or booking-capacity control, subject to staff input. |
| Cancellations | Late cancellations can create operational and transportation costs. | Define booking cancellation rules and communicate them clearly. |
| Special instructions | Staff need to know about special garments, separate washing requirements, and other customer preferences. | Provide a field for relevant order instructions. |
| Ease of use and cost | Staff may be hesitant if the application is difficult to use or requires additional costs. | Keep staff workflows simple and assess practical infrastructure requirements. |
| Privacy | Staff emphasized protecting customer information. | Restrict access to personal details and handle data responsibly. |
| Promotions and loyalty | An owner expressed interest in discounts, coupons, and rewards. | Consider promotional features for a later version. |