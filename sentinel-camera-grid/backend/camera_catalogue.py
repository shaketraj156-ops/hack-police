import os
import re
import urllib.parse
import requests

# Camera ID validation regex: cam01 .. cam30
CAMERA_ID_PATTERN = re.compile(r"^cam(?:0[1-9]|[12][0-9]|30)$")

def validate_camera_id(cam_id):
    if not cam_id:
        return False
    return bool(CAMERA_ID_PATTERN.fullmatch(cam_id.strip()))

def get_rtsp_url(cam_id, email, password, direct_ip, rtsp_port):
    if not validate_camera_id(cam_id):
        raise ValueError(f"Invalid camera ID: {cam_id}")

    # Encode credentials safely with safe="" per OWASP/RTSP spec
    encoded_email = urllib.parse.quote(email, safe="")
    encoded_password = urllib.parse.quote(password, safe="")

    return (
        f"rtsp://{encoded_email}:{encoded_password}"
        f"@{direct_ip}:{rtsp_port}"
        f"/stream/{cam_id}"
    )

def fetch_catalogue(session, cdn_host, email, password, direct_ip, rtsp_port, offline_demo_id):
    cat_url = f"{cdn_host}/cameras.json"
    raw_cams = None
    cdn_error = None
    is_auth = False

    try:
        response = session.get(cat_url, timeout=10, allow_redirects=False)
        if response.status_code == 200 and response.headers.get("content-type", "").startswith("application/json"):
            raw_cams = response.json()
            is_auth = True
        else:
            cdn_error = f"HTTP {response.status_code} from {cat_url}"
    except requests.RequestException as exc:
        cdn_error = str(exc)

    catalogue = {}
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

    if raw_cams and isinstance(raw_cams, list) and len(raw_cams) > 0:
        for c in raw_cams:
            cid = c.get("id") or c.get("providerId") or c.get("name")
            if not cid or not validate_camera_id(cid):
                continue
            display_name = c.get("name") or c.get("displayName") or f"Camera {cid}"
            loc = c.get("location") or "Ahmedabad Metro"
            hls_url = c.get("hlsUrl") or f"{cdn_host}/{cid}/index.m3u8"
            rtsp_url = get_rtsp_url(cid, email, password, direct_ip, rtsp_port)
            
            is_offline = (cid == offline_demo_id)
            catalogue[cid] = {
                "providerId": cid,
                "displayName": display_name,
                "realName": display_name,
                "location": loc,
                "status": "OFFLINE" if is_offline else "CONNECTING",
                "hlsUrl": f"/api/hls-manifest?id={cid}",
                "rawHlsUrl": hls_url,
                "rtspUrl": rtsp_url,
                "frameUrl": f"/api/frame/{cid}",
                "mjpegUrl": f"/api/mjpeg/{cid}",
                "lastChecked": None,
                "lastError": "Demo camera intentionally disabled" if is_offline else None
            }
    else:
        # Structured fallback for 30 cameras
        for i in range(1, 31):
            num_str = f"{i:02d}"
            cid = f"cam{num_str}"
            loc = locations[(i - 1) % len(locations)]
            display_name = f"Camera {num_str} - {loc.split(',')[0]}"
            rtsp_url = get_rtsp_url(cid, email, password, direct_ip, rtsp_port)
            
            is_offline = (cid == offline_demo_id)
            catalogue[cid] = {
                "providerId": cid,
                "displayName": display_name,
                "realName": display_name,
                "location": loc,
                "status": "OFFLINE" if is_offline else "CONNECTING",
                "hlsUrl": f"/api/hls-manifest?id={cid}",
                "rawHlsUrl": f"{cdn_host}/{cid}/index.m3u8",
                "rtspUrl": rtsp_url,
                "frameUrl": f"/api/frame/{cid}",
                "mjpegUrl": f"/api/mjpeg/{cid}",
                "lastChecked": None,
                "lastError": "Demo camera intentionally disabled" if is_offline else None
            }

    return catalogue, is_auth, cdn_error
