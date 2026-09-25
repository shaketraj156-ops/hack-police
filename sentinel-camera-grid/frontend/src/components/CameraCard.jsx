import { useState } from "react";
import CameraPlayer, { STATE } from "./CameraPlayer";

export default function CameraCard({ camera, onSelect }) {
  const [streamState, setStreamState] = useState(STATE.CONNECTING);

  const isLive = streamState === STATE.LIVE || streamState === STATE.OPENCV_LIVE;

  const footerLabel =
    camera.status !== "ONLINE" ? "Disconnected" :
    streamState === STATE.LIVE ? "Live Stream (HLS)" :
    streamState === STATE.OPENCV_LIVE ? "Live Stream (OpenCV)" :
    streamState === STATE.CONNECTING ? "Connecting…" :
    "Stream error";

  const footerClass =
    camera.status !== "ONLINE" ? "live-badge offline" :
    isLive ? "live-badge live" :
    streamState === STATE.CONNECTING ? "live-badge connecting" :
    "live-badge error";

  return (
    <article className="camera-card" onClick={() => onSelect && onSelect(camera)}>
      <header className="camera-header">
        <div className="header-info">
          <h2>{camera.realName || camera.displayName}</h2>
          <p>
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24"
              fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
              <circle cx="12" cy="10" r="3" />
            </svg>
            {camera.location}
          </p>
          <span className="cam-id-badge">{camera.providerId}</span>
        </div>
        <div className="header-actions">
          <span className={`status status-${camera.status.toLowerCase()}`}>
            {camera.status === "ONLINE" && <span className="status-dot" />}
            {camera.status}
          </span>
          <button className="expand-card-btn" onClick={(e) => { e.stopPropagation(); onSelect && onSelect(camera); }} title="Zoom In Camera">
            🔍 Zoom
          </button>
        </div>
      </header>

      <CameraPlayer camera={camera} onStreamState={setStreamState} />

      <footer className="camera-footer">
        <span className="provider-id">{camera.providerId}</span>
        <span className={footerClass}>
          {isLive && camera.status === "ONLINE" && (
            <span className="recording-dot" />
          )}
          {footerLabel}
        </span>
      </footer>
    </article>
  );
}
