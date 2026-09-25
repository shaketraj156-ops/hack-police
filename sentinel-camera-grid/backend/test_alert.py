import asyncio
import websockets
import json
from datetime import datetime

async def simulate_ai_detection():
    # The exact WebSocket URL your React frontend and AI will connect to
    uri = "ws://127.0.0.1:8000/ws/alerts"
    
    try:
        async with websockets.connect(uri) as websocket:
            # This is the fake payload your AI would generate
            fake_alert = {
                "type": "AI_ALERT",
                "camera": "cam02",
                "location": "Ahmedabad",
                "message": "MATCH FOUND: Stolen vehicle detected (Plate: GJ-01-XX-9999)",
                "timestamp": datetime.now().isoformat()
            }
            
            # Send the payload to the FastAPI server
            await websocket.send(json.dumps(fake_alert))
            print(f"[SUCCESS] Alert successfully sent to backend: {fake_alert['message']}")
            
    except Exception as e:
        print(f"[ERROR] Could not connect to backend. Is Uvicorn running? Error: {e}")

if __name__ == "__main__":
    asyncio.run(simulate_ai_detection())