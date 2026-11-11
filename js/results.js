// results.js - shows the report card the backend sent back after a scan,
// plus a chat box for questions about the results.
import { renderAppShell } from "./ui.js";
renderAppShell("results");

const API = "http://localhost:8000";
const content = document.getElementById("content");
const report = JSON.parse(localStorage.getItem("lastResult") || "null");

// ---------- helpers ----------

// make text safe to put inside HTML
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const VIEW_LABELS = { front: "Front", left: "Left side", right: "Right side", back: "Back" };

// plain-language names + a short explanation for every angle the scan measures
const ANGLE_INFO = {
    knee:           { label: "Knee extension",       hint: "How straight the leg is. Fully straight is close to 180°." },
    hip:            { label: "Hip extension",        hint: "How upright the hip sits from the side." },
    ankle:          { label: "Ankle angle",          hint: "Angle between shin and foot." },
    shoulderTilt:   { label: "Shoulder level",       hint: "Degrees off level. 0° means perfectly level." },
    hipTilt:        { label: "Hip level",            hint: "Degrees off level. 0° means perfectly level." },
    leftKneeAlign:  { label: "Left knee alignment",  hint: "Hip-knee-ankle line. About 180° is a straight line." },
    rightKneeAlign: { label: "Right knee alignment", hint: "Hip-knee-ankle line. About 180° is a straight line." },
};
const angleLabel = (a) => ANGLE_INFO[a]?.label ?? a;
const angleHint = (a) => ANGLE_INFO[a]?.hint ?? "";
const deg = (v) => `${Number(v).toFixed(1)}°`;

// how far along the bar to draw a value: the healthy range sits in the middle third
function barPercent(value, range) {
    if (!range) return 50;
    const [low, high] = range;
    const span = Math.max(high - low, 1);
    const min = low - span, max = high + span;
    return Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));
}

function chip(status) {
    if (status === "ok") return `<span class="chip ok">In range</span>`;
    if (status === "watch") return `<span class="chip watch">Worth a look</span>`;
    return `<span class="chip info">For reference</span>`;
}

function visibilityChip(v) {
    if (v >= 0.8) return `<span class="chip ok">Clear view</span>`;
    if (v >= 0.6) return `<span class="chip info">OK view</span>`;
    return `<span class="chip watch">Low visibility</span>`;
}

const ICON_OK = `<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12 5 5 9-10"/></svg>`;
const ICON_WATCH = `<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16h.01"/></svg>`;

// ---------- sections ----------

function summarySection() {
    const n = report.flags.length;
    const viewCount = Object.keys(report.views || {}).length;
    const missed = 4 - viewCount;
    const text = n === 0
        ? `Everything we measured was within the typical range.`
        : `${n} measurement${n > 1 ? "s" : ""} stood out. See what's below and the stretches that can help.`;
    const missedText = missed > 0
        ? ` ${missed} view${missed > 1 ? "s were" : " was"} skipped, so a re-scan may show more.`
        : "";
    return `
        <div class="summary ${n === 0 ? "ok" : "watch"}">
            <span class="icon">${n === 0 ? ICON_OK : ICON_WATCH}</span>
            <p>${esc(text + missedText)}</p>
        </div>`;
}

function findingsSection() {
    if (report.flags.length === 0) return "";
    const items = report.flags.map((f) => {
        const [low, high] = f.healthy_range;
        const direction = f.measured < low ? "below" : "above";
        return `
            <li class="finding">
                <strong>${esc(VIEW_LABELS[f.view] ?? f.view)} · ${esc(angleLabel(f.angle))}</strong>
                <p>Measured ${deg(f.measured)}, a little ${direction} the typical ${low}–${high}° range. ${esc(angleHint(f.angle))}</p>
            </li>`;
    }).join("");
    return `<h2 class="section-title">What stood out</h2><ul class="findings">${items}</ul>`;
}

function measurementsSection() {
    const byView = {};
    for (const m of report.measurements) (byView[m.view] ??= []).push(m);

    const cards = ["front", "left", "right", "back"].filter((v) => byView[v]).map((view) => {
        const info = report.views?.[view];
        const metrics = byView[view].map((m) => `
            <li class="metric">
                <div class="metric-top">
                    <div>
                        <div class="metric-label">${esc(angleLabel(m.angle))}</div>
                        <div class="metric-hint">${m.healthy_range ? `Typical ${m.healthy_range[0]}–${m.healthy_range[1]}°` : "No typical range set yet"}</div>
                    </div>
                    <div class="metric-right">
                        <span class="metric-value">${deg(m.measured)}</span>
                        ${chip(m.status)}
                    </div>
                </div>
                <div class="bar ${m.status === "watch" ? "watch" : ""}"><span style="width:${barPercent(m.measured, m.healthy_range)}%"></span></div>
            </li>`).join("");
        return `
            <section class="card">
                <div class="view-head">
                    <h3>${esc(VIEW_LABELS[view] ?? view)}</h3>
                    ${info ? visibilityChip(info.visibility) : ""}
                </div>
                <ul class="metrics">${metrics}</ul>
            </section>`;
    }).join("");

    return `<h2 class="section-title">Your measurements</h2><div class="grid views">${cards}</div>`;
}

// side-by-side left vs right, when both sides were captured
function leftRightSection() {
    const get = (view, angle) => report.measurements.find((m) => m.view === view && m.angle === angle)?.measured;
    const pairs = [];
    for (const angle of ["knee", "hip", "ankle"]) {
        const l = get("left", angle), r = get("right", angle);
        if (l != null && r != null) pairs.push({ label: angleLabel(angle), l, r });
    }
    const la = get("front", "leftKneeAlign"), ra = get("front", "rightKneeAlign");
    if (la != null && ra != null) pairs.push({ label: "Knee alignment (front)", l: la, r: ra });
    if (pairs.length === 0) return "";

    const rows = pairs.map((p) => {
        const diff = Math.abs(p.l - p.r);
        return `
            <li class="metric">
                <div class="metric-top">
                    <div class="metric-label">${esc(p.label)}</div>
                    <div class="metric-right">
                        <span class="metric-hint">L ${deg(p.l)} · R ${deg(p.r)}</span>
                        <span class="chip ${diff > 5 ? "watch" : "ok"}">${diff.toFixed(1)}° apart</span>
                    </div>
                </div>
            </li>`;
    }).join("");
    return `
        <h2 class="section-title">Left vs right</h2>
        <section class="card">
            <p class="muted" style="margin-top:0">Big differences between sides can be worth keeping an eye on. Webcam measurements can be off by a few degrees.</p>
            <ul class="metrics">${rows}</ul>
        </section>`;
}

function planSection() {
    const plan = report.plan || [];
    if (plan.length === 0) return "";
    const title = report.planType === "maintenance" ? "A short routine to keep moving well" : "Recommended stretches";
    const items = plan.map((s) => `
        <article class="plan-item">
            <h3>${esc(s.name)}</h3>
            <p>${esc(s.how)}</p>
            <p class="dose">${esc(s.dose)}</p>
            <p class="metric-hint">For: ${esc(s.joints.join(", "))}</p>
        </article>`).join("");
    return `
        <h2 class="section-title">${esc(title)}</h2>
        <div class="grid plan">${items}</div>
        <div class="card" style="display:flex; align-items:center; justify-content:space-between; gap:16px; flex-wrap:wrap; margin-top:20px">
            <div>
                <strong style="color:var(--ink)">Questions about your plan?</strong>
                <p class="muted" style="margin:4px 0 0">Ask why a stretch was picked or what a measurement means.</p>
            </div>
            <button class="btn btn-accent" type="button" data-open-chat>Ask the assistant</button>
        </div>`;
}

// ---------- chat ----------

// Extra styles for the chat launcher, suggestion chips and open animation.
// (Kept here so this page works with the existing style.css; could move there later.)
const CHAT_CSS = `
.chat-launcher {
    position: fixed; right: 24px; bottom: 24px; z-index: 70;
    display: inline-flex; align-items: center; height: 56px; padding: 0 16px;
    border: 0; border-radius: 999px; background: var(--accent); color: #fff;
    font: inherit; font-weight: 600; cursor: pointer;
    box-shadow: 0 10px 28px rgba(238, 108, 77, 0.35);
    transition: background 0.15s, box-shadow 0.15s;
}
.chat-launcher:hover, .chat-launcher:focus-visible { background: var(--accent-dark); }
.chat-launcher .icon { width: 24px; height: 24px; }
.chat-launcher .label {
    max-width: 0; overflow: hidden; white-space: nowrap; opacity: 0;
    transition: max-width 0.25s ease, opacity 0.2s ease, margin 0.25s ease;
}
.chat-launcher:hover .label, .chat-launcher:focus-visible .label {
    max-width: 220px; opacity: 1; margin-left: 10px;
}
.chat-panel { opacity: 0; transform: translateY(16px) scale(0.98); transform-origin: bottom right;
    transition: opacity 0.2s ease, transform 0.2s ease; }
.chat-panel.open { opacity: 1; transform: none; }
.chat-suggestions { display: flex; flex-direction: column; align-items: flex-start; gap: 8px; }
.chat-chip {
    padding: 8px 12px; border: 1px solid #bfe0da; border-radius: 999px;
    background: var(--surface); color: var(--primary-dark);
    font: inherit; font-size: 0.85rem; font-weight: 500; text-align: left; cursor: pointer;
}
.chat-chip:hover { background: var(--primary-soft); }
@media (prefers-reduced-motion: reduce) {
    .chat-panel, .chat-launcher .label { transition: none; }
}`;

const ICON_CHAT = `<svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z"/><path d="M8.5 11h.01M12 11h.01M15.5 11h.01"/></svg>`;

// Suggested questions, based on THIS person's results
function suggestedQuestions() {
    const qs = [];
    const flag = report.flags[0];
    const firstStretch = report.plan?.[0]?.name;

    if (flag) {
        if (firstStretch) qs.push(`Why was the ${firstStretch.toLowerCase()} picked for me?`);
        qs.push(`What does my ${angleLabel(flag.angle).toLowerCase()} result mean?`);
    } else {
        qs.push("Why these stretches if everything is in range?");
        if (firstStretch) qs.push(`How often should I do the ${firstStretch.toLowerCase()}?`);
    }

    // biggest left/right difference, if both sides were captured
    let biggest = null;
    for (const angle of ["knee", "hip", "ankle"]) {
        const l = report.measurements.find((m) => m.view === "left" && m.angle === angle)?.measured;
        const r = report.measurements.find((m) => m.view === "right" && m.angle === angle)?.measured;
        if (l != null && r != null) {
            const diff = Math.abs(l - r);
            if (!biggest || diff > biggest.diff) biggest = { angle, diff };
        }
    }
    if (biggest && biggest.diff >= 1) {
        qs.push(`Is a ${biggest.diff.toFixed(1)}° difference between my left and right ${biggest.angle} normal?`);
    }
    return qs.slice(0, 3);
}

function setupChat() {
    const style = document.createElement("style");
    style.textContent = CHAT_CSS;
    document.head.append(style);

    // leave empty space at the bottom of the page so the floating
    // button never sits on top of the last bit of text
    content.style.paddingBottom = "120px";

    // round button with a chat icon; the label slides out on hover
    const launcher = document.createElement("button");
    launcher.className = "chat-launcher";
    launcher.type = "button";
    launcher.setAttribute("aria-label", "Ask about my results");
    launcher.innerHTML = `<span class="icon">${ICON_CHAT}</span><span class="label">Ask about my results</span>`;

    const panel = document.createElement("div");
    panel.className = "chat-panel";
    panel.hidden = true;
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-label", "Results assistant");
    panel.innerHTML = `
        <div class="chat-head">
            <strong>Results assistant</strong>
            <button class="chat-close" type="button" aria-label="Close chat">&times;</button>
        </div>
        <div class="chat-messages" id="chatMessages"></div>
        <p class="chat-note">Answers are general information, not medical advice.</p>
        <form class="chat-form" id="chatForm">
            <input class="chat-input" id="chatInput" placeholder="Ask a question..." autocomplete="off" required>
            <button class="btn btn-sm" type="submit">Send</button>
        </form>`;
    document.body.append(launcher, panel);

    const messages = panel.querySelector("#chatMessages");
    const form = panel.querySelector("#chatForm");
    const input = panel.querySelector("#chatInput");

    const addMsg = (text, cls) => {
        const div = document.createElement("div");
        div.className = `msg ${cls}`;
        div.textContent = text;  // textContent = safe, no HTML injection
        messages.append(div);
        messages.scrollTop = messages.scrollHeight;
        return div;
    };

    addMsg("Hi! Ask me what a measurement means or why a stretch was recommended. Here are a few ideas:", "bot");

    // tappable suggested questions
    const suggestions = document.createElement("div");
    suggestions.className = "chat-suggestions";
    for (const q of suggestedQuestions()) {
        const chipBtn = document.createElement("button");
        chipBtn.type = "button";
        chipBtn.className = "chat-chip";
        chipBtn.textContent = q;
        chipBtn.addEventListener("click", () => ask(q));
        suggestions.append(chipBtn);
    }
    messages.append(suggestions);

    // open with a short slide-up, close the same way
    const openChat = () => {
        panel.hidden = false;
        launcher.hidden = true;
        requestAnimationFrame(() => panel.classList.add("open"));
        input.focus();
    };
    const closeChat = () => {
        panel.classList.remove("open");
        setTimeout(() => { panel.hidden = true; launcher.hidden = false; launcher.focus(); }, 200);
    };
    launcher.addEventListener("click", openChat);
    panel.querySelector(".chat-close").addEventListener("click", closeChat);
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !panel.hidden) closeChat(); });
    // the "Ask the assistant" button under the stretch plan opens the same chat
    document.querySelectorAll("[data-open-chat]").forEach((b) => b.addEventListener("click", openChat));

    // context about this scan, so the answer can be about YOUR results
    const firstFlag = report.flags[0];
    const context = {
        joint: firstFlag?.joint ?? report.plan?.[0]?.joints?.[0] ?? null,
        angle: firstFlag?.measured ?? null,
        exercises: (report.plan || []).map((s) => s.name),
    };

    async function ask(question) {
        suggestions.remove();  // chips disappear after the first question
        addMsg(question, "user");
        const pending = addMsg("Thinking...", "bot pending");

        try {
            const res = await fetch(`${API}/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question, ...context }),
            });
            if (!res.ok) throw new Error(`Server responded ${res.status}`);
            const data = await res.json();
            pending.remove();
            if (data.error) {
                addMsg(data.error, "bot error");
            } else {
                let text = data.answer;
                if (data.sources?.length) {
                    text += "\n\nSources:\n" + data.sources.map((s) => `${s.id}: ${s.citation}`).join("\n");
                }
                addMsg(text, "bot");
            }
        } catch (err) {
            console.error(err);
            pending.remove();
            addMsg("Can't reach the assistant right now. Is the backend running?", "bot error");
        }
    }

    form.addEventListener("submit", (e) => {
        e.preventDefault();
        const question = input.value.trim();
        if (!question) return;
        input.value = "";
        ask(question);
    });
}

// ---------- render ----------

if (!report) {
    content.innerHTML = `
        <div class="empty">
            <h2>No results yet</h2>
            <p>Do a scan first and your results will show up here.</p>
            <a href="scan.html" class="btn">Start a scan</a>
        </div>`;
} else if (!report.measurements) {
    // a report saved before the backend sent full measurements
    content.innerHTML = `
        <div class="empty">
            <h2>Your last scan is from an older version</h2>
            <p>Run a new scan to see your full results.</p>
            <a href="scan.html" class="btn">Scan again</a>
        </div>`;
} else {
    content.innerHTML = `
        <div class="page-head">
            <div>
                <h1>Your results</h1>
                <p class="muted">${esc(new Date(report.capturedAt).toLocaleString())} · ${Object.keys(report.views || {}).length} of 4 views captured</p>
            </div>
            <div style="display:flex; gap:10px; flex-wrap:wrap">
                <a href="scan.html" class="btn btn-secondary">Scan again</a>
                <a href="dashboard.html" class="btn">Dashboard</a>
            </div>
        </div>
        ${summarySection()}
        ${findingsSection()}
        ${planSection()}
        ${measurementsSection()}
        ${leftRightSection()}
        <p class="disclaimer">
            These are rough webcam estimates, not a diagnosis. If you have pain or an injury,
            talk to a doctor or physical therapist before starting any exercise.
        </p>`;
    setupChat();
}