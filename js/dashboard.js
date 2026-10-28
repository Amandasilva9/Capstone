// dashboard.js - fills the dashboard. placeholder until the /history endpoint is ready
const username = localStorage.getItem("username") || "there";
document.getElementById("history").innerHTML = `<p class="muted">Hi ${username} - no scans yet. Do your first scan to see history here.</p>`;
document.getElementById("trend").innerHTML = `<p class="muted">Trends will appear after a few scans.</p>`;
document.getElementById("plan").innerHTML = `<p class="muted">Your plan will appear after your first scan flags something.</p>`;