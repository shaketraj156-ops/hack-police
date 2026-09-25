# 📹 Sentinel Camera Grid — Unified CCTV Operations Dashboard & OpenCV Proxy

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Flask](https://img.shields.io/badge/Flask-3.1%2B-green.svg)](https://flask.palletsprojects.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.9-red.svg)](https://opencv.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-d70a53.svg)](https://www.sqlalchemy.org/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.0-646cff.svg)](https://vitejs.dev/)

**Sentinel Camera Grid** is an enterprise-grade, real-time CCTV operations dashboard designed to monitor up to **30 live security cameras** across metropolitan transit networks (e.g., Gujarat / Ahmedabad Metro Infrastructure).

It features a **unified Python backend** (FastAPI + uvicorn on Port 8000 & Flask on Port 3001) with database persistence, live OpenCV (`cv2`) high-framerate streaming, real-time WebSocket AI alerts, and an **interactive React 18 dashboard** with dual streaming engines and digital zoom controls.

---

## 🌟 Key Features

- **🎥 30 Authorized CCTV Streams:** Dynamically loads the camera catalogue from MediaMTX / Sentinel CDN without hardcoded stream counts.
- **⚡ Dual-Engine Video Streaming:**
  - **Engine 1 (HLS.js):** Browser-native HLS HTML5 playback for low-bandwidth monitoring.
  - **Engine 2 (OpenCV MJPEG):** 25 FPS live OpenCV video proxy directly reading TCP RTSP feeds (`rtsp://...:8554`) for zero latency and AI inference readiness.
- **🔍 Interactive Digital Zoom & Pan:** Modal view allowing operators to zoom from 1.0x up to 4.0x, click-and-drag to pan across high-resolution streams, and reset with one click or `Esc`.
- **🚨 Real-Time WebSocket AI Alerts:** `/ws/alerts` WebSocket push engine for instant broadcast of ANPR license plate detections and security alerts to connected React dashboards.
- **💾 Database & ORM Persistence:** Built-in SQLAlchemy ORM supporting SQLite (`sentinel.db`) and PostgreSQL. `init_db.py` automatically seeds 30 camera records and ANPR target watchlists.
- **🚨 Honest Task 1 Offline Testing:** `cam03` / `cam05` strictly locked offline for system failure testing. Failed cameras display real connection state errors—no synthetic dummy noise replaces real physical camera failures unless explicitly configured (`USE_SYNTHETIC_FALLBACK=true`).
- **🛡️ Enterprise Security & SSRF Protection:**
  - Credentials safely URL-encoded (`safe=""`) for MediaMTX RTSP basic auth.
  - Strict host allowlist validation (`cctv.corp8.cloud`) on all media proxy routes to prevent Server-Side Request Forgery (SSRF).
  - Environment isolation via `.env` files.

---

## 📐 Architecture & Protocol Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          REACT FRONTEND (Vite)                              │
│                                                                             │
│   App.jsx  ──►  useCameras Hook  ──►  CameraGrid  ──►  CameraCard           │
│     │                                                       │               │
│     └─────────►  CameraModal (1.0x-4.0x Zoom & Pan) ◄──────────┘               │
└───────────────────────┬──────────────────────────────┬──────────────────────┘
     HTTP / REST (Port 8000 / 3001)                  │ WebSocket (/ws/alerts)
┌───────────────────────▼──────────────────────────────▼──────────────────────┐
│                    UNIFIED PYTHON BACKEND (FastAPI / Flask)                  │
│                                                                             │
│   main.py / app.py  ──►  REST API & Route Handlers                          │
│    ├── database.py & models.py (SQLAlchemy ORM + SQLite / PostgreSQL)       │
│    ├── camera_catalogue.py     (ID Regex Validation & URL Resolution)       │
│    ├── camera_worker.py        (Multi-Threaded OpenCV RTSP Frame Grabber)   │
│    └── stream_proxy.py         (SSRF Host Validation & HLS Manifest Proxy)  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ RTSP / TCP (Port 8554)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                      SENTINEL MEDIAMTX STREAM SERVER                        │
│                     Direct IP: 103.250.160.189:8554                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Protocol Comparison

| Protocol | Primary Use Case | Transport | Implementation |
|---|---|---|---|
| **HLS (`.m3u8`)** | Dashboard Video Player | HTTP / HTTPS | Proxied via `/api/hls-manifest` & `/api/hls-segment` |
| **RTSP (`rtsp://`)** | Python / OpenCV AI Inference | TCP (Port 8554) | OpenCV `cv2.VideoCapture` background workers |
| **WebSockets (`/ws/alerts`)** | Live AI Detection Alerts | WS / WSS | FastAPI ConnectionManager broadcast channel |
| **WebRTC / WHEP** | Sub-Second Low-Latency Preview | HTTP / WHEP | Direct WHEP streaming endpoints |

---

## 🛠️ Tech Stack & Dependencies

| Layer | Technology | Role |
|---|---|---|
| **Primary Server** | FastAPI 0.110 + uvicorn | Async web server, OpenAPI documentation, and WebSocket broadcast. |
| **Alternative Server** | Flask 3.1 + Flask-CORS | Micro-framework alternative on port 3001. |
| **Database & ORM** | SQLAlchemy 2.0 + SQLite / PostgreSQL | Database models (`Camera`, `Watchlist`), connection pooling, and migrations. |
| **Video Engine** | OpenCV (`cv2`) & FFmpeg | Reads H.264/HEVC RTSP streams over TCP, overlays timestamps, encodes JPEG buffers. |
| **WebSockets** | websockets | Full-duplex communication channel for real-time security alerts. |
| **HTTP & Security** | Requests & urllib | Handles session authentication, cookie persistence, and URL safety encoding. |
| **Frontend Framework** | React 18 | Declarative UI framework managing grid states, filtering, and modal dialogs. |
| **Build Tool** | Vite 5 | Rapid HMR dev server configured with `/api` proxy targeting port 8000/3001. |
| **Video Engine (UI)** | HLS.js | Decodes HLS manifests for browser video tags without native HLS support. |
| **Styling** | Vanilla CSS3 | Custom dark glassmorphism aesthetic with responsive grid and ambient glows. |

---

## 📁 Repository Structure

```
sentinel-camera-grid/
├── backend/
│   ├── main.py                # Primary FastAPI application (Port 8000, WebSockets, DB integration)
│   ├── app.py                 # Alternative Flask backend (Port 3001)
│   ├── database.py            # SQLAlchemy database connection engine & session factory
│   ├── models.py              # Database models (Camera, Watchlist)
│   ├── init_db.py             # Database table creation & 30-camera seed script
│   ├── test_alert.py          # WebSocket test script to broadcast simulated AI alerts
│   ├── camera_catalogue.py    # Camera catalogue loader, ID validator & URL generator
│   ├── camera_worker.py       # OpenCV multi-threaded frame grabber & memory cache
│   ├── stream_proxy.py        # SSRF proxy validator for HLS manifests and video segments
│   ├── package.json           # npm scripts (`dev`, `start`, `flask`)
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Environment credentials & configuration
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # Main operational dashboard container
│   │   ├── components/
│   │   │   ├── CameraCard.jsx # Individual camera card with live badges & zoom trigger
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

### 1. Launch FastAPI Backend (Recommended — Port 8000)

```bash
cd backend

# Create & activate virtual environment (Windows PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt

# Seed SQLite database with 30 cameras
python init_db.py

# Run FastAPI backend via npm script
npm run dev
# OR: .\venv\Scripts\uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
*FastAPI runs on `http://127.0.0.1:8000`.*

### 2. Alternative: Launch Flask Backend (Port 3001)

```bash
cd backend
npm run flask
# OR: .\venv\Scripts\python app.py
```

### 3. Launch Frontend Dashboard (React + Vite)

```bash
cd frontend
npm install
npm run dev
```
*Frontend opens on `http://localhost:5173`.*

---

## 📡 API & WebSocket Reference

| Endpoint / Route | Method / Protocol | Parameters | Description |
|---|---|---|---|
| `/` | `GET` | — | Returns root service status and available endpoints JSON. |
| `/api/cameras` | `GET` | — | Returns full JSON list of 30 cameras, health statuses, and media URLs. |
| `/api/health` | `GET` | — | Returns system operational status, active cached frames, and CDN state. |
| `/api/mjpeg/<cam_id>` | `GET` | `cam_id` (`cam01`..`cam30`) | Continuous 25 FPS MJPEG live video stream for browser HTML `<img>`. |
| `/api/frame/<cam_id>` | `GET` | `cam_id` (`cam01`..`cam30`) | Single JPEG frame snapshot from OpenCV cache. |
| `/api/hls-manifest` | `GET` | `id` (`cam01`..`cam30`) | Proxied `.m3u8` manifest with rewritten segment paths for CORS bypass. |
| `/api/hls-segment` | `GET` | `url` (encoded HTTPS URL) | Proxied `.ts` video segment or AES decryption key. |
| `/ws/alerts` | `WebSocket` | — | Full-duplex WebSocket channel for real-time security alerts. |

---

## 🧪 Testing Tools & Utilities

### 1. Database Seeding (`init_db.py`)
Run `python init_db.py` to recreate database tables (`cameras`, `watchlist`) and populate all 30 camera records (`cam01` through `cam30`).

### 2. Live AI Alert Broadcasting (`test_alert.py`)
Run `python test_alert.py` while the FastAPI backend is running to push a test ANPR detection alert through the `/ws/alerts` WebSocket channel.

---

## 📝 License & Attribution

Developed for **Gujarat Police Hackathon / Sentinel Operations**. Built with Python, FastAPI, Flask, OpenCV, SQLAlchemy, React, and MediaMTX.
