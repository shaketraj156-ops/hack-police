import time
import threading
import cv2
import numpy as np

# Global shared state
camera_map = {}
frame_cache = {}
lock = threading.Lock()

def set_camera_status(cid, status, error=None, offline_demo_id="cam05"):
    with lock:
        if cid not in camera_map:
            return
        
        if cid == offline_demo_id:
            camera_map[cid]["status"] = "OFFLINE"
            camera_map[cid]["lastChecked"] = time.time()
            camera_map[cid]["lastError"] = "Demo camera intentionally disabled"
            return

        camera_map[cid]["status"] = status
        camera_map[cid]["lastChecked"] = time.time()
        camera_map[cid]["lastError"] = error

def generate_synthetic_cctv_frame(cid, location, display_name):
    width, height = 640, 360
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    cv2.rectangle(frame, (10, 10), (width-10, height-10), (40, 40, 40), 2)
    cv2.line(frame, (width//2, 10), (width//2, height-10), (25, 25, 25), 1)
    cv2.line(frame, (10, height//2), (width-10, height//2), (25, 25, 25), 1)
    
    timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S DEMO")
    cv2.putText(frame, f"SYNTHETIC DEMO - {cid.upper()}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 165, 0), 2)
    cv2.putText(frame, display_name, (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(frame, f"LOC: {location}", (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)
    cv2.putText(frame, timestamp_str, (20, height - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 250, 250), 1)
    cv2.circle(frame, (width - 30, 40), 6, (0, 165, 255), -1)

    success, buffer = cv2.imencode(".jpg", frame)
    return buffer.tobytes() if success else None

def camera_worker(cam, offline_demo_id, use_synthetic_fallback):
    cid = cam["providerId"]

    while True:
        if cid == offline_demo_id:
            set_camera_status(
                cid,
                "OFFLINE",
                "Demo camera intentionally disabled",
                offline_demo_id
            )
            time.sleep(5)
            continue

        cap = None
        try:
            cap = cv2.VideoCapture(cam["rtspUrl"], cv2.CAP_FFMPEG)
            if not cap.isOpened():
                raise RuntimeError("Could not open RTSP connection")

            set_camera_status(cid, "CONNECTING", None, offline_demo_id)

            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    raise RuntimeError("Frame read failed from RTSP stream")

                timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S LIVE")
                cv2.putText(
                    frame,
                    f"REAL CCTV STREAM - {cid.upper()}",
                    (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (0, 255, 0),
                    2
                )
                cv2.putText(
                    frame,
                    timestamp_str,
                    (15, frame.shape[0] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 255),
                    1
                )

                success, buffer = cv2.imencode(".jpg", frame)
                if not success:
                    continue

                with lock:
                    frame_cache[cid] = buffer.tobytes()
                    camera_map[cid]["status"] = "ONLINE"
                    camera_map[cid]["lastChecked"] = time.time()
                    camera_map[cid]["lastError"] = None

        except Exception as exc:
            if use_synthetic_fallback:
                synthetic = generate_synthetic_cctv_frame(cid, cam["location"], cam["displayName"])
                with lock:
                    if synthetic:
                        frame_cache[cid] = synthetic
                    camera_map[cid]["status"] = "DEMO"
                    camera_map[cid]["lastChecked"] = time.time()
                    camera_map[cid]["lastError"] = str(exc)
            else:
                set_camera_status(cid, "OFFLINE", str(exc), offline_demo_id)
            time.sleep(5)
        finally:
            if cap is not None:
                cap.release()

def start_camera_workers(offline_demo_id, use_synthetic_fallback):
    with lock:
        cams = list(camera_map.values())

    for cam in cams:
        thread = threading.Thread(
            target=camera_worker,
            args=(cam, offline_demo_id, use_synthetic_fallback),
            daemon=True
        )
        thread.start()
