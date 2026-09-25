# 🚨 Hack Police — Gujarat Police Hackathon Operations

This repository contains the official surveillance, AI video processing, and security operations platform developed for the **Gujarat Police Hackathon**.

## 🎥 Core Sub-Projects

### 📹 [Sentinel Camera Grid](./sentinel-camera-grid)
A real-time CCTV operations dashboard and Python OpenCV stream proxy monitoring **30 live security cameras** across transit and municipal infrastructure.

- **Frontend:** React 18 + Vite + HLS.js + Glassmorphism CSS UI
- **Backend:** Python 3 + Flask + OpenCV (`cv2`) multi-threaded RTSP frame workers
- **Protocols:** HLS, RTSP (Port 8554 TCP), WebRTC / WHEP
- **Features:**
  - 30-Camera Live Catalogue Grid
  - 25 FPS MJPEG video streaming proxy
  - Interactive 1.0x–4.0x Digital Zoom & Pan Focus Modal
  - Task 1 failure resilience with locked offline camera testing (`cam05`)
  - SSRF protected proxy & URL-encoded basic auth security

---

## 🚀 Quickstart

```bash
# 1. Run Python Backend (Port 3001)
cd sentinel-camera-grid/backend
.\venv\Scripts\python app.py

# 2. Run React Dashboard (Port 5173)
cd sentinel-camera-grid/frontend
npm run dev
```

For full system architecture, API specifications, and developer documentation, see **[Sentinel Camera Grid README](./sentinel-camera-grid/README.md)**.
