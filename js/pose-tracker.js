// pose-tracker.js loads MediaPipe and turns landmarks into joint angles
import {
    PoseLandmarker, FilesetResolver, DrawingUtils
} from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/vision_bundle.mjs";

let landmarker = null;

const MODEL_URL =
    "https://storage.googleapis.com/mediapipe-tasks/pose_landmarker/pose_landmarker_lite.task";

export async function loadPose() {
    const fileset = await FilesetResolver.forVisionTasks(
        "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm"
    );

    const create = (delegate) =>
        PoseLandmarker.createFromOptions(fileset, {
            baseOptions: { modelAssetPath: MODEL_URL, delegate },
            runningMode: "VIDEO",
            numPoses: 1
        });

    try {
        landmarker = await create("GPU");
    } catch (err) {
        console.warn("GPU delegate failed, falling back to CPU:", err);
        landmarker = await create("CPU");
    }
}

export function detect(video, timestampMs) {
    if (!landmarker) return null;
    const results = landmarker.detectForVideo(video, timestampMs);
    return results.landmarks.length > 0 ? results.landmarks[0] : null;
}

export function drawSkeleton(canvas, landmarks) {
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!landmarks) return;
    const drawing = new DrawingUtils(ctx);
    drawing.drawConnectors(landmarks, PoseLandmarker.POSE_CONNECTIONS, {
        color: "#00ff00", lineWidth: 3
    });
    drawing.drawLandmarks(landmarks, { color: "#ff0000", radius: 3 });
}

// Angle at point b formed by a-b-c, in degrees.
// Landmarks are normalized (0-1), so scale by frame size first,
// otherwise x and y are stretched differently and the angle is wrong.
export function angle(a, b, c, w = 640, h = 480) {
    const radians =
        Math.atan2((c.y - b.y) * h, (c.x - b.x) * w) -
        Math.atan2((a.y - b.y) * h, (a.x - b.x) * w);
    let deg = Math.abs((radians * 180) / Math.PI);
    if (deg > 180) deg = 360 - deg;
    return deg;
}

// MediaPipe landmark indexes (left / right)
export const IDX = {
    left:  { shoulder: 11, hip: 23, knee: 25, ankle: 27, foot: 31 },
    right: { shoulder: 12, hip: 24, knee: 26, ankle: 28, foot: 32 }
};

// Side-view angles. Pass forceSide ("left"/"right") to pick a side,
// otherwise it uses whichever side the camera sees best.
export function getAngles(lm, w = 640, h = 480, forceSide = null) {
    const avgVis = (s) =>
        Object.values(IDX[s]).reduce((sum, i) => sum + (lm[i].visibility ?? 0), 0) / 5;
    const side = forceSide ?? (avgVis("left") > avgVis("right") ? "left" : "right");
    const p = IDX[side];
    return {
        side,
        visibility: avgVis(side),
        // ~180 = straight leg, ~90 = bent leg
        knee:  angle(lm[p.hip], lm[p.knee], lm[p.ankle], w, h),
        // ~180 = standing, ~90 = sitting
        hip:   angle(lm[p.shoulder], lm[p.hip], lm[p.knee], w, h),
        // ~90-100 = neutral standing
        ankle: angle(lm[p.knee], lm[p.ankle], lm[p.foot], w, h)
    };
}

// Which landmarks must be clearly visible for each view.
// Side views only need the side facing the camera.
export function requiredPoints(view) {
    const sides = view === "left" ? ["left"] : view === "right" ? ["right"] : ["left", "right"];
    return sides.flatMap((s) => Object.values(IDX[s]));
}

// Is the person actually in frame, big enough, and clearly seen?
export function checkFrame(lm, view, minVis = 0.6, margin = 0.02) {
    const pts = requiredPoints(view);
    let minV = 1, outside = false;
    for (const i of pts) {
        const p = lm[i];
        minV = Math.min(minV, p.visibility ?? 0);
        if (p.x < margin || p.x > 1 - margin || p.y < margin || p.y > 1 - margin) outside = true;
    }
    const shoulderY = (lm[11].y + lm[12].y) / 2;
    const ankleY = (lm[27].y + lm[28].y) / 2;
    const tooSmall = ankleY - shoulderY < 0.45;

    if (outside)   return { ok: false, minVis: minV, hint: "Step back so your whole body fits in the frame." };
    if (tooSmall)  return { ok: false, minVis: minV, hint: "Step a little closer." };
    if (minV < minVis) return { ok: false, minVis: minV, hint: "I can't see you clearly. Check the lighting and that nothing blocks your legs." };
    return { ok: true, minVis: minV, hint: "Good. Hold still..." };
}

// Front/back views: shoulder and hip tilt (degrees off horizontal)
// and knee alignment (about 180 = straight line hip-knee-ankle).
export function frontalMetrics(lm, w = 640, h = 480) {
    const tilt = (a, b) => {
        const [l, r] = a.x < b.x ? [a, b] : [b, a];
        return (Math.atan2((r.y - l.y) * h, (r.x - l.x) * w) * 180) / Math.PI;
    };
    return {
        shoulderTilt: tilt(lm[11], lm[12]),
        hipTilt: tilt(lm[23], lm[24]),
        leftKneeAlign: angle(lm[23], lm[25], lm[27], w, h),
        rightKneeAlign: angle(lm[24], lm[26], lm[28], w, h)
    };
}