const submitBtn = document.getElementById("submitBtn");
const resetBtn = document.getElementById("resetBtn");
const statusMsg = document.getElementById("statusMsg");
const resultCard = document.getElementById("resultCard");
const resultBody = document.getElementById("resultBody");
const officersGrid = document.getElementById("officersGrid");

const tabs = document.querySelectorAll(".tab");
const panelFile = document.getElementById("panel-file");
const panelTrack = document.getElementById("panel-track");

const trackBtn = document.getElementById("trackBtn");
const trackPhone = document.getElementById("trackPhone");
const trackResults = document.getElementById("trackResults");

// ---------- Tabs ----------
tabs.forEach((btn) => {
  btn.addEventListener("click", () => {
    tabs.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    const isFile = btn.dataset.tab === "file";
    panelFile.hidden = !isFile;
    panelTrack.hidden = isFile;
  });
});

// ---------- Officers ----------
async function loadOfficers() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/officers`);
    const officers = await res.json();
    officersGrid.innerHTML = officers
      .map((o) => {
        const isFree = o.status === "active";
        const cls = isFree ? `officer free ${o.department}` : "officer busy";
        const meta = isFree ? `${o.department} \u00b7 free ${o.next_slot}` : `${o.department} \u00b7 busy`;
        return `<div class="${cls}"><div class="name">${o.officer_name}</div><div class="meta">${meta}</div></div>`;
      })
      .join("");
  } catch (err) {
    officersGrid.innerHTML = `<p class="status">Couldn't reach the backend at ${API_BASE_URL}. It may be waking up \u2014 wait 30s and refresh.</p>`;
  }
}

// ---------- File a report ----------
async function submitReport() {
  const name = document.getElementById("name").value.trim() || "Resident";
  const phone = document.getElementById("phone").value.trim();
  const zone = document.getElementById("zone").value.trim() || "unspecified zone";
  const issue = document.getElementById("issue").value.trim();

  if (!issue) {
    statusMsg.textContent = "Describe the issue before filing a report.";
    return;
  }
  if (!phone) {
    statusMsg.textContent = "Add a phone number so you can track this report later.";
    return;
  }

  statusMsg.textContent = "Gemini is classifying your report...";
  submitBtn.disabled = true;

  try {
    const res = await fetch(`${API_BASE_URL}/api/checkin`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, phone, zone, issue }),
    });

    if (!res.ok) throw new Error("Request failed");
    const data = await res.json();

    statusMsg.textContent = "";
    resultCard.hidden = false;
    resultBody.innerHTML = renderTicket(data);
    loadOfficers();
  } catch (err) {
    statusMsg.textContent = `Couldn't reach the backend. It may be waking up (free-tier servers sleep when idle) \u2014 wait 30\u201350s and try again.`;
  } finally {
    submitBtn.disabled = false;
  }
}

function renderTicket(data) {
  const badgeClass = data.urgency === "hazard" ? "hazard" : "routine";
  const badgeLabel = data.urgency === "hazard" ? "HAZARD \u2014 top priority" : "Routine";
  const officerLine =
    data.assigned_officer && data.assigned_officer !== "none - queued"
      ? `Assigned to <strong>${data.assigned_officer}</strong>.`
      : "No officer free right now \u2014 queued, will auto-escalate on SLA breach.";

  return `
    <p class="ticket-id">${data.ticket_id} &middot; filed ${data.filed_at}</p>
    <p class="ticket-route">
      <span class="badge ${badgeClass}">${badgeLabel}</span>
      Routed to <strong>${data.department}</strong>
    </p>
    <p class="reasoning">${data.reasoning}</p>
    <p class="officer-line">${officerLine}</p>
  `;
}

// ---------- Track my reports ----------
async function searchTickets() {
  const phone = trackPhone.value.trim();
  if (!phone) {
    trackResults.innerHTML = `<p class="empty-state">Enter the phone number you used when filing a report.</p>`;
    return;
  }

  trackResults.innerHTML = `<p class="empty-state">Searching...</p>`;

  try {
    const res = await fetch(`${API_BASE_URL}/api/tickets?phone=${encodeURIComponent(phone)}`);
    const results = await res.json();

    if (!results.length) {
      trackResults.innerHTML = `<p class="empty-state">No reports found for this number yet.</p>`;
      return;
    }

    trackResults.innerHTML = results
      .slice()
      .reverse()
      .map((t) => {
        const cls = t.urgency === "hazard" ? "hazard" : "routine";
        return `
          <div class="track-ticket ${cls}">
            <div class="meta">${t.ticket_id} &middot; ${t.filed_at} &middot; ${t.department}</div>
            <p class="issue">${t.issue}</p>
            <div class="officer">${t.assigned_officer && t.assigned_officer !== "none - queued" ? "Assigned to " + t.assigned_officer : "Queued"}</div>
          </div>
        `;
      })
      .join("");
  } catch (err) {
    trackResults.innerHTML = `<p class="status">Couldn't reach the backend at ${API_BASE_URL}.</p>`;
  }
}

// ---------- Reset ----------
async function resetAll() {
  await fetch(`${API_BASE_URL}/api/reset`, { method: "POST" });
  resultCard.hidden = true;
  statusMsg.textContent = "";
  trackResults.innerHTML = "";
  loadOfficers();
}

submitBtn.addEventListener("click", submitReport);
resetBtn.addEventListener("click", resetAll);
trackBtn.addEventListener("click", searchTickets);

loadOfficers();
