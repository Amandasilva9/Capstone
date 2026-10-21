// webcam.js runs the guided four-view scan
import {
    loadPose, detect, drawSkeleton, getAngles,
    checkFrame, frontalMetrics, requiredPoints
} from "./pose-tracker.js";

const $ = (id) => document.getElementById(id);
const video = $("video"), canvas = $("overlay");
const startBtn = $("startBtn"), titleEl = $("stepTitle");
const msgEl = $("message"), countEl = $("countdown"), statusEl = $("status");

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

function snapshot() {
    const c = document.createElement("canvas");
    c.width = video.videoWidth;
    c.height = video.videoHeight;
    c.getContext("2d").drawImage(video, 0, 0);
    return c.toDataURL("image/jpeg", 0.85);
}

function meanMotion(a, b, viewId) {
    const pts = requiredPoints(viewId);
    return pts.reduce((s, i) => s + Math.hypot(a[i].x - b[i].x, a[i].y - b[i].y), 0) / pts.length;
}

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

        drawSkeleton(canvas, check.ok ? lm : null);   // only draw when the body is really there

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
    drawSkeleton(canvas, null);
    for (let n = COUNTDOWN_SEC; n > 0; n--) {
        countEl.textContent = n;
        msgEl.textContent = "Hold still...";
        await sleep(1000);
    }
    countEl.textContent = "";
}

// Phase 3: burst of frames, keep the best few
async function captureBurst(view) {
    const frames = [];
    let prev = null, best = null;
    const t0 = performance.now();
    msgEl.textContent = "Capturing...";

    while (performance.now() - t0 < BURST_MS) {
        const lm = await nextPose();
        if (!lm) continue;
        const check = checkFrame(lm, view.id);
        const motion = prev ? meanMotion(lm, prev, view.id) : 0;
        prev = lm;
        const score = check.minVis - 10 * motion;   // clear + still = high score
        const f = { lm, score, ok: check.ok };
        frames.push(f);
        if (check.ok && (!best || score > best.score)) {
            best = f;
            best.image = snapshot();
        }
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
    return {
        angles,
        visibility: Number(best.score.toFixed(2)),
        framesUsed: good.length,
        image: best.image
    };
}

startBtn.addEventListener("click", async () => {
    startBtn.disabled = true;
    try {
        statusEl.textContent = "Loading pose model...";
        await loadPose();
        statusEl.textContent = "Asking for camera permission...";
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { width: 640, height: 480 }, audio: false
        });
        video.srcObject = stream;
        await video.play();
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        statusEl.textContent = "";

        const results = {};
        for (let i = 0; i < VIEWS.length; i++) {
            const view = VIEWS[i];
            titleEl.textContent = `Step ${i + 1} of ${VIEWS.length}: ${view.label}`;
            results[view.id] = null;

            for (let attempt = 1; attempt <= MAX_ATTEMPTS && !results[view.id]; attempt++) {
                const ready = await positionPhase(view);
                if (!ready) { msgEl.textContent = "Couldn't get set up. Skipping this view."; await sleep(1500); break; }
                await countdown();
                results[view.id] = await captureBurst(view);
                msgEl.textContent = results[view.id] ? "Got it!" : "That one wasn't clear. Let's try again.";
                await sleep(1200);
            }
        }

        stream.getTracks().forEach((t) => t.stop());
        drawSkeleton(canvas, null);
        titleEl.textContent = "Scan complete";
        msgEl.textContent = "Done.";

        // Payload without the images (send images separately if the backend wants them)
        const payload = { capturedAt: new Date().toISOString(), views: {} };
        for (const [id, r] of Object.entries(results)) {
            payload.views[id] = r ? { angles: r.angles, visibility: r.visibility, framesUsed: r.framesUsed } : null;
        }
        console.log("Payload:", payload);
        console.log("Images:", Object.fromEntries(Object.entries(results).map(([k, r]) => [k, r?.image])));
        $("results").textContent = JSON.stringify(payload, null, 2);
        startBtn.disabled = false;
        startBtn.textContent = "Scan again";
    } catch (err) {
        console.error(err);
        statusEl.textContent = "Error: " + err.message;
        startBtn.disabled = false;
    }
});