// Drop, Wash, Go — small page helpers. The server (Flask) does the real saving;
// this file only makes forms and pop-ups nicer to use.

document.addEventListener("DOMContentLoaded", () => {
  const peso = (n) => "₱" + Number(n).toLocaleString("en-PH", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  // Table rows that open a page
  document.querySelectorAll("tr[data-href]").forEach((row) => {
    row.classList.add("clickable");
    row.addEventListener("click", (e) => {
      if (!e.target.closest("a, button")) location.href = row.dataset.href;
    });
  });

  // Shop list: the search box and the filter chips work together (no page reload)
  const search = document.querySelector("[data-search]");
  if (search) {
    const grid = document.querySelector(search.dataset.search);
    const chips = document.querySelector(".chips[data-filter]");
    const empty = document.querySelector("#no-shops");
    let want = "all";
    const apply = () => {
      const q = search.value.trim().toLowerCase();
      let shown = 0;
      grid.querySelectorAll("[data-name]").forEach((item) => {
        const tagOk = want === "all" || item.dataset.tags.split(" ").includes(want);
        item.hidden = !(tagOk && item.dataset.name.toLowerCase().includes(q));
        if (!item.hidden) shown++;
      });
      if (empty) empty.hidden = shown > 0;
    };
    search.addEventListener("input", apply);
    if (chips) {
      chips.addEventListener("click", (e) => {
        const chip = e.target.closest(".chip");
        if (!chip) return;
        chips.querySelectorAll(".chip").forEach((c) => c.classList.toggle("active", c === chip));
        want = chip.dataset.value;
        apply();
      });
    }
  }

  // Welcome page: Continue goes to the sign-up page of the chosen role
  const roleForm = document.querySelector("#role-form");
  if (roleForm) {
    roleForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const role = roleForm.querySelector("input[name=role]:checked").value;
      location.href = role === "shop" ? roleForm.dataset.shopUrl : roleForm.dataset.customerUrl;
    });
  }

  // Book laundry: keep the summary in sync with the form
  const booking = document.querySelector("#booking-form");
  if (booking) {
    const fee = Number(booking.dataset.fee || 0);
    const service = booking.querySelector("#service_id");
    const kg = booking.querySelector("#est_weight");
    const set = (sel, text) => document.querySelectorAll(sel).forEach((el) => (el.textContent = text));
    const update = () => {
      const opt = booking.querySelector("input[name=handling]:checked");
      const handling = opt ? opt.value : "drop-off";
      const delivers = handling === "pickup-delivery";
      const pickup = handling !== "drop-off";
      const rate = Number(service.selectedOptions[0]?.dataset.rate || booking.dataset.rate);
      const weight = Number(kg.value) || 0;
      const laundry = rate * weight;
      set("[data-sum=handling]", opt ? opt.dataset.label : "—");
      set("[data-sum=rate]", "₱" + rate);
      set("[data-sum=kg]", weight + " " + (service.selectedOptions[0]?.dataset.unit || "kg"));
      set("[data-sum=laundry]", peso(laundry));
      set("[data-sum=total]", peso(laundry + (delivers ? fee : 0)));
      set("[data-when]", pickup ? "Pickup" : "Drop-off");
      document.querySelectorAll("[data-show=delivery]").forEach((el) => (el.hidden = !delivers));
      document.querySelectorAll("[data-show=pickup]").forEach((el) => (el.hidden = !pickup));
      document.querySelectorAll("[data-pay]").forEach((el) => (el.hidden = el.dataset.pay !== (delivers ? "delivery" : "counter")));
    };
    booking.addEventListener("change", update);
    kg.addEventListener("input", update);
    update();
  }

  // Mark as paid: change due, and GCash reference instead of cash amount
  const paid = document.querySelector("#paid-form");
  if (paid) {
    const due = Number(paid.dataset.due);
    const received = paid.querySelector("#amount_received");
    const change = paid.querySelector("#change");
    const update = () => {
      const gcash = paid.querySelector("input[name=method]:checked")?.value === "gcash";
      paid.querySelector("[data-method=cash]").hidden = gcash;
      paid.querySelector("[data-method=gcash]").hidden = !gcash;
      const diff = (Number(received.value.replace(/[^\d.]/g, "")) || 0) - due;
      change.textContent = peso(Math.max(diff, 0));
    };
    paid.addEventListener("change", update);
    received.addEventListener("input", update);
    update();
  }

  // Confirm weight pop-up (staff order details)
  const weightModal = document.querySelector("#weight-modal");
  if (weightModal) {
    const form = weightModal.querySelector("#weight-form");
    const input = form.querySelector("#actual_weight");
    const discard = document.querySelector("#discard-modal");
    const rate = Number(form.dataset.rate);
    const fee = Number(form.dataset.fee);
    const startValue = input.defaultValue;
    const update = () => {
      const kg = Number(input.value) || 0;
      document.querySelectorAll("[data-w=kg]").forEach((el) => (el.textContent = kg));
      form.querySelector("[data-w=laundry]").textContent = peso(rate * kg);
      form.querySelector("[data-w=total]").textContent = peso(rate * kg + fee);
    };
    const open = () => { input.value = startValue; update(); weightModal.showModal(); input.focus(); };
    // Cancel only asks for confirmation when the weight was changed
    const cancel = () => (input.value !== startValue ? discard.showModal() : weightModal.close());

    document.querySelector("#open-weight")?.addEventListener("click", open);
    input.addEventListener("input", update);
    weightModal.querySelectorAll("[data-cancel]").forEach((b) => b.addEventListener("click", cancel));
    weightModal.addEventListener("cancel", (e) => { e.preventDefault(); cancel(); }); // Esc key
    weightModal.addEventListener("click", (e) => { if (e.target === weightModal) cancel(); }); // click outside
    discard.querySelector("#keep-editing").addEventListener("click", () => { discard.close(); input.focus(); });
    discard.querySelector("#discard-weight").addEventListener("click", () => { discard.close(); weightModal.close(); });
    if (location.hash === "#confirm-weight" && document.querySelector("#open-weight")) open();
  }

  // Shop info: Save is disabled until something changes,
  // and leaving with unsaved changes asks first and shows what changed.
  const shopForm = document.querySelector("#shop-form");
  if (shopForm) {
    const saveBtn = document.querySelector("#save-shop");
    const dirtyHint = document.querySelector("#dirty-hint");
    const modal = document.querySelector("#unsaved-modal");
    const list = modal.querySelector("#changes-list");
    const fields = [...shopForm.querySelectorAll("input[name]:not([type=hidden])")];
    const labelOf = (el) => shopForm.querySelector(`label[for="${el.id}"]`)?.textContent.trim() || el.name;
    const valueOf = (el) => (el.type === "checkbox" ? (el.checked ? "On" : "Off") : el.value.trim());
    const saved = new Map(fields.map((el) => [el, valueOf(el)]));
    const changes = () => fields.filter((el) => valueOf(el) !== saved.get(el));
    let submitting = false;
    let pendingHref = null;

    const refresh = () => {
      const dirty = changes().length > 0;
      saveBtn.disabled = !dirty;
      dirtyHint.hidden = !dirty;
    };
    shopForm.addEventListener("input", refresh);
    shopForm.addEventListener("change", refresh);
    shopForm.addEventListener("submit", () => { submitting = true; });

    document.addEventListener("click", (e) => {
      const link = e.target.closest("a[href]");
      if (!link || !changes().length || link.getAttribute("href").startsWith("#")) return;
      e.preventDefault();
      pendingHref = link.getAttribute("href");
      modal.querySelector("#leave-to").textContent = link.getAttribute("aria-label") || link.textContent.trim();
      const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
      list.innerHTML = changes().map((el) =>
        `<li><span class="ch-label">${esc(labelOf(el))}</span>` +
        `<span><span class="ch-old">${esc(saved.get(el) || "(empty)")}</span> → <span class="ch-new">${esc(valueOf(el) || "(empty)")}</span></span></li>`
      ).join("");
      modal.showModal();
    });

    modal.querySelector("#keep-editing").addEventListener("click", () => { pendingHref = null; modal.close(); });
    modal.querySelector("#discard-leave").addEventListener("click", () => { submitting = true; location.href = pendingHref; });
    modal.querySelector("#save-leave").addEventListener("click", () => {
      // Save on the server, then go where the user clicked
      shopForm.querySelector("#shop-next").value = pendingHref;
      submitting = true;
      shopForm.requestSubmit();
    });

    // Browser back, refresh, or closing the tab
    window.addEventListener("beforeunload", (e) => {
      if (changes().length && !submitting) { e.preventDefault(); e.returnValue = ""; }
    });
  }
});
