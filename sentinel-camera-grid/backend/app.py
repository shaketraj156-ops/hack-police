import os
import time
import threading
from flask import Flask, request, Response, jsonify, stream_with_context
from flask_cors import CORS
import requests
from dotenv import load_dotenv

from camera_catalogue import validate_camera_id, fetch_catalogue
from camera_worker import (
    camera_map,
    frame_cache,
    lock,
    start_camera_workers,
    set_camera_status
)
from stream_proxy import proxy_hls_manifest, proxy_hls_segment

load_dotenv()

app = Flask(__name__)
CORS(app)

# Explicit configuration parsing
SENTINEL_EMAIL = os.getenv("SENTINEL_EMAIL", "").strip()
SENTINEL_PASSWORD = os.getenv("SENTINEL_PASSWORD", "")
SENTINEL_CDN_HOST = os.getenv("SENTINEL_CDN_HOST", "https://cctv.corp8.cloud").rstrip("/")
SENTINEL_DIRECT_IP = os.getenv("SENTINEL_DIRECT_IP", "103.250.160.189").strip()
SENTINEL_RTSP_PORT = int(os.getenv("SENTINEL_RTSP_PORT", "8554"))
PORT = int(os.getenv("PORT", "3001"))

OFFLINE_DEMO_ID = os.getenv("OFFLINE_DEMO_ID", "cam05").strip()
USE_SYNTHETIC_FALLBACK = (os.getenv("USE_SYNTHETIC_FALLBACK", "false").lower() == "true")

# Shared requests session
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://cctv.corp8.cloud/"
})

is_authenticated = False
auth_error = None
cdn_error = None

def initialize_backend():
    global is_authenticated, auth_error, cdn_error
    
    catalogue, is_auth, err = fetch_catalogue(
        session,
        SENTINEL_CDN_HOST,
        SENTINEL_EMAIL,
        SENTINEL_PASSWORD,
        SENTINEL_DIRECT_IP,
        SENTINEL_RTSP_PORT,
        OFFLINE_DEMO_ID
    )
    
    is_authenticated = is_auth
    auth_error = err
    cdn_error = err

    with lock:
        camera_map.update(catalogue)

    # Start persistent camera worker threads
    start_camera_workers(OFFLINE_DEMO_ID, USE_SYNTHETIC_FALLBACK)

# Initialize catalogue and workers
initialize_backend()

# API Endpoints
@app.route("/api/cameras", methods=["GET"])
def get_cameras():
    with lock:
        cams = sorted(list(camera_map.values()), key=lambda x: x["providerId"])
    
    online_count = sum(1 for c in cams if c["status"] == "ONLINE")
    demo_count = sum(1 for c in cams if c["status"] == "DEMO")

    return jsonify({
        "ok": True,
        "total": len(cams),
        "online": online_count,
        "demo": demo_count,
        "offline": len(cams) - online_count - demo_count,
        "cdnError": cdn_error,
        "authError": auth_error,
        "useSyntheticFallback": USE_SYNTHETIC_FALLBACK,
        "cameras": cams
    })

@app.route("/api/hls-manifest", methods=["GET"])
def get_hls_manifest():
    cam_id = request.args.get("id")
    return proxy_hls_manifest(cam_id, session, SENTINEL_CDN_HOST, camera_map, lock)

@app.route("/api/hls-segment", methods=["GET"])
def get_hls_segment():
    raw_url = request.args.get("url")
    return proxy_hls_segment(raw_url, session)

@app.route("/api/frame/<cam_id>", methods=["GET"])
def get_camera_frame(cam_id):
    if not validate_camera_id(cam_id):
        return jsonify({"error": "Invalid camera ID"}), 400

    with lock:
        jpg_bytes = frame_cache.get(cam_id)
        cam = camera_map.get(cam_id)

    if jpg_bytes:
        return Response(
            jpg_bytes,
            mimetype="image/jpeg",
            headers={
                "Cache-Control": "no-cache, no-store",
                "Access-Control-Allow-Origin": "*"
            }
        )

    last_err = cam.get("lastError") if cam else "RTSP stream unavailable"
    return jsonify({
        "error": "Real RTSP stream frame unavailable",
        "camId": cam_id,
        "reason": last_err or "RTSP connection failed"
    }), 502

@app.route("/api/mjpeg/<cam_id>", methods=["GET"])
def get_mjpeg_stream(cam_id):
    if not validate_camera_id(cam_id):
        return jsonify({"error": "Invalid camera ID"}), 400

    @stream_with_context
    def generate():
        try:
            while True:
                with lock:
                    jpg_bytes = frame_cache.get(cam_id)

                if jpg_bytes:
                    yield (
                        b"--frame\r\n"
                        b"Content-Type: image/jpeg\r\n\r\n"
                        + jpg_bytes
                        + b"\r\n"
                    )

                time.sleep(0.1)

        except GeneratorExit:
            return

    return Response(
        generate(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store",
            "Access-Control-Allow-Origin": "*"
        }
    )

@app.route("/api/health", methods=["GET"])
def health_check():
    with lock:
        total = len(camera_map)
        online = sum(1 for c in camera_map.values() if c["status"] == "ONLINE")
        demo = sum(1 for c in camera_map.values() if c["status"] == "DEMO")
        cached_count = len(frame_cache)

    return jsonify({
        "ok": True,
        "backend": "Python Flask + OpenCV Persistent Workers",
        "authenticated": is_authenticated,
        "authError": auth_error,
        "cdnError": cdn_error,
        "sentinelCdnHost": SENTINEL_CDN_HOST,
        "sentinelDirectIp": SENTINEL_DIRECT_IP,
        "useSyntheticFallback": USE_SYNTHETIC_FALLBACK,
        "cameras": total,
        "online": online,
        "demo": demo,
        "offline": total - online - demo,
        "cachedFrames": cached_count,
        "timestamp": int(time.time() * 1000)
    })

if __name__ == "__main__":
    print(f"Starting Modular Python Sentinel Backend on port {PORT}...")
    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
