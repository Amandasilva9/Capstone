// dashboard.js - fills the dashboard with the user's real scan history from /history
const username = localStorage.getItem("username") || "";
const historyEl = document.getElementById("history");
const trendEl = document.getElementById("trend");
const planEl = document.getElementById("plan");

async function loadHistory() {
    try {
        const res = await fetch("http://localhost:8000/history?username=" + encodeURIComponent(username));
        const data = await res.json();

        if (data.count === 0) {
            historyEl.innerHTML = `<p class="muted">Hi ${username} - no scans yet. Do your first scan to see history here.</p>`;
            return;
        }

        // one line per scan: date + restricted or clear
        historyEl.innerHTML = data.scans.map(s => `
            <p>${new Date(s.capturedAt).toLocaleString()} —
            ${s.restricted ? "⚠️ limitations found" : "✓ all clear"}</p>
        `).join("");

        // newest scan's plan fills the plan card
        const latest = data.scans[0].report;
        planEl.innerHTML = latest.plan && latest.plan.length
            ? "<ul>" + latest.plan.map(p => `<li><strong>${p.name}</strong> — ${p.dose}</li>`).join("") + "</ul>"
            : `<p class="muted">No plan yet.</p>`;

        trendEl.innerHTML = `<p class="muted">${data.count} scan${data.count > 1 ? "s" : ""} recorded — trends coming soon.</p>`;
    } catch {
        historyEl.innerHTML = `<p class="muted">Can't reach the server — is the backend running?</p>`;
    }
}

loadHistory();