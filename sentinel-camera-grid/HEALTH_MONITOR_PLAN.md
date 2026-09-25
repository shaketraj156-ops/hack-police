# Sentinel Camera Grid — Backend Health Monitor Plan

## Section 13: Real Catalogue & Automatic Status (Future Milestone)

### Current State (Task 1)
- Camera catalogue is **static** — `src/data/cameras.js` hard-codes 30 entries
- Status (`ONLINE` / `OFFLINE`) is **hard-coded** — cam03 is always offline
- This is correct for Task 1 milestone

### Planned Backend Architecture

```
┌─────────────────────────────────────┐
│           React Frontend            │
│   Polls /api/cameras every 30s      │
└────────────────┬────────────────────┘
                 │ JSON (safe fields only)
                 │ No RTSP, no credentials
┌────────────────▼────────────────────┐
│         Express / FastAPI Backend   │
│   • Reads cameras.json catalogue    │
│   • Tracks last_seen per camera     │
│   • Returns ONLINE if last_seen     │
│     was < 30 seconds ago            │
└────────────────┬────────────────────┘
                 │ Updates last_seen
┌────────────────▼────────────────────┐
│        RTSP Health Worker           │
│   (Python + OpenCV/FFmpeg)          │
│   • Connects to RTSP stream         │
│   • Reads 1 frame per 10s           │
│   • On success: POST /internal/seen │
│   • On fail: reconnects after 5s    │
└─────────────────────────────────────┘
```

### Status Logic (from guide Section 13)
```
if current_time - last_seen < 30 seconds:
    status = "ONLINE"
else:
    status = "OFFLINE"
```

### Security Rules
- RTSP credentials stay on the backend machine ONLY
- Frontend receives: `{ providerId, displayName, location, status, hlsUrl }`
- Frontend NEVER receives: RTSP URL, email, password, access token
- `cameras.json` with credentials lives on the server, not in this repo

### RTSP Worker Concept (Python)
```python
import cv2, requests, time

def health_worker(rtsp_url, camera_id, api_base):
    while True:
        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break  # reconnect outer loop
            requests.post(f"{api_base}/internal/seen", json={"id": camera_id})
            time.sleep(10)
        cap.release()
        time.sleep(5)  # wait before reconnecting
```

### Next Steps
1. Set up Express/FastAPI backend
2. Implement `/api/cameras` endpoint
3. Build RTSP health worker for one camera
4. Update React to fetch from API instead of static file
5. Scale to all 30 cameras
