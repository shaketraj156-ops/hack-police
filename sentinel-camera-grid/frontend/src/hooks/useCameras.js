import { useState, useEffect, useCallback } from "react";

const API_URL = "/api/cameras";
const POLL_INTERVAL_MS = 30_000; // sync with backend health check interval

/**
 * Fetches the live camera list from the backend API.
 * Polls every 30 seconds so the dashboard reflects health check results
 * without a page reload — mirrors the guide §13 health monitor logic.
 *
 * Returns: { cameras, loading, error, lastUpdated, refetch }
 */
export function useCameras() {
  const [cameras, setCameras]       = useState([]);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchCameras = useCallback(async () => {
    try {
      const res = await fetch(API_URL);
      if (!res.ok) throw new Error(`Backend returned HTTP ${res.status}`);
      const data = await res.json();
      const list = Array.isArray(data) ? data : (data.cameras ?? []);
      setCameras(list);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error("[useCameras] Failed to fetch cameras:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCameras();
    const id = setInterval(fetchCameras, POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [fetchCameras]);

  return { cameras, loading, error, lastUpdated, refetch: fetchCameras };
}
