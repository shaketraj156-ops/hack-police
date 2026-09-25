# 📹 Sentinel Camera Grid — Real-Time CCTV Operations Dashboard

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-green.svg)](https://flask.palletsprojects.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.10-red.svg)](https://opencv.org/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.0-646cff.svg)](https://vitejs.dev/)

**Sentinel Camera Grid** is an enterprise-grade, real-time CCTV operations dashboard designed to monitor up to **30 live security cameras** across metropolitan transit networks (e.g., Gujarat / Ahmedabad Metro Infrastructure). 

It features a **modular Python Flask + OpenCV (`cv2`) backend** streaming high-framerate video and an **interactive React 18 dashboard** with dual streaming engines, live health monitoring, and interactive 1.0x–4.0x digital zoom capabilities.

---

## 🌟 Key Features

- **🎥 30 Authorized CCTV Streams:** Dynamically loads the camera catalogue from the MediaMTX / Sentinel CDN engine without hardcoding camera counts.
- **⚡ Dual-Engine Video Streaming:**
  - **Engine 1 (HLS.js):** Browser-native HLS HTML5 playback for low-bandwidth monitoring.
  - **Engine 2 (OpenCV MJPEG):** 25 FPS live OpenCV video proxy directly reading TCP RTSP feeds (`rtsp://...:8554`) for zero latency and AI inference readiness.
- **🔍 Interactive Digital Zoom & Pan:** Modal view allowing operators to zoom from 1.0x up to 4.0x, click-and-drag to pan across the high-resolution stream, and reset with one click or `Esc`.
- **🚨 Honest Task 1 Offline Testing:** `cam05` is strictly locked offline for system failure testing. Failed cameras display real connection state errors—no synthetic dummy noise images replace real physical camera failures unless explicitly configured via `USE_SYNTHETIC_FALLBACK=true`.
- **🛡️ Enterprise Security & SSRF Protection:**
  - Credentials safely URL-encoded (`safe=""`) for MediaMTX RTSP basic auth.
  - Strict host allowlist validation (`cctv.corp8.cloud`) on all media proxy routes to prevent Server-Side Request Forgery (SSRF).
  - Environment isolation via `.env` files.
- **💓 Background Daemon Health Monitoring:** Multi-threaded worker pool (`ThreadPoolExecutor`) continuously polls active camera feeds, updates frame caches in memory, and tracks uptime stats.

---

## 📐 Architecture & Protocol Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          REACT FRONTEND (Vite)                              │
│                                                                             │
│   App.jsx  ──►  useCameras Hook  ──►  CameraGrid  ──►  CameraCard           │
│     │                                                       │               │
│     └─────────►  CameraModal (1.0x-4.0x Zoom & Pan) ◄──────────┘               │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP / REST API (Port 3001)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                    PYTHON FLASK BACKEND (Modular Stack)                     │
│                                                                             │
│   app.py  ──►  REST API & Route Handlers                                    │
│    ├── camera_catalogue.py  (ID Regex Validation & URL Resolution)          │
│    ├── camera_worker.py     (Multi-Threaded OpenCV RTSP Capture & Caching)   │
│    └── stream_proxy.py      (SSRF Host Validation & HLS Manifest Proxy)     │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ RTSP / TCP (Port 8554)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                      SENTINEL MEDIAMTX STREAM SERVER                        │
│                     Direct IP: 103.250.160.189:8554                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### The 3 Protocol Strategy

| Protocol | Primary Use Case | Transport | Backend Implementation |
|---|---|---|---|
| **HLS (`.m3u8`)** | Dashboard Video Player | HTTP / HTTPS | Proxied via `/api/hls-manifest` & `/api/hls-segment` |
| **RTSP (`rtsp://`)** | Python / OpenCV AI Inference | TCP (Port 8554) | OpenCV `cv2.VideoCapture` background workers |
| **WebRTC / WHEP** | Sub-Second Low-Latency Preview | HTTP / WHEP | Directly pointed to WHEP endpoints |

---

## 🛠️ Tech Stack & Technologies Used

| Layer | Component | Description & Role |
|---|---|---|
| **Backend Runtime** | Python 3.10+ | Powers API server, worker threads, and image processing. |
| **Video Engine** | OpenCV (`cv2`) & FFmpeg | Reads H.264/HEVC RTSP streams over TCP, overlays timestamps, encodes JPEG buffers. |
| **Web Server** | Flask & Flask-CORS | Exposes REST endpoints, proxy routes, and MJPEG stream handlers. |
| **HTTP & Security** | Requests & urllib | Handles session authentication, cookie persistence, and URL safety encoding. |
| **Frontend Framework** | React 18 | Declarative UI framework managing grid states, filtering, and modal dialogs. |
| **Build Tool** | Vite | Rapid HMR dev server configured with `/api` proxy targeting backend port `3001`. |
| **Video Engine (UI)** | HLS.js | Decodes HLS manifests for browser video tags without native HLS support. |
| **Styling** | Vanilla CSS3 | Custom dark glassmorphism aesthetic with responsive grid and ambient glows. |

---

## 📁 Repository Structure

```
sentinel-camera-grid/
├── backend/
│   ├── app.py                 # Main Flask application entry point & REST API routes
│   ├── camera_catalogue.py    # Camera catalogue loader, ID validator & URL generator
│   ├── camera_worker.py       # OpenCV multi-threaded frame grabber & memory cache
│   ├── stream_proxy.py        # SSRF proxy validator for HLS manifests and video segments
│   ├── requirements.txt       # Python dependencies (flask, opencv-python, requests, etc.)
│   └── .env                   # Environment variables (credentials, IPs, ports)
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Main operational dashboard container
│   │   ├── components/
│   │   │   ├── CameraCard.jsx # Individual camera status & video card
│   │   │   ├── CameraGrid.jsx # Responsive grid component
│   │   │   ├── CameraModal.jsx# Fullscreen digital zoom & pan focus modal
│   │   │   └── CameraPlayer.jsx# Dual-engine (HLS + MJPEG) stream renderer
│   │   ├── hooks/
│   │   │   └── useCameras.js  # Auto-refresh camera catalogue custom hook
│   │   └── styles/
│   │       └── app.css        # Glassmorphic dark design system
│   ├── package.json
│   └── vite.config.js         # Vite configuration with API proxying
├── HEALTH_MONITOR_PLAN.md     # Architecture specification for camera health checks
└── PROJECT_DOCUMENTATION.md   # Comprehensive technical deep-dive and component guide
```

---

## 🚀 Quickstart & Setup Guide

### Prerequisites
- **Python:** 3.10 or higher
- **Node.js:** 18 or higher
- **OS:** Windows / Linux / macOS

### 1. Launch Backend Server (Python Flask + OpenCV)

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment (Windows PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt

# Run backend application
python app.py
```
*Backend runs on `http://localhost:3001`.*

### 2. Launch Frontend Dashboard (React + Vite)

```bash
# Open a new terminal and navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite dev server
npm run dev
```
*Frontend opens on `http://localhost:5173`.*

---

## 📡 API Endpoint Reference

| Endpoint | Method | Query / Path Params | Description |
|---|---|---|---|
| `/api/cameras` | `GET` | — | Returns full JSON list of 30 cameras, health statuses, and media URLs. |
| `/api/health` | `GET` | — | Returns system operational status, active cached frames, and CDN state. |
| `/api/mjpeg/<cam_id>` | `GET` | `cam_id` (`cam01`..`cam30`) | Continuous 25 FPS MJPEG live video stream for browser HTML `<img>`. |
| `/api/frame/<cam_id>` | `GET` | `cam_id` (`cam01`..`cam30`) | Single JPEG frame snapshot from OpenCV cache. |
| `/api/hls-manifest` | `GET` | `id` (`cam01`..`cam30`) | Proxied `.m3u8` manifest with rewritten segment paths for CORS bypass. |
| `/api/hls-segment` | `GET` | `url` (encoded HTTPS URL) | Proxied `.ts` video segment or AES decryption key. |
| `/api/proxy-stream` | `GET` | `url` (encoded HTTPS URL) | Validated SSRF stream proxy for external player clients. |

---

## 🔍 Task 1 Compliance Audit

- [x] **Dynamic 30-Camera Grid:** Catalogue dynamically fetched and populated (`cam01` through `cam30`).
- [x] **Location Badges & IDs:** Displays Metro station locations and standardized camera identifiers.
- [x] **No Synthetic Fake Frames:** Offline cameras return honest HTTP 503 errors and offline status cards.
- [x] **Demo Offline Lock:** `cam05` is hard-locked as `OFFLINE` to verify system error resilience.
- [x] **Single Camera Zoom Modal:** Dedicated Zoom button opens a 1.0x–4.0x pan-and-zoom focal view.
- [x] **Clean Architecture:** Fully modular code split across `app.py`, `camera_catalogue.py`, `camera_worker.py`, and `stream_proxy.py`.

---

## 📝 License & Attribution

Developed for **Gujarat Police Hackathon / Sentinel Operations**. Built with Python, Flask, OpenCV, React, and MediaMTX.
