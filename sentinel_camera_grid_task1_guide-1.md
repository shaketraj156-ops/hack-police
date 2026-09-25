## Sentinel Camera Grid — Task 1 Implementation Guide

Complete beginner-to-working-project guide for a React CCTV dashboard using the authorized 30-camera grid. This guide assumes GitHub is already connected and focuses on command prompt commands, project code, stream handling, status display, and testing.

## 1. What you will build

The finished application displays up to 30 cameras in a grid. Each card shows a camera ID, location, status, and a live HLS preview. HLS is used in the browser because the supplied guide exposes browser-friendly HLS URLs through the CDN. RTSP is reserved for backend AI inference, while WebRTC/WHEP is an optional low-latency browser path.

```
Camera catalogue React frontend HLS player dashboard
backend health monitor ONLINE/OFFLINE
RTSP future Python/OpenCV/AI worker
```

## Expected first output:

```
CAM-001 Ahmedabad CAM-001 Ahmedabad ONLINE [live video] [live video]
CAM-002 Gandhinagar ONLINE [live video]
CAM-003 Surat CAM-003 OFFLINE OFFLINE [offline panel] [offline panel]
...
CAM-030 ... ONLINE/OFFLINE
```

## 2. Security rules

Use only camera access authorized for your account. Never commit email, password, RTSP URL, or access token to GitHub. Keep RTSP credentials on a backend machine. The supplied endpoint patterns are HLS https://cctv.corp8.cloud//index.m3u8, RTSP rtsp://:@103.250.160.189:8554/stream/, and WHEP http://103.250.160.189:8889/stream//whep. Encode @ in the email as %40 and encode other special password characters.

## 3. Prerequisites and GitHub setup

```
node --version
npm --version
git --version
cd %USERPROFILE%\Desktop
mkdir sentinel-camera-grid
cd sentinel-camera-grid
git init
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git branch -M main
```

## 4. Initialise React

```
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install hls.js
npm run dev
```

Open the local URL printed by Vite, normally http://localhost:5173. Stop with Ctrl+C.

## 5. Create files

```
cd %USERPROFILE%\Desktop\sentinel-camera-grid\frontend
mkdir src\components src\data src\styles
notepad src\data\cameras.js
notepad src\components\CameraPlayer.jsx
notepad src\components\CameraCard.jsx
notepad src\components\CameraGrid.jsx
notepad src\App.jsx
notepad src\main.jsx
notepad src\styles\app.css
```

## 6. cameras.js

```
const cityNames = [
"Ahmedabad", "Gandhinagar", "Surat", "Vadodara", "Rajkot",
"Bhavnagar", "Jamnagar", "Junagadh", "Anand", "Bharuch"
];
```


```
export const cameras = Array.from({ length: 30 }, (_, index) => {
const number = String(index + 1).padStart(2, "0");
const providerId = `cam${number}`;
return {
providerId,
displayName: `CAM-${number}`,
location: cityNames[index % cityNames.length],
status: providerId === "cam03" ? "OFFLINE" : "ONLINE",
hlsUrl: `https://cctv.corp8.cloud/${providerId}/index.m3u8`
};
});
```

## 7. CameraPlayer.jsx

```
import { useEffect, useRef } from "react";
import Hls from "hls.js";
export default function CameraPlayer({ camera }) {
const videoRef = useRef(null);
useEffect(() => {
const video = videoRef.current;
if (!video || camera.status !== "ONLINE") return;
let hls;
if (Hls.isSupported()) {
hls = new Hls({ enableWorker: true });
hls.loadSource(camera.hlsUrl);
hls.attachMedia(video);
hls.on(Hls.Events.ERROR, (_, data) => {
console.error(`Stream error for ${camera.providerId}`, data);
});
} else if (video.canPlayType("application/vnd.apple.mpegurl")) {
video.src = camera.hlsUrl;
}
return () => {
if (hls) hls.destroy();
video.removeAttribute("src");
video.load();
};
}, [camera]);
if (camera.status !== "ONLINE") {
return <div className="offline-panel">Camera offline</div>;
}
return <video ref={videoRef} autoPlay muted playsInline controls className="camera-video" />;
}
```

## 8. CameraCard.jsx and CameraGrid.jsx

```
import CameraPlayer from "./CameraPlayer";
export default function CameraCard({ camera }) {
return (
<article className="camera-card">
<header className="camera-header">
<div><h2>{camera.displayName}</h2><p>{camera.location}</p></div>
<span className={`status status-${camera.status.toLowerCase()}`}>{camera.status}</span>
</header>
<CameraPlayer camera={camera} />
<footer className="camera-footer"><span>{camera.providerId}</span><span>Live stream</span></footer>
</article>
);
}
import CameraCard from "./CameraCard";
export default function CameraGrid({ cameras }) {
return <section className="camera-grid">{cameras.map((camera) => <CameraCard key={camera.providerId} camera={camera} />)}</se
}
```

## 9. App.jsx and main.jsx

```
import { useMemo, useState } from "react";
import { cameras } from "./data/cameras";
import CameraGrid from "./components/CameraGrid";
import "./styles/app.css";
export default function App() {
const [filter, setFilter] = useState("ALL");
const visibleCameras = useMemo(() => filter === "ALL" ? cameras : cameras.filter(c => c.status === filter), [filter]);
const onlineCount = cameras.filter(c => c.status === "ONLINE").length;
```


return (

<main className="app-shell">

<header className="app-header"><div><p className="eyebrow">SENTINEL CAMERA GRID</p><h1>CCTV Operations Dashboard</h1><p>M

<nav className="filters">{["ALL", "ONLINE", "OFFLINE"].map(value => <button key={value} onClick={() => setFilter(value)}

<CameraGrid cameras={visibleCameras} />

</main>

);

}

import { StrictMode } from "react";

import { createRoot } from "react-dom/client";

import App from "./App";

createRoot(document.getElementById("root")).render(<StrictMode><App /></StrictMode>);

## 10. app.css

```
:root { font-family: Inter, system-ui, sans-serif; color: #e5e7eb; background: #070b12; }
* { box-sizing: border-box; }
body { margin: 0; }
.app-shell { min-height: 100vh; padding: 28px; }
.app-header { display: flex; justify-content: space-between; gap: 20px; align-items: center; margin-bottom: 24px; }
.eyebrow { color: #60a5fa; font-size: 12px; letter-spacing: 2px; }
h1 { margin: 6px 0; }
.app-header p { color: #94a3b8; }
.summary { display: flex; gap: 10px; }
.summary span, .status { padding: 7px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }
.summary span:first-child, .status-online { color: #86efac; background: #14532d; }
.summary span:last-child, .status-offline { color: #fca5a5; background: #7f1d1d; }
.filters { display: flex; gap: 10px; margin-bottom: 20px; }
.filters button { cursor: pointer; border: 1px solid #334155; border-radius: 8px; padding: 9px 14px; color: #cbd5e1; background
.filters button.active { color: white; background: #2563eb; }
.camera-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(310px, 1fr)); gap: 18px; }
.camera-card { overflow: hidden; border: 1px solid #243145; border-radius: 12px; background: #101722; }
.camera-header, .camera-footer { display: flex; justify-content: space-between; align-items: center; padding: 14px 16px; }
.camera-header h2, .camera-header p { margin: 0; }
.camera-header p, .camera-footer { color: #94a3b8; font-size: 13px; }
.camera-video, .offline-panel { display: block; width: 100%; height: 190px; background: #020617; }
.camera-video { object-fit: cover; }
.offline-panel { display: grid; place-items: center; color: #fca5a5; }
```

The responsive grid creates more columns on large screens and fewer on small screens. The status is static in this first milestone; the next stage is automatic health monitoring.

## 11. Run and test

```
cd %USERPROFILE%\Desktop\sentinel-camera-grid\frontend npm run dev
// In another Command Prompt window:
curl -I https://cctv.corp8.cloud/cam01/index.m3u8
```

Open the Vite URL. You should see 30 cards. CAM-003 is intentionally offline. Online cards play only if the provider accepts your authorized browser request. HTTP 401/403 means authentication must be configured by the provider. CORS or mixed-content errors must be solved on the streaming server or an approved secure backend proxy.

## 12. GitHub push

```
cd %USERPROFILE%\Desktop\sentinel-camera-grid
git add .
git commit -m "Initialize Sentinel camera grid dashboard"
git push -u origin main
findstr /S /I "password rtsp:// 103.250.160.189" frontend\src\*.*
```

Run the last command before pushing to look for accidentally included credentials.

## 13. Real catalogue and automatic status

The generated catalogue is only a working first step. Your guide says to retrieve cameras.json because the camera set can change. In the next milestone, a backend fetches and validates that catalogue, stores metadata, and returns safe fields to React. Do not put protected catalogue credentials in browser code. A configured camera is not automatically online: the health monitor should update last_seen after a successful frame and show ONLINE only while the last successful frame is recent.

```
If current_time - last_seen < 30 seconds: ONLINE
Otherwise: OFFLINE
```


## 14. RTSP AI stage

When the dashboard works, use RTSP from a backend AI worker, not React. Start with one camera, read frames, run detection, update last_seen, and save events. Scale gradually to 30 while measuring CPU, GPU, RAM, network, and dropped frames. The stream is live and non-seekable, so the worker must reconnect after interruptions.

```
ffplay -rtsp_transport tcp "rtsp://ENCODED_EMAIL:PASSWORD@103.250.160.189:8554/stream/cam01"
Python concept:
cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
while True:
ok, frame = cap.read()
if not ok:
reconnect()
continue
detections = model(frame)
update_last_seen("cam01")
```

## 15. Completion checklist

```
[ ] React/Vite project created
[ ] GitHub remote connected
[ ] hls.js installed
[ ] 30 camera records displayed
[ ] Each card has ID and location
[ ] Online/offline badges visible
[ ] One intentional offline camera demonstrated
[ ] One authorized HLS URL tested
[ ] No credentials committed
[ ] Dashboard pushed to GitHub
[ ] Backend health monitoring planned
```

## Reference note

This guide follows the endpoint model in your supplied Sentinel guide. Browser streaming should use HLS or WebRTC, while RTSP is intended for AI tools. MediaMTX documentation describes browser reading through HLS/WebRTC and RTSP as a recommended media-processing input. [web:24][web:27]
