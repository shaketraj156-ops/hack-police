import { useState, useEffect } from "react";
import CameraPlayer from "./CameraPlayer";

export default function CameraModal({ camera, onClose }) {
  const [zoomLevel, setZoomLevel] = useState(1);
  const [panPos, setPanPos] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  const handleZoomIn = () => {
    setZoomLevel((prev) => Math.min(prev + 0.5, 4));
  };

  const handleZoomOut = () => {
    setZoomLevel((prev) => {
      const next = Math.max(prev - 0.5, 1);
      if (next === 1) setPanPos({ x: 0, y: 0 });
      return next;
    });
  };

  const handleResetZoom = () => {
    setZoomLevel(1);
    setPanPos({ x: 0, y: 0 });
  };

  const handleMouseDown = (e) => {
    if (zoomLevel <= 1) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - panPos.x, y: e.clientY - panPos.y });
  };

  const handleMouseMove = (e) => {
    if (!isDragging || zoomLevel <= 1) return;
    setPanPos({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => setIsDragging(false);

  const handleWheel = (e) => {
    e.preventDefault();
    if (e.deltaY < 0) {
      handleZoomIn();
    } else {
      handleZoomOut();
    }
  };

  if (!camera) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        <header className="modal-header">
          <div className="modal-title-group">
            <span className="modal-badge">FOCUSED CAMERA VIEW</span>
            <h2>{camera.realName || camera.displayName}</h2>
            <p className="modal-location">📍 {camera.location} — {camera.providerId}</p>
          </div>
          <button className="modal-close-btn" onClick={onClose} title="Close (Esc)">
            ✕
          </button>
        </header>

        <div
          className={`modal-video-wrapper ${zoomLevel > 1 ? "draggable" : ""}`}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          onWheel={handleWheel}
        >
          <div
            className="zoom-viewport"
            style={{
              transform: `scale(${zoomLevel}) translate(${panPos.x / zoomLevel}px, ${panPos.y / zoomLevel}px)`,
              transition: isDragging ? "none" : "transform 0.2s ease-out",
            }}
          >
            <CameraPlayer camera={camera} />
          </div>

          <div className="zoom-hud-overlay">
            <span className="zoom-level-badge">{zoomLevel.toFixed(1)}x ZOOM</span>
            {zoomLevel > 1 && <span className="pan-hint">Drag video to pan position</span>}
          </div>
        </div>

        <footer className="modal-footer">
          <div className="zoom-controls">
            <button className="zoom-btn" onClick={handleZoomOut} disabled={zoomLevel <= 1} title="Zoom Out (-)">
              🔍 -
            </button>
            <span className="zoom-text">{Math.round(zoomLevel * 100)}%</span>
            <button className="zoom-btn" onClick={handleZoomIn} disabled={zoomLevel >= 4} title="Zoom In (+)">
              🔍 +
            </button>
            <button className="reset-btn" onClick={handleResetZoom} title="Reset View">
              ↺ Reset
            </button>
          </div>

          <div className="modal-metadata">
            <span className="meta-pill">LIVE 25 FPS</span>
            <span className="meta-pill">RTSP STREAM</span>
            <span className="meta-pill provider-code">{camera.providerId}</span>
          </div>
        </footer>
      </div>
    </div>
  );
}
