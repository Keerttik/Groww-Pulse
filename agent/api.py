from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import sqlite3
import os
from typing import List, Optional

from agent.orchestrator import run_pulse
from agent.run_record import list_records, _row_to_record, DB_PATH
from agent.models.types import RunRecord
from agent.config import load_config

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = FastAPI(title="Groww Pulse API", description="API for the Groww Pulse Orchestrator")

# Allow CORS for the Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev, allow all. Restrict in prod.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class StartPulseRequest(BaseModel):
    week: str
    force: bool = False
    email_mode: str = "send"

@app.get("/api/runs", response_model=List[dict])
def get_runs(limit: int = 20):
    config = load_config()
    records = list_records(config.product.id, limit=limit)
    return [r.to_dict() for r in records]

@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail="Database not initialized")
        
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Run not found")
        
        record = _row_to_record(row)
        return record.to_dict()

@app.post("/api/runs/start")
def start_pulse(req: StartPulseRequest, background_tasks: BackgroundTasks):
    # Run the pulse in the background
    background_tasks.add_task(run_pulse, req.week, req.force, req.email_mode)
    return {"message": f"Pulse run for week {req.week} ({req.email_mode} mode) triggered in the background."}

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/logs")
def get_recent_logs(lines: int = 100):
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'logs')
    if not os.path.exists(log_dir):
        return {"logs": [], "message": f"Log dir not found at {log_dir}"}
    files = sorted([f for f in os.listdir(log_dir) if f.endswith('.log')], reverse=True)
    if not files:
        return {"logs": [], "message": "No log files found"}
    latest_file = os.path.join(log_dir, files[0])
    try:
        with open(latest_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.readlines()
        return {"file": files[0], "lines": content[-lines:]}
    except Exception as e:
        return {"error": str(e)}

# Serve static files from Vite build
if os.path.exists("web/dist"):
    app.mount("/assets", StaticFiles(directory="web/dist/assets"), name="assets")
    
    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        # Serve index.html for all other routes to support client-side routing
        # and ensure static files like favicon are served if they exist in dist root
        dist_path = os.path.join("web/dist", full_path)
        if os.path.exists(dist_path) and not os.path.isdir(dist_path):
            return FileResponse(dist_path)
        return FileResponse("web/dist/index.html")

