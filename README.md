# 🚨 Hack Police — Gujarat Police Hackathon Operations Platform

This repository contains the enterprise CCTV surveillance, AI video processing, and security operations platform developed for the **Gujarat Police Hackathon**.

## 🎥 Core Sub-Projects

### 📹 [Sentinel Camera Grid](./sentinel-camera-grid)
A real-time CCTV operations dashboard, database-backed API server, and Python OpenCV stream proxy monitoring **30 live security cameras** across transit and municipal infrastructure (e.g., Gujarat / Ahmedabad Metro Infrastructure).

- **Frontend:** React 18 + Vite 5 + HLS.js + Glassmorphism Dark CSS UI
- **Unified Backend:** Python 3 + FastAPI + uvicorn (Port 8000) / Flask (Port 3001) + OpenCV (`cv2`) frame processing
- **Database & Persistence:** SQLAlchemy ORM (PostgreSQL / SQLite `sentinel.db`) with automatic camera catalogue and ANPR watchlist seeding
- **Real-Time Communication:** WebSockets broadcast channel (`/ws/alerts`) for instant AI detection alerts
- **Media Protocols:** HLS (`.m3u8`), RTSP (Port 8554 TCP), WebRTC / WHEP, and 25 FPS MJPEG live video proxy
- **Key Features:**
  - 30-Camera Live Catalogue Grid with location badges & status heartbeats
  - Dual-engine playback (HLS HTML5 player + OpenCV 25 FPS MJPEG video proxy)
  - Interactive 1.0x–4.0x Digital Zoom, Click-and-Drag Pan & Focus Modal View
  - Task 1 failure resilience with locked offline camera testing (`cam03` / `cam05`)
  - SSRF protected proxy & URL-encoded basic auth security

---

## 🚀 Quickstart Guide

### 1. Unified FastAPI Backend (Recommended — Port 8000)

```bash
# Navigate to backend directory
cd sentinel-camera-grid/backend

# Initialize virtual environment (Windows PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt

# Initialize database & seed 30 cameras
python init_db.py

# Start FastAPI server via uvicorn
npm run dev
# OR: .\venv\Scripts\uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Alternative Flask Backend (Port 3001)

```bash
cd sentinel-camera-grid/backend
npm run flask
# OR: .\venv\Scripts\python app.py
```

### 3. React Dashboard Frontend (Port 5173)

```bash
cd sentinel-camera-grid/frontend
npm install
npm run dev
```

---

## 📄 Complete Documentation

For detailed system design, API route specs, WebSocket protocols, and component breakdowns:
- **[Sentinel Camera Grid README](./sentinel-camera-grid/README.md)**
- **[Project Tech Stack & Architecture Guide](./sentinel-camera-grid/PROJECT_DOCUMENTATION.md)**
- **[Health Monitor Implementation Plan](./sentinel-camera-grid/HEALTH_MONITOR_PLAN.md)**
