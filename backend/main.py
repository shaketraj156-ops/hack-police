from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import os
import asyncio
from datetime import datetime, timezone
from typing import List

from database import get_db, SessionLocal
from models import Camera

load_dotenv()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Sentinel CCTV API",
    description="Backend for the Sentinel Camera Grid Dashboard"
)

# Add this CORS block so Antogravity's React frontend isn't blocked
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PHASE 5: WebSocket Connection Manager ---
class ConnectionManager:
    def __init__(self):
        # Keeps track of all active frontend users viewing the dashboard
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast_alert(self, message: dict):
        # Instantly pushes JSON alerts to every connected React dashboard
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()


# --- PHASE 4: Background Health Monitor ---
@app.on_event("startup")
async def start_health_check():
    asyncio.create_task(health_monitor_loop())

async def health_monitor_loop():
    while True:
        db = SessionLocal()
        try:
            cameras = db.query(Camera).all()
            now = datetime.now(timezone.utc)
            
            for cam in cameras:
                if cam.last_seen and (now.replace(tzinfo=timezone.utc) - cam.last_seen.replace(tzinfo=timezone.utc)).total_seconds() > 30:
                    if cam.status != "OFFLINE":
                        cam.status = "OFFLINE"
                        # Bonus: Instantly alert the frontend if a camera drops
                        await manager.broadcast_alert({
                            "type": "SYSTEM_WARNING",
                            "message": f"ALERT: {cam.display_name} connection lost!"
                        })
            
            db.commit()
        finally:
            db.close()
            
        await asyncio.sleep(10)


# --- PHASE 1 & 3: Standard Endpoints ---
@app.get("/")
def read_root():
    return {"status": "Online"}

@app.get("/api/cameras")
def get_cameras(db: Session = Depends(get_db)):
    cameras = db.query(Camera).all()
    result = []
    for c in cameras:
        result.append({
            "providerId": c.provider_id,
            "displayName": c.display_name,
            "location": c.location,
            "hlsUrl": c.hls_url,
            "status": c.status
        })
    return result


# --- PHASE 5: WebSocket Endpoint ---
@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Listens for incoming detections from your AI python script
            data = await websocket.receive_json()
            
            # Broadcasts that AI detection to the React frontend immediately
            await manager.broadcast_alert(data)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)