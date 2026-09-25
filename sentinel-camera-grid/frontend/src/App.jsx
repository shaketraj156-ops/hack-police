import { useMemo, useState, useEffect } from "react";
import { useCameras } from "./hooks/useCameras";
import CameraGrid from "./components/CameraGrid";
import CameraModal from "./components/CameraModal";
import "./styles/app.css";

export default function App() {
  const { cameras, loading, error, lastUpdated, refetch } = useCameras();
  const [filter, setFilter] = useState("ALL");
  const [selectedCamera, setSelectedCamera] = useState(null);
  const [alerts, setAlerts] = useState([]);

  // Connect to the unified backend WebSocket for live AI and system alerts
  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/alerts`;
    let ws = null;
    let timer = null;

    function connect() {
      try {
        ws = new WebSocket(wsUrl);
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            setAlerts((prev) => [
              { ...data, id: Date.now() + Math.random() },
              ...prev.slice(0, 4),
            ]);
            // If it's a camera drop alert, refresh the camera list
            if (data.type === "SYSTEM_WARNING") {
              refetch();
            }
          } catch (err) {
            console.error("Alert JSON error:", err);
          }
        };
        ws.onclose = () => {
          timer = setTimeout(connect, 4000);
        };
        ws.onerror = () => {
          if (ws) ws.close();
        };
      } catch (err) {
        timer = setTimeout(connect, 4000);
      }
    }

    connect();

    return () => {
      clearTimeout(timer);
      if (ws) ws.close();
    };
  }, [refetch]);

  const visibleCameras = useMemo(
    () => (filter === "ALL" ? cameras : cameras.filter((c) => c.status === filter)),
    [filter, cameras]
  );

  const onlineCount = cameras.filter((c) => c.status === "ONLINE").length;
  const totalCount  = cameras.length;

  return (
    <main className="app-shell">
      <div className="ambient-background" />

      <header className="app-header">
        <div className="header-titles">
          <p className="eyebrow">SENTINEL CAMERA GRID</p>
          <h1>CCTV Operations Dashboard</h1>
          <p className="subtitle">
            {loading
              ? "Connecting to unified backend…"
              : error
              ? "⚠ Backend unreachable"
              : `Monitoring ${onlineCount} of ${totalCount} cameras live`}
          </p>
        </div>

        <div className="header-right">
          <div className="summary">
            <span className="summary-online">
              <span className="status-dot" /> {onlineCount} ONLINE
            </span>
            <span className="summary-offline">{totalCount - onlineCount} OFFLINE</span>
          </div>
          {lastUpdated && (
            <div className="last-updated">
              Updated {lastUpdated.toLocaleTimeString()}
              <button className="refresh-btn" onClick={refetch} title="Refresh now">↻</button>
            </div>
          )}
        </div>
      </header>

      {/* Real-time AI Alerts and System Drop Warnings */}
      {alerts.length > 0 && (
        <div className="alerts-container">
          {alerts.map((al) => (
            <div
              key={al.id}
              className={`alert-banner ${al.type === "AI_ALERT" ? "alert-ai" : "alert-system"}`}
            >
              <div className="alert-content">
                <span className="alert-badge">
                  {al.type === "AI_ALERT" ? "🚨 ANPR / AI ALERT" : "⚠️ SYSTEM WARNING"}
                </span>
                <span className="alert-text">{al.message}</span>
                {al.location && <span className="alert-tag">📍 {al.location}</span>}
              </div>
              <button
                className="alert-dismiss"
                onClick={() => setAlerts((prev) => prev.filter((item) => item.id !== al.id))}
                title="Dismiss"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Error banner — shown when backend is down */}
      {error && (
        <div className="error-banner">
          <strong>Backend not reachable:</strong> {error}
          <br />
          <small>Make sure the backend is running: <code>cd backend &amp;&amp; uvicorn main:app --reload --port 8000</code></small>
        </div>
      )}

      <nav className="filters">
        {["ALL", "ONLINE", "OFFLINE"].map((value) => (
          <button
            key={value}
            className={`filter-btn ${filter === value ? "active" : ""}`}
            onClick={() => setFilter(value)}
          >
            {value === "ALL" ? "All Cameras" : value === "ONLINE" ? "Online Only" : "Offline Only"}
            <span className="count-badge">
              {value === "ALL"
                ? totalCount
                : value === "ONLINE"
                ? onlineCount
                : totalCount - onlineCount}
            </span>
          </button>
        ))}
      </nav>

      {/* Loading skeleton */}
      {loading && (
        <div className="loading-grid">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="skeleton-card">
              <div className="skeleton-header" />
              <div className="skeleton-video" />
              <div className="skeleton-footer" />
            </div>
          ))}
        </div>
      )}

      {/* Real grid */}
      {!loading && (
        <CameraGrid
          cameras={visibleCameras}
          onSelectCamera={setSelectedCamera}
        />
      )}

      {/* Focused Camera Modal with Zoom & Pan */}
      {selectedCamera && (
        <CameraModal
          camera={selectedCamera}
          onClose={() => setSelectedCamera(null)}
        />
      )}
    </main>
  );
}
