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
    email_mode: str = "draft"

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
    return {"message": f"Pulse run for week {req.week} triggered in the background."}

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

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

