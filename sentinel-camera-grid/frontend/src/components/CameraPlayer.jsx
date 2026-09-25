import { useEffect, useRef, useState } from "react";
import Hls from "hls.js";

// Stream states
const STATE = {
  CONNECTING: "CONNECTING",
  LIVE: "LIVE",
  OPENCV_LIVE: "OPENCV_LIVE",
  ERROR: "ERROR",
};

export default function CameraPlayer({ camera, onStreamState }) {
  const videoRef = useRef(null);
  const hlsRef = useRef(null);
  const [streamState, setStreamState] = useState(STATE.CONNECTING);
  const [useOpenCvFallback, setUseOpenCvFallback] = useState(false);

  const updateState = (state) => {
    setStreamState(state);
    if (onStreamState) onStreamState(state);
  };

  useEffect(() => {
    if (camera.status !== "ONLINE") return;

    // Reset state on camera change
    setUseOpenCvFallback(false);
    updateState(STATE.CONNECTING);

    const video = videoRef.current;
    if (!video) return;

    let hls;

    if (Hls.isSupported()) {
      hls = new Hls({
        enableWorker: true,
        manifestLoadingTimeOut: 5000,
        levelLoadingTimeOut: 5000,
        fragLoadingTimeOut: 5000,
        maxBufferLength: 10,
        xhrSetup: (xhr) => {
          xhr.withCredentials = false;
        },
      });
      hlsRef.current = hls;

      hls.loadSource(camera.hlsUrl);
      hls.attachMedia(video);

      hls.on(Hls.Events.MANIFEST_PARSED, (_, data) => {
        if (!data.levels || data.levels.length === 0 || !data.levels[0].details || data.levels[0].details.fragments.length === 0) {
          // Empty manifest from CDN -> fallback to live OpenCV MJPEG video stream
          setUseOpenCvFallback(true);
          updateState(STATE.OPENCV_LIVE);
          return;
        }
        video.play().catch(() => {});
        updateState(STATE.LIVE);
      });

      hls.on(Hls.Events.ERROR, (_, data) => {
        if (data.fatal) {
          setUseOpenCvFallback(true);
          updateState(STATE.OPENCV_LIVE);
          hls.destroy();
        }
      });
    } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
      video.src = camera.hlsUrl;
      video.addEventListener("loadedmetadata", () => updateState(STATE.LIVE));
      video.addEventListener("error", () => {
        setUseOpenCvFallback(true);
        updateState(STATE.OPENCV_LIVE);
      });
    } else {
      setUseOpenCvFallback(true);
      updateState(STATE.OPENCV_LIVE);
    }

    return () => {
      if (hls) hls.destroy();
      hlsRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [camera.providerId, camera.hlsUrl, camera.status]);

  // ── Camera is marked OFFLINE in data catalogue ──
  if (camera.status !== "ONLINE") {
    return (
      <div className="stream-panel offline-panel">
        <div className="pulse-dot-offline" />
        <span className="panel-title">Camera Offline</span>
        <span className="panel-sub">No signal from device</span>
      </div>
    );
  }

  const mjpegUrl = camera.mjpegUrl || `/api/mjpeg/${camera.providerId}`;

  return (
    <div className="video-container">
      {!useOpenCvFallback ? (
        <video
          ref={videoRef}
          autoPlay
          muted
          playsInline
          className={`camera-video ${streamState !== STATE.LIVE ? "hidden-video" : ""}`}
        />
      ) : (
        <img
          src={mjpegUrl}
          alt={camera.displayName}
          className="camera-video opencv-frame"
          onError={() => updateState(STATE.ERROR)}
        />
      )}

      {streamState === STATE.CONNECTING && !useOpenCvFallback && (
        <div className="stream-panel connecting-panel">
          <div className="spinner" />
          <span className="panel-title">Connecting stream…</span>
          <span className="panel-sub">{camera.providerId}</span>
        </div>
      )}
    </div>
  );
}

export { STATE };
