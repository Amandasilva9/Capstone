// results.js - shows the report card the backend sent back after a scan
const content = document.getElementById("content");
const report = JSON.parse(localStorage.getItem("lastResult") || "null");

if (!report) {
    content.innerHTML = `<p class="muted">No results yet - <a href="scan.html">do a scan</a> first.</p>`;
} else {
    const flagList = report.flags.length
        ? report.flags.map(f =>
            `<li><strong>${f.view} ${f.angle}</strong>: measured ${f.measured}°, healthy is ${f.healthy_range[0]}–${f.healthy_range[1]}°</li>`
          ).join("")
        : "<li>Everything measured within the healthy range. Nice.</li>";

    const stretchList = report.stretches.map(s => `<li>${s}</li>`).join("");

    content.innerHTML = `
        <h1>Your results</h1>
        <p class="muted">Scan: ${report.test} · ${new Date(report.capturedAt).toLocaleString()}</p>
        <h2>${report.restricted ? "Limitations found" : "No limitations found"}</h2>
        <ul>${flagList}</ul>
        <h2>Recommended stretches</h2>
        <ul>${stretchList}</ul>
        <p><a href="scan.html" class="btn">Scan again</a> <a href="dashboard.html" class="btn">Back to dashboard</a></p>
    `;
}