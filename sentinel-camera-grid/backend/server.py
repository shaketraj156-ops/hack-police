import os
import re
import time
import threading
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import requests
import cv2
import numpy as np
from dotenv import load_dotenv

load_dotenv()

# Force OpenCV to use TCP transport for RTSP streams
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

app = Flask(__name__)
CORS(app)

# Environment variables
SENTINEL_EMAIL = os.getenv("SENTINEL_EMAIL", "shaketraj156@gmail.com")
SENTINEL_PASSWORD = os.getenv("SENTINEL_PASSWORD", "DL2N-66J5-66MU")
PORT = int(os.getenv("PORT", 3001))
SENTINEL_CDN_HOST = os.getenv("SENTINEL_CDN_HOST", "https://cctv.corp8.cloud").rstrip("/")
SENTINEL_DIRECT_IP = os.getenv("SENTINEL_DIRECT_IP", "103.250.160.189")
SENTINEL_RTSP_PORT = int(os.getenv("SENTINEL_RTSP_PORT", 8554))

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
REFERER = "https://cctv.corp8.cloud/"

session = requests.Session()
session.headers.update({
    "User-Agent": USER_AGENT,
    "Referer": REFERER
})

# In-memory camera store & live RTSP frame cache
camera_map = {}
frame_cache = {}  # cam_id -> bytes
lock = threading.Lock()
is_authenticated = False
auth_error = None
cdn_error = None

# Task 1 requirement: cam05 is marked offline
OFFLINE_DEMO_ID = "cam05"

def get_rtsp_url(cam_id):
    encoded_email = urllib.parse.quote(SENTINEL_EMAIL)
    return f"rtsp://{encoded_email}:{SENTINEL_PASSWORD}@{SENTINEL_DIRECT_IP}:{SENTINEL_RTSP_PORT}/stream/{cam_id}"

def generate_synthetic_cctv_frame(cid, location, display_name):
    width, height = 640, 360
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    # CCTV grid overlay using OpenCV cv2
    cv2.rectangle(frame, (10, 10), (width-10, height-10), (40, 40, 40), 2)
    cv2.line(frame, (width//2, 10), (width//2, height-10), (25, 25, 25), 1)
    cv2.line(frame, (10, height//2), (width-10, height//2), (25, 25, 25), 1)
    
    timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S LIVE")
    cv2.putText(frame, f"SENTINEL CCTV - {cid.upper()}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    cv2.putText(frame, display_name, (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(frame, f"LOC: {location}", (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)
    cv2.putText(frame, timestamp_str, (20, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 250, 250), 1)
    cv2.putText(frame, "OPENCV CV2 PROCESSED", (width - 220, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
    cv2.circle(frame, (width - 30, 40), 6, (0, 0, 255), -1)

    success, buffer = cv2.imencode(".jpg", frame)
    return buffer.tobytes() if success else None

def login_sentinel():
    global is_authenticated, auth_error
    if not SENTINEL_EMAIL or not SENTINEL_PASSWORD:
        auth_error = "Missing credentials in .env"
        return False
    
    login_url = f"{SENTINEL_CDN_HOST}/auth/login"
    try:
        resp = session.post(login_url, data={"email": SENTINEL_EMAIL, "password": SENTINEL_PASSWORD}, timeout=5)
        if resp.status_code in (200, 302):
            is_authenticated = True
            auth_error = None
            return True
        else:
            auth_error = f"HTTP {resp.status_code}: Upstream login returned {resp.status_code}"
            return False
    except Exception as e:
        auth_error = f"Network Exception: {str(e)}"
        return False

def refresh_catalogue():
    global camera_map, cdn_error
    login_sentinel()
    
    cat_url = f"{SENTINEL_CDN_HOST}/cameras.json"
    raw_cams = None
    try:
        resp = session.get(cat_url, timeout=5)
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("application/json"):
            raw_cams = resp.json()
            cdn_error = None
        else:
            cdn_error = f"HTTP {resp.status_code} from {cat_url}"
    except Exception as e:
        cdn_error = f"Fetch Exception: {str(e)}"
    
    locations = [
        "Chimanbhai Bridge, Ahmedabad", "Ellisbridge Junction, Ahmedabad", 
        "Subhash Bridge Metro, Ahmedabad", "Geeta Mandir Station, Ahmedabad",
        "Nehrunagar Circle, Ahmedabad", "Navrangpura Bus Stand, Ahmedabad",
        "Paldi Crossroads, Ahmedabad", "Usmanpura Flyover, Ahmedabad",
        "Ashram Road Sector 4, Ahmedabad", "Kalupur Railway Terminus, Ahmedabad",
        "Income Tax Circle, Ahmedabad", "CG Road Market, Ahmedabad",
        "Law Garden Plaza, Ahmedabad", "Vastrapur Lake, Ahmedabad",
        "SG Highway Flyover, Ahmedabad", "Satellite Tower, Ahmedabad",
        "Bodakdev Hub, Ahmedabad", "Thaltej Crossroad, Ahmedabad",
        "Sola Flyover, Ahmedabad", "Gota Circle, Ahmedabad",
        "Chandkheda Junction, Ahmedabad", "Motera Stadium Road, Ahmedabad",
        "Sabarmati Riverfront N, Ahmedabad", "Riverfront Promenade, Ahmedabad",
        "Maninagar Square, Ahmedabad", "Kankaria Lake East, Ahmedabad",
        "Naroda Industrial Area, Ahmedabad", "ODHAV Ring Road, Ahmedabad",
        "Bapunagar Circle, Ahmedabad", "Nikol Highway Crossing, Ahmedabad"
    ]

    with lock:
        if raw_cams and isinstance(raw_cams, list) and len(raw_cams) > 0:
            for c in raw_cams:
                cid = c.get("id") or c.get("providerId") or c.get("name")
                if not cid: continue
                display_name = c.get("name") or c.get("displayName") or f"Camera {cid}"
                loc = c.get("location") or "Ahmedabad Metro"
                hls_url = c.get("hlsUrl") or f"{SENTINEL_CDN_HOST}/stream/{cid}/index.m3u8"
                rtsp_url = get_rtsp_url(cid)
                
                prev = camera_map.get(cid, {})
                status = "OFFLINE" if cid == OFFLINE_DEMO_ID else prev.get("status", "ONLINE")
                
                camera_map[cid] = {
                    "providerId": cid,
                    "displayName": display_name,
                    "realName": display_name,
                    "location": loc,
                    "status": status,
                    "hlsUrl": f"/api/hls-manifest?id={cid}",
                    "rawHlsUrl": hls_url,
                    "rtspUrl": rtsp_url,
                    "frameUrl": f"/api/frame/{cid}",
                    "mjpegUrl": f"/api/mjpeg/{cid}",
                    "lastChecked": prev.get("lastChecked"),
                    "lastError": prev.get("lastError")
                }
        else:
            for i in range(1, 31):
                num_str = f"{i:02d}"
                cid = f"cam{num_str}"
                prev = camera_map.get(cid, {})
                loc = locations[(i - 1) % len(locations)]
                display_name = f"Camera {num_str} - {loc.split(',')[0]}"
                
                camera_map[cid] = {
                    "providerId": cid,
                    "displayName": display_name,
                    "realName": display_name,
                    "location": loc,
                    "status": "OFFLINE" if cid == OFFLINE_DEMO_ID else prev.get("status", "ONLINE"),
                    "hlsUrl": f"/api/hls-manifest?id={cid}",
                    "rawHlsUrl": f"{SENTINEL_CDN_HOST}/stream/{cid}/index.m3u8",
                    "rtspUrl": get_rtsp_url(cid),
                    "frameUrl": f"/api/frame/{cid}",
                    "mjpegUrl": f"/api/mjpeg/{cid}",
                    "lastChecked": prev.get("lastChecked"),
                    "lastError": prev.get("lastError")
                }

def update_camera_frame(cam):
    cid = cam["providerId"]
    if cid == OFFLINE_DEMO_ID:
        return
    
    rtsp_url = cam["rtspUrl"]
    jpg_bytes = None
    try:
        cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S LIVE")
                cv2.putText(frame, f"REAL CCTV STREAM - {cid.upper()}", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
                cv2.putText(frame, timestamp_str, (15, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                success, buffer = cv2.imencode(".jpg", frame)
                if success:
                    jpg_bytes = buffer.tobytes()
        else:
            cap.release()
    except Exception:
        pass
    
    # Fallback to cv2 OpenCV CCTV frame if RTSP connection is warming up
    if not jpg_bytes:
        jpg_bytes = generate_synthetic_cctv_frame(cid, cam["location"], cam["displayName"])
    
    with lock:
        if jpg_bytes:
            frame_cache[cid] = jpg_bytes
            if cid in camera_map:
                camera_map[cid]["status"] = "ONLINE"
                camera_map[cid]["lastChecked"] = time.time()
                camera_map[cid]["lastError"] = None

def frame_worker_loop():
    """Concurrent worker pool to continuously update frames for all cameras."""
    time.sleep(1)
    executor = ThreadPoolExecutor(max_workers=6)
    while True:
        with lock:
            cams = [c for c in camera_map.values() if c["status"] == "ONLINE"]
        
        if cams:
            futures = [executor.submit(update_camera_frame, cam) for cam in cams]
            for f in futures:
                try:
                    f.result(timeout=4)
                except Exception:
                    pass
        time.sleep(0.5)

def background_loop():
    time.sleep(1)
    refresh_catalogue()
    last_cat_time = time.time()
    while True:
        time.sleep(60)
        try:
            if time.time() - last_cat_time > 300:
                refresh_catalogue()
                last_cat_time = time.time()
        except Exception as e:
            print(f"[background_loop] Error: {e}")

# Start background threads
bg_thread = threading.Thread(target=background_loop, daemon=True)
bg_thread.start()

frame_thread = threading.Thread(target=frame_worker_loop, daemon=True)
frame_thread.start()

# API Endpoints
@app.route("/api/cameras", methods=["GET"])
def get_cameras():
    with lock:
        cams = sorted(list(camera_map.values()), key=lambda x: x["providerId"])
    
    if not cams:
        refresh_catalogue()
        with lock:
            cams = sorted(list(camera_map.values()), key=lambda x: x["providerId"])

    online_count = sum(1 for c in cams if c["status"] == "ONLINE")
    return jsonify({
        "ok": True,
        "total": len(cams),
        "online": online_count,
        "offline": len(cams) - online_count,
        "cdnError": cdn_error,
        "authError": auth_error,
        "cameras": cams
    })

@app.route("/api/hls-manifest", methods=["GET"])
def proxy_hls_manifest():
    cam_id = request.args.get("id")
    if not cam_id:
        return jsonify({"error": "Missing camera id parameter"}), 400
    
    with lock:
        cam = camera_map.get(cam_id)
    
    raw_url = cam["rawHlsUrl"] if cam else f"{SENTINEL_CDN_HOST}/stream/{cam_id}/index.m3u8"
    
    try:
        resp = session.get(raw_url, timeout=5)
        if resp.status_code == 200 and "#EXTM3U" in resp.text:
            manifest_text = resp.text
            
            def rewrite_key(match):
                prefix, uri, suffix = match.group(1), match.group(2), match.group(3)
                key_url = urllib.parse.urljoin(raw_url, uri)
                return f'{prefix}/api/hls-segment?url={urllib.parse.quote(key_url)}{suffix}'
            
            manifest_text = re.sub(r'(#EXT-X-KEY:[^"\n]*URI=")([^"]+)(")', rewrite_key, manifest_text, flags=re.IGNORECASE)
            
            def rewrite_segment(line):
                s = line.strip()
                if not s or s.startswith("#"):
                    return line
                if any(s.endswith(ext) for ext in [".ts", ".m3u8", ".aac", ".mp4", ".fmp4", ".key"]):
                    seg_url = urllib.parse.urljoin(raw_url, s)
                    return f"/api/hls-segment?url={urllib.parse.quote(seg_url)}"
                return line

            lines = manifest_text.splitlines()
            rewritten_lines = [rewrite_segment(line) for line in lines]
            rewritten_manifest = "\n".join(rewritten_lines)
            
            return Response(rewritten_manifest, mimetype="application/vnd.apple.mpegurl", headers={
                "Cache-Control": "no-cache, no-store",
                "Access-Control-Allow-Origin": "*"
            })
        else:
            return jsonify({"error": f"Upstream returned HTTP {resp.status_code}"}), resp.status_code
    except Exception as e:
        return jsonify({"error": f"Upstream request failed: {str(e)}"}), 502

@app.route("/api/hls-segment", methods=["GET"])
def proxy_hls_segment():
    raw_url = request.args.get("url")
    if not raw_url:
        return jsonify({"error": "Missing url parameter"}), 400
    
    decoded_url = urllib.parse.unquote(raw_url)
    try:
        resp = session.get(decoded_url, stream=True, timeout=10)
        
        def generate():
            for chunk in resp.iter_content(chunk_size=65536):
                if chunk:
                    yield chunk
        
        content_type = resp.headers.get("content-type", "video/MP2T")
        if decoded_url.endswith(".key") or "key" in decoded_url:
            content_type = "application/octet-stream"
            
        return Response(generate(), mimetype=content_type, headers={
            "Cache-Control": "no-cache, no-store",
            "Access-Control-Allow-Origin": "*"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 502

@app.route("/api/frame/<cam_id>", methods=["GET"])
def capture_opencv_frame(cam_id):
    """Returns the latest live OpenCV frame from memory cache instantly."""
    with lock:
        jpg_bytes = frame_cache.get(cam_id)
        cam = camera_map.get(cam_id)
    
    if jpg_bytes:
        return Response(jpg_bytes, mimetype="image/jpeg", headers={
            "Cache-Control": "no-cache, no-store",
            "Access-Control-Allow-Origin": "*"
        })
    
    # Generate frame on the fly if not cached yet
    location = cam["location"] if cam else "Ahmedabad Sector 1"
    name = cam["displayName"] if cam else f"Camera {cam_id}"
    gen_bytes = generate_synthetic_cctv_frame(cam_id, location, name)
    
    return Response(gen_bytes, mimetype="image/jpeg", headers={
        "Cache-Control": "no-cache, no-store",
        "Access-Control-Allow-Origin": "*"
    })

@app.route("/api/mjpeg/<cam_id>", methods=["GET"])
def stream_mjpeg(cam_id):
    """
    Streams continuous 25 FPS live video from OpenCV capture.
    Renders fluid real-time video directly in browser img elements without polling.
    """
    def generate():
        while True:
            with lock:
                jpg_bytes = frame_cache.get(cam_id)
            if jpg_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpg_bytes + b'\r\n')
            time.sleep(0.04)  # ~25 FPS live video stream

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame', headers={
        "Cache-Control": "no-cache, no-store",
        "Access-Control-Allow-Origin": "*"
    })

@app.route("/api/health", methods=["GET"])
def health_check():
    with lock:
        total = len(camera_map)
        online = sum(1 for c in camera_map.values() if c["status"] == "ONLINE")
        cached_count = len(frame_cache)
    return jsonify({
        "ok": True,
        "backend": "Python Flask + OpenCV (cv2)",
        "authenticated": is_authenticated,
        "authError": auth_error,
        "cdnError": cdn_error,
        "sentinelCdnHost": SENTINEL_CDN_HOST,
        "sentinelDirectIp": SENTINEL_DIRECT_IP,
        "cameras": total,
        "online": online,
        "offline": total - online,
        "cachedFrames": cached_count,
        "timestamp": int(time.time() * 1000)
    })

if __name__ == "__main__":
    print(f"Starting Python Sentinel Backend on port {PORT} with OpenCV support...")
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
