"""
src/dashboard.py — Real-Time Web Dashboard & Cyber Range Visualizer

Serves a live glassmorphic web dashboard with WebSockets broadcasting real-time:
- Network topology status (DMZ, Honeypot, Vault)
- Live terminal execution feed
- Agent team chat channel
- Match stats and dynamic flag tracker
"""

import asyncio
import json
import os
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import HTTPException
from fastapi.staticfiles import StaticFiles
import uvicorn
import glob

app = FastAPI(title="Hacker Society — Cyber Range Visualizer")

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"WebVisualizer Client Connected: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print("WebVisualizer Client Disconnected.")

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

# Global event broad-caster accessible by match runner
def broadcast_match_event(event_type: str, data: dict):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(manager.broadcast({"type": event_type, "data": data}))
    except Exception:
        pass


BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"
os.makedirs(WEB_DIR, exist_ok=True)


@app.get("/")
def get_dashboard():
    index_path = WEB_DIR / "index.html"
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Hacker Society Web Dashboard — index.html not found</h1>")


@app.websocket("/ws/match")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/logs")
def get_logs():
    logs_dir = BASE_DIR / "logs"
    if not logs_dir.exists():
        return JSONResponse(content={"logs": []})

    logs = []
    for log_file in glob.glob(str(logs_dir / "match_*_log.json")):
        match_id = Path(log_file).name.replace("match_", "").replace("_log.json", "")
        logs.append(match_id)
    return JSONResponse(content={"logs": logs})

@app.get("/api/logs/{match_id:path}")
def get_match_log(match_id: str):
    # Prevent path traversal
    if "/" in match_id or "\\" in match_id or ".." in match_id:
        raise HTTPException(status_code=400, detail="Invalid match_id format.")

    logs_dir = BASE_DIR / "logs"
    log_file = logs_dir / f"match_{match_id}_log.json"

    # Check if we are still inside logs directory after resolution just in case
    try:
        resolved_log_file = log_file.resolve()
        resolved_logs_dir = logs_dir.resolve()
        if not str(resolved_log_file).startswith(str(resolved_logs_dir)):
            raise HTTPException(status_code=400, detail="Invalid match_id format.")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid match_id format.")

    if not log_file.exists():
        raise HTTPException(status_code=404, detail="Match log not found.")

    with open(log_file, "r", encoding="utf-8") as f:
        try:
            log_data = json.load(f)
            return JSONResponse(content=log_data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Error reading match log.")


def start_dashboard(host="0.0.0.0", port=8080):
    print(f"\n=======================================================")
    print(f"   HACKER SOCIETY REAL-TIME CYBER RANGE DASHBOARD")
    print(f"   Open in browser: http://localhost:{port}")
    print(f"=======================================================\n")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_dashboard()
