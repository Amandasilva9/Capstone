// webcam.js will start the camera and run the live tracking loop
import { loadPose, detect, drawSkeleton, getAngles } from "./pose-tracker.js";

const video = document.getElementById("video");
const canvas = document.getElementById("overlay");
const statusE1 = document.getElementById("status");
const startBtn = document.getElementById("startBtn");

let frames = 0, lastFpsTime = performance.now();

startBtn.addEventListener("click", async () => {
    try {
        startBtn.disabled = true;
        statusE1.textContent = "Loading MediaPipe model...";
        await loadPose();

        statusE1.textContent = "Asking for camera permission...";
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { width: 640, height: 480 }, audio: false
        });
        video.srcObject = stream;
        await video.play();

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        statusE1.textContent = "Tracking. Stand with your whole body visible, side-on to the camera.";
        requestAnimationFrame(loop);
    } catch (err) {
        console.error(err);
        statusE1.textContent = "Error: " + err.message;
        startBtn.disabled = false;
    }
});

function loop () {
    const lm = detect(video, performance.now());
    drawSkeleton(canvas, lm);

    if (lm) {
        const a = getAngles(lm);
        $("side").textContent = a.side;
        $("knee").textContent = a.knee.toFixed(1) + "°";
        $("hip").textContent = a.hip.toFixed(1) + "°";
        $("ankle").textContent = a.ankle.toFixed(1) + "°";
        $("visibility").textContent = (a.visibility * 100).toFixed(0) + "%";
    } else {
        $("visibility").textContent = "no person detected";
    }
    frames++;
    const now = performance.now();
    if (now - lastFpsTime >= 1000) {
        $("fps").textContent = frames;
        frames = 0;
        lastFpsTime = now;
    }
    requestAnimationFrame(loop);
}