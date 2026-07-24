const submitBtn = document.getElementById("submitBtn");
const resetBtn = document.getElementById("resetBtn");
const statusMsg = document.getElementById("statusMsg");
const resultCard = document.getElementById("resultCard");
const resultBody = document.getElementById("resultBody");
const officersGrid = document.getElementById("officersGrid");

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
    officersGrid.innerHTML = `<p class="status">Couldn't reach the backend at ${API_BASE_URL}. Check config.js.</p>`;
  }
}

async function submitReport() {
  const name = document.getElementById("name").value.trim() || "Resident";
  const zone = document.getElementById("zone").value.trim() || "unspecified zone";
  const issue = document.getElementById("issue").value.trim();

  if (!issue) {
    statusMsg.textContent = "Describe the issue before filing a report.";
    return;
  }

  statusMsg.textContent = "Routing your report...";
  submitBtn.disabled = true;

  try {
    const res = await fetch(`${API_BASE_URL}/api/checkin`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, zone, issue }),
    });

    if (!res.ok) throw new Error("Request failed");
    const data = await res.json();

    statusMsg.textContent = "";
    resultCard.hidden = false;

    const ticketId = "CR-" + Math.floor(1000 + Math.random() * 9000);
    const badgeClass = data.urgency === "hazard" ? "hazard" : "routine";
    const badgeLabel = data.urgency === "hazard" ? "HAZARD \u2014 top priority" : "Routine";

    resultBody.innerHTML = `
      <p class="ticket-id">Ticket ${ticketId} &middot; ${data.name} &middot; ${data.zone}</p>
      <p class="ticket-route">
        <span class="badge ${badgeClass}">${badgeLabel}</span>
        Routed to <strong>${data.department}</strong>
      </p>
      <p class="status" style="color: var(--sub)">${data.reasoning}</p>
      <p>${data.assigned_officer && data.assigned_officer !== "none - queued"
        ? `Assigned to <strong>${data.assigned_officer}</strong>.`
        : "No officer free right now \u2014 queued, will auto-escalate on SLA breach."}
      </p>
    `;

    loadOfficers();
  } catch (err) {
    statusMsg.textContent = `Couldn't reach the backend at ${API_BASE_URL}. Check config.js and that the backend is running.`;
  } finally {
    submitBtn.disabled = false;
  }
}

async function resetOfficers() {
  await fetch(`${API_BASE_URL}/api/reset`, { method: "POST" });
  resultCard.hidden = true;
  statusMsg.textContent = "";
  loadOfficers();
}

submitBtn.addEventListener("click", submitReport);
resetBtn.addEventListener("click", resetOfficers);

loadOfficers();
