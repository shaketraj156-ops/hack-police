import re
import urllib.parse
from flask import Response, jsonify
import requests
from camera_catalogue import validate_camera_id

ALLOWED_CDN_HOST = "cctv.corp8.cloud"

def is_allowed_cdn_url(value):
    if not value:
        return False
    try:
        parsed = urllib.parse.urlparse(value)
        return (
            parsed.scheme == "https"
            and parsed.hostname == ALLOWED_CDN_HOST
            and parsed.port in (None, 443)
            and parsed.path.startswith("/")
        )
    except Exception:
        return False

def proxy_hls_manifest(cam_id, session, cdn_host, camera_map, lock):
    if not validate_camera_id(cam_id):
        return jsonify({"error": "Invalid camera ID"}), 400

    with lock:
        cam = camera_map.get(cam_id)

    raw_url = cam["rawHlsUrl"] if cam else f"{cdn_host}/{cam_id}/index.m3u8"

    try:
        resp = session.get(raw_url, timeout=10, allow_redirects=False)
        if resp.status_code == 200 and "#EXTM3U" in resp.text:
            manifest_text = resp.text

            def rewrite_key(match):
                prefix, uri, suffix = match.group(1), match.group(2), match.group(3)
                key_url = urllib.parse.urljoin(raw_url, uri)
                return f'{prefix}/api/hls-segment?url={urllib.parse.quote(key_url)}{suffix}'

            manifest_text = re.sub(
                r'(#EXT-X-KEY:[^"\n]*URI=")([^"]+)(")',
                rewrite_key,
                manifest_text,
                flags=re.IGNORECASE
            )

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

            return Response(
                rewritten_manifest,
                mimetype="application/vnd.apple.mpegurl",
                headers={
                    "Cache-Control": "no-cache, no-store",
                    "Access-Control-Allow-Origin": "*"
                }
            )
        else:
            return jsonify({"error": f"Upstream returned HTTP {resp.status_code}"}), resp.status_code

    except requests.RequestException as exc:
        return jsonify({"error": f"Upstream request failed: {str(exc)}"}), 502

def proxy_hls_segment(raw_url, session):
    if not raw_url:
        return jsonify({"error": "Missing URL parameter"}), 400

    decoded_url = urllib.parse.unquote(raw_url)

    # SSRF Protection: validate against allowlist
    if not is_allowed_cdn_url(decoded_url):
        return jsonify({"error": "Forbidden: URL host is not allowed"}), 403

    try:
        resp = session.get(
            decoded_url,
            stream=True,
            timeout=10,
            allow_redirects=False
        )

        if resp.status_code != 200:
            return jsonify({"error": f"Upstream returned HTTP {resp.status_code}"}), resp.status_code

        def generate():
            try:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        yield chunk
            finally:
                resp.close()

        content_type = resp.headers.get("content-type", "video/MP2T")
        if decoded_url.endswith(".key") or "key" in decoded_url:
            content_type = "application/octet-stream"

        return Response(
            generate(),
            content_type=content_type,
            headers={
                "Cache-Control": "no-cache, no-store",
                "Access-Control-Allow-Origin": "*"
            }
        )

    except requests.RequestException as exc:
        return jsonify({"error": str(exc)}), 502
