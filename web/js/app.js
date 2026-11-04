// Drop, Wash, Go — small UI helpers for the static pages.
// No data is saved; these only make the mockups clickable.

document.addEventListener("DOMContentLoaded", () => {
  // Table rows that open a page
  document.querySelectorAll("tr[data-href]").forEach((row) => {
    row.classList.add("clickable");
    row.addEventListener("click", (e) => {
      if (!e.target.closest("a, button")) location.href = row.dataset.href;
    });
  });

  // Chip groups: highlight the clicked chip and filter items by data-tags
  document.querySelectorAll(".chips[data-filter]").forEach((group) => {
    const target = group.dataset.filter ? document.querySelector(group.dataset.filter) : null;
    group.addEventListener("click", (e) => {
      const chip = e.target.closest(".chip");
      if (!chip) return;
      group.querySelectorAll(".chip").forEach((c) => c.classList.toggle("active", c === chip));
      if (!target) return;
      const want = chip.dataset.value;
      target.querySelectorAll("[data-tags]").forEach((item) => {
        item.hidden = want !== "all" && !item.dataset.tags.split(" ").includes(want);
      });
    });
  });

  // Shop search
  const search = document.querySelector("[data-search]");
  if (search) {
    const items = document.querySelectorAll(search.dataset.search + " [data-name]");
    search.addEventListener("input", () => {
      const q = search.value.trim().toLowerCase();
      items.forEach((item) => (item.hidden = !item.dataset.name.toLowerCase().includes(q)));
    });
  }

  // Welcome page: Continue goes to the page for the chosen role
  const roleForm = document.querySelector("#role-form");
  if (roleForm) {
    roleForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const role = roleForm.querySelector("input[name=role]:checked").value;
      location.href = role === "shop" ? "staff-register.html" : "create-account.html";
    });
  }

  // Book laundry: update the summary when the handling option changes
  const booking = document.querySelector("#booking-form");
  if (booking) {
    const rate = Number(booking.dataset.rate);
    const fee = Number(booking.dataset.fee || 0);
    const kg = booking.querySelector("#weight");
    const update = () => {
      const opt = booking.querySelector("input[name=handling]:checked");
      const delivers = opt.value === "pickup-delivery";
      const pickup = opt.value !== "drop-off";
      const weight = Number(kg.value) || 0;
      const laundry = rate * weight;
      const total = laundry + (delivers ? fee : 0);
      const set = (sel, text) => document.querySelectorAll(sel).forEach((el) => (el.textContent = text));
      set("[data-sum=handling]", opt.dataset.label);
      set("[data-sum=kg]", weight);
      set("[data-sum=laundry]", "₱" + laundry.toLocaleString());
      set("[data-sum=total]", "₱" + total.toLocaleString());
      set("[data-when]", pickup ? "Pickup" : "Drop-off");
      document.querySelectorAll("[data-show=delivery]").forEach((el) => (el.hidden = !delivers));
      document.querySelectorAll("[data-show=pickup]").forEach((el) => (el.hidden = !pickup));
      document.querySelectorAll("[data-pay]").forEach((el) => (el.hidden = el.dataset.pay !== (delivers ? "delivery" : "counter")));
    };
    booking.addEventListener("change", update);
    kg.addEventListener("input", update);
    update();
  }

  // Mark as paid: compute change, swap the GCash reference field
  const paid = document.querySelector("#paid-form");
  if (paid) {
    const due = Number(paid.dataset.due);
    const received = paid.querySelector("#received");
    const change = paid.querySelector("#change");
    const update = () => {
      const gcash = paid.querySelector("input[name=method]:checked").value === "gcash";
      paid.querySelector("[data-method=cash]").hidden = gcash;
      paid.querySelector("[data-method=gcash]").hidden = !gcash;
      const diff = (Number(received.value.replace(/[^\d.]/g, "")) || 0) - due;
      change.textContent = "₱" + Math.max(diff, 0).toFixed(2);
    };
    paid.addEventListener("change", update);
    received.addEventListener("input", update);
    update();
  }

  // Notifications: mark all as read
  const markAll = document.querySelector("#mark-all");
  if (markAll) {
    markAll.addEventListener("click", () => document.querySelectorAll(".unread-dot").forEach((d) => d.remove()));
  }

  // Confirm weight pop-up (staff order details)
  const weightModal = document.querySelector("#weight-modal");
  if (weightModal) {
    const form = weightModal.querySelector("#weight-form");
    const input = form.querySelector("#actual-weight");
    const discard = document.querySelector("#discard-modal");
    const rate = Number(form.dataset.rate);
    const fee = Number(form.dataset.fee);
    const startValue = input.defaultValue;
    const peso = (n) => "₱" + n.toFixed(2);
    const update = () => {
      const kg = Number(input.value) || 0;
      document.querySelectorAll("[data-w=kg]").forEach((el) => (el.textContent = kg));
      form.querySelector("[data-w=laundry]").textContent = peso(rate * kg);
      form.querySelector("[data-w=total]").textContent = peso(rate * kg + fee);
    };
    const open = () => {
      input.value = startValue;
      update();
      weightModal.showModal();
      input.focus();
    };
    // Cancel only asks for confirmation when the weight was changed
    const cancel = () => {
      if (input.value !== startValue) discard.showModal();
      else weightModal.close();
    };

    document.querySelector("#open-weight").addEventListener("click", open);
    input.addEventListener("input", update);
    weightModal.querySelectorAll("[data-cancel]").forEach((b) => b.addEventListener("click", cancel));
    weightModal.addEventListener("cancel", (e) => { e.preventDefault(); cancel(); }); // Esc key
    weightModal.addEventListener("click", (e) => { if (e.target === weightModal) cancel(); }); // click outside
    discard.querySelector("#keep-editing").addEventListener("click", () => { discard.close(); input.focus(); });
    discard.querySelector("#discard-weight").addEventListener("click", () => { discard.close(); weightModal.close(); });

    form.addEventListener("submit", (e) => {
      if (!input.checkValidity()) { e.preventDefault(); input.reportValidity(); return; }
      const kg = Number(input.value);
      const status = document.querySelector("#order-status");
      status.className = "pill processing";
      status.textContent = "Processing";
      document.querySelector("#order-total").innerHTML = `<span>Total (${kg} kg)</span><span>${peso(rate * kg + fee)}</span>`;
      const note = document.querySelector("#next-step-note");
      note.textContent = `Weight confirmed: ${kg} kg. The order is now processing.`;
      document.querySelector("#open-weight").hidden = true;
    });

    if (location.hash === "#confirm-weight") open();
  }

  // Shop info: Save is disabled until something changes,
  // and leaving with unsaved changes asks first.
  const shopForm = document.querySelector("#shop-form");
  if (shopForm) {
    const saveBtn = document.querySelector("#save-shop");
    const dirtyHint = document.querySelector("#dirty-hint");
    const savedHint = document.querySelector("#saved-hint");
    const modal = document.querySelector("#unsaved-modal");
    const list = modal.querySelector("#changes-list");
    const fields = [...shopForm.querySelectorAll("input")];
    const labelOf = (el) => shopForm.querySelector(`label[for="${el.id}"]`).textContent;
    const valueOf = (el) => (el.type === "checkbox" ? (el.checked ? "On" : "Off") : el.value.trim());
    let saved = new Map(fields.map((el) => [el, valueOf(el)]));
    let pendingHref = null;

    const changes = () => fields.filter((el) => valueOf(el) !== saved.get(el));
    const refresh = () => {
      const dirty = changes().length > 0;
      saveBtn.disabled = !dirty;
      dirtyHint.hidden = !dirty;
      if (dirty) savedHint.hidden = true;
    };
    const save = () => {
      saved = new Map(fields.map((el) => [el, valueOf(el)]));
      refresh();
      savedHint.hidden = false;
    };

    shopForm.addEventListener("input", refresh);
    shopForm.addEventListener("change", refresh);
    shopForm.addEventListener("submit", (e) => { e.preventDefault(); save(); });

    // Any link that leaves the page (sidebar, bottom nav, profile, log out)
    document.addEventListener("click", (e) => {
      const link = e.target.closest("a[href]");
      if (!link || !changes().length) return;
      e.preventDefault();
      pendingHref = link.href;
      modal.querySelector("#leave-to").textContent = link.getAttribute("aria-label") || link.textContent.trim();
      const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
      list.innerHTML = changes().map((el) =>
        `<li><span class="ch-label">${esc(labelOf(el))}</span>` +
        `<span><span class="ch-old">${esc(saved.get(el) || "(empty)")}</span> → <span class="ch-new">${esc(valueOf(el) || "(empty)")}</span></span></li>`
      ).join("");
      modal.showModal();
    });

    modal.querySelector("#keep-editing").addEventListener("click", () => { pendingHref = null; modal.close(); });
    modal.querySelector("#discard-leave").addEventListener("click", () => { location.href = pendingHref; });
    modal.querySelector("#save-leave").addEventListener("click", () => { save(); location.href = pendingHref; });

    // Browser back, refresh, or closing the tab
    window.addEventListener("beforeunload", (e) => {
      if (changes().length && !pendingHref) { e.preventDefault(); e.returnValue = ""; }
    });
  }
});
