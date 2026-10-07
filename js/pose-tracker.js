// pose tracker.js loads the MediaPipe and turns specific landmarks into the joint angles
import {
    PoseLandmarker, FilesetResolver, DrawingUtils
} from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/vision_bundle.mjs";
 
let landmarker = null;

export async function loadPose() {
    const fileset = await FilesetResolver.forVisionTasks (
        "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm"
    );
    landmarker = await PoseLandmarker.createFromOptions(fileset, {
        baseOptions: {
            modelAssetPath:
                "https://storage.googleapis.com/mediapipe-tasks/pose_landmarker/pose_landmarker_lite.task",
                delegate: "GPU"
        },
        runningMode : "VIDEO",
        numPoses: 1
    });
}

export function detect (video, timestampMs) {
    if (!landmarker) return null;
    const results = landmarker.detectForVideo(video, timestampMs);
    return results.landmarks.length > 0 ? result.landmarks[0] : null;
}

export function drawSkeleton(canvas, landmarks) {
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!landmarks) return;
    const drawing = new DrawingUtils(ctx);
    drawing.drawConnectors(landmarks, Poselandmarker.POSE_CONNECTIONS, {color: "00ff00", lineWidth: 3});
    drawing.drawLandmarks(landmarks, {color: "ff0000", radius: 3}); 
}

// The angle at point b is formed by points a-b-c in degrees
export function angle(a, b, c) {
    const radians = Math.atan2(c.y - b.y, c.x - b.x) - Math.atan2(a.y - b.y, a.x - b.x);
    let deg = Math.abs ((radians * 180) / Math.PI);
    if (deg > 180) deg = 360 - deg;
    return deg;
}

// Media Pipe landmark index (left / right)
const IDX = {
    left : { shoulder : 11, hip : 23, knee : 25, ankle : 27, foot : 31 },
    right : { shoulder : 12, hip : 24, knee : 26, ankle : 28, foot : 32 }
};

// side friendly view -- Use whichever side the camera sees best
export function getAngles(lm) {
    const avgVIS = (s) =>
        Object.values(IDX[s]).reduce((sum, i) => sum + (lm[i].visibility ?? 0),0) / 5;
    const side = avgVis("left") > avgVIS("right") ? "left" : "right";
    const p = IDX[side];
    return {
        side,
        visibility : avgVIS(side),
        // ~180 = straight leg, ~90 = bent leg
        knee : angle(lm[p.hip], lm[p.knee], lm[p.ankle]), 
        // ~180 = standing, ~90 = sitting
        hip : angle(lm[p.shoulder], lm[p.hip], lm[p.knee]),
        // ~90-100 = neutral standing
        ankle : angle(lm[p.knee], lm[p.ankle], lm[p.foot])    
    };
}