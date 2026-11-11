// webcam.js runs the guided four-view scan
import {
    loadPose, detect, drawSkeleton, getAngles,
    checkFrame, frontalMetrics, requiredPoints
} from "./pose-tracker.js";

const API = "http://localhost:8000";

const $ = (id) => document.getElementById(id);
const video = $("video"), canvas = $("overlay");
const startBtn = $("startBtn"), titleEl = $("stepTitle");
const msgEl = $("message"), countEl = $("countdown"), statusEl = $("status");
const introEl = $("intro"), scanAreaEl = $("scanArea");
const stepsEl = $("steps"), retryBtn = $("retryBtn");

const VIEWS = [
    { id: "front", label: "Front",      instruction: "Face the camera with your arms relaxed at your sides." },
    { id: "left",  label: "Left side",  instruction: "Turn so your LEFT side faces the camera." },
    { id: "right", label: "Right side", instruction: "Turn so your RIGHT side faces the camera." },
    { id: "back",  label: "Back",       instruction: "Turn around so your back faces the camera." }
];

const GET_READY_MS = 8000;     // minimum time to get into position
const HOLD_MS = 1500;          // must be correctly positioned this long
const POSITION_TIMEOUT_MS = 40000;
const COUNTDOWN_SEC = 3;
const BURST_MS = 2000;         // how long to collect frames
const MAX_ATTEMPTS = 2;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const median = (arr) => [...arr].sort((a, b) => a - b)[Math.floor(arr.length / 2)];

let stream = null;          // the camera, so we can always turn it off
let pendingPayload = null;  // the finished scan, kept so "Try sending again" works

// ---------- screen switching ----------

// Show the camera screen and hide the intro card (or the other way round)
function showScanScreen(show) {
    introEl.hidden = show;
    scanAreaEl.hidden = !show;
}

// The step list next to the camera: done / active / skipped
function renderSteps(activeIndex, results = {}) {
    stepsEl.innerHTML = VIEWS.map((v, i) => {
        let cls = "", label = v.label;
        if (i < activeIndex) {
            if (results[v.id]) cls = "done";
            else label += " (skipped)";
        } else if (i === activeIndex) {
            cls = "active";
        }
        return `<li class="${cls}">${label}</li>`;
    }).join("");
}

function stopCamera() {
    if (stream) stream.getTracks().forEach((t) => t.stop());
    stream = null;
    video.srcObject = null;
    drawSkeleton(canvas, null);
}

// ---------- pose helpers ----------

// Resolves with landmarks (or null) for the next NEW camera frame
let lastVideoTime = -1;
function nextPose() {
    return new Promise((resolve) => {
        const tick = () => {
            if (video.currentTime === lastVideoTime) return requestAnimationFrame(tick);
            lastVideoTime = video.currentTime;
            resolve(detect(video, performance.now()));
        };
        requestAnimationFrame(tick);
    });
}

function meanMotion(a, b, viewId) {
    const pts = requiredPoints(viewId);
    return pts.reduce((s, i) => s + Math.hypot(a[i].x - b[i].x, a[i].y - b[i].y), 0) / pts.length;
}

// ---------- scan phases ----------

// Phase 1: give the person time, give live feedback, wait until they are set
async function positionPhase(view) {
    const start = performance.now();
    let okSince = null;
    while (true) {
        const lm = await nextPose();
        const now = performance.now();
        const elapsed = now - start;
        const check = lm
            ? checkFrame(lm, view.id)
            : { ok: false, hint: "I can't see you yet. Step into the frame." };

        // draw the skeleton whenever a body is detected, so people can see it tracking them
        drawSkeleton(canvas, lm);

        if (elapsed < GET_READY_MS) {
            countEl.textContent = Math.ceil((GET_READY_MS - elapsed) / 1000);
            msgEl.textContent = view.instruction;
            okSince = null;
            continue;
        }

        countEl.textContent = "";
        msgEl.textContent = check.hint;
        if (check.ok) {
            okSince ??= now;
            if (now - okSince >= HOLD_MS) return true;
        } else {
            okSince = null;
        }
        if (elapsed > POSITION_TIMEOUT_MS) return false;
    }
}

// Phase 2: 3-2-1
async function countdown() {
    for (let n = COUNTDOWN_SEC; n > 0; n--) {
        countEl.textContent = n;
        msgEl.textContent = "Hold still...";
        await sleep(1000);
    }
    countEl.textContent = "";
}

// Phase 3: burst of frames, keep the best few, return the median angles
async function captureBurst(view) {
    const frames = [];
    let prev = null;
    const t0 = performance.now();
    msgEl.textContent = "Capturing...";

    while (performance.now() - t0 < BURST_MS) {
        const lm = await nextPose();
        drawSkeleton(canvas, lm);
        if (!lm) continue;
        const check = checkFrame(lm, view.id);
        const motion = prev ? meanMotion(lm, prev, view.id) : 0;
        prev = lm;
        frames.push({
            lm,
            ok: check.ok,
            minVis: check.minVis,
            score: check.minVis - 10 * motion   // clear + still = high score
        });
    }

    const good = frames.filter((f) => f.ok).sort((a, b) => b.score - a.score).slice(0, 3);
    if (good.length === 0) return null;

    const w = video.videoWidth, h = video.videoHeight;
    const perFrame = good.map((f) =>
        view.id === "front" || view.id === "back"
            ? frontalMetrics(f.lm, w, h)
            : getAngles(f.lm, w, h, view.id)
    );

    // Median of the top frames for each measurement
    const angles = {};
    for (const key of Object.keys(perFrame[0])) {
        if (typeof perFrame[0][key] === "number" && key !== "visibility") {
            angles[key] = Number(median(perFrame.map((p) => p[key])).toFixed(1));
        }
    }

    // real visibility (0-1): average of the worst-seen joint in each kept frame
    const visibility = good.reduce((s, f) => s + f.minVis, 0) / good.length;

    return { angles, visibility: Number(visibility.toFixed(2)), framesUsed: good.length };
}

// ---------- sending to the backend ----------

async function sendScan(payload) {
    retryBtn.hidden = true;
    msgEl.textContent = "Analyzing your results...";
    try {
        const res = await fetch(`${API}/recommend`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error(`Server responded ${res.status}`);
        const report = await res.json();

        localStorage.setItem("lastResult", JSON.stringify(report));
        window.location.href = "results.html";
    } catch (err) {
        console.error(err);
        // keep the measurements so the person doesn't have to redo the scan
        msgEl.textContent = "Couldn't send your scan. Check the backend is running, then try again.";
        retryBtn.hidden = false;
    }
}

retryBtn.addEventListener("click", () => {
    if (pendingPayload) sendScan(pendingPayload);
});

// ---------- the main flow ----------

startBtn.addEventListener("click", async () => {
    startBtn.disabled = true;
    statusEl.textContent = "";
    pendingPayload = null;

    try {
        statusEl.textContent = "Loading pose model...";
        await loadPose();

        statusEl.textContent = "Asking for camera permission...";
        stream = await navigator.mediaDevices.getUserMedia({
            video: { width: 640, height: 480 }, audio: false
        });

        // swap the intro card for the camera screen BEFORE starting the video:
        // a video inside a hidden section may never start playing
        showScanScreen(true);
        retryBtn.hidden = true;
        titleEl.textContent = "Getting ready";
        msgEl.textContent = "Starting the camera...";

        video.srcObject = stream;
        await video.play();
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        statusEl.textContent = "";

        const results = {};
        for (let i = 0; i < VIEWS.length; i++) {
            const view = VIEWS[i];
            titleEl.textContent = `Step ${i + 1} of ${VIEWS.length}: ${view.label}`;
            renderSteps(i, results);
            results[view.id] = null;

            for (let attempt = 1; attempt <= MAX_ATTEMPTS && !results[view.id]; attempt++) {
                const ready = await positionPhase(view);
                if (!ready) {
                    msgEl.textContent = "Couldn't get set up. Skipping this view.";
                    await sleep(1500);
                    break;
                }
                await countdown();
                results[view.id] = await captureBurst(view);
                msgEl.textContent = results[view.id] ? "Got it!" : "That one wasn't clear. Let's try again.";
                await sleep(1200);
            }
        }

        stopCamera();
        renderSteps(VIEWS.length, results);
        titleEl.textContent = "Scan complete";

        // Build the payload the backend expects. Skipped views are left out.
        const payload = { test: "baseline_scan", capturedAt: new Date().toISOString(), views: {} };
        for (const [id, r] of Object.entries(results)) {
            if (r) payload.views[id] = r;
        }

        if (Object.keys(payload.views).length === 0) {
            msgEl.textContent = "No views were captured. Check your lighting and that your whole body is in frame, then try again.";
            startBtn.disabled = false;
            startBtn.textContent = "Try again";
            showScanScreen(false);
            statusEl.textContent = msgEl.textContent;
            return;
        }

        pendingPayload = payload;
        await sendScan(payload);
    } catch (err) {
        console.error(err);
        stopCamera();
        showScanScreen(false);
        statusEl.textContent = err.name === "NotAllowedError"
            ? "Camera permission was blocked. Click the camera icon in the address bar, allow it, then try again."
            : "Error: " + err.message;
        startBtn.disabled = false;
        startBtn.textContent = "Try again";
    }
});