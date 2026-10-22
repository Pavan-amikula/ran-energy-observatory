"""Local API, replay stream and validated external allocation ingestion."""
import asyncio
import csv
import io
import json
from collections import deque
from pathlib import Path
import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ValidationError
from .engine import Config, compare, validate_trace, power_trace

app = FastAPI(title="RAN Energy Observatory", version="1.0.0")
ROOT = Path(__file__).parent
app.mount("/static", StaticFiles(directory=ROOT/"static"), name="static")
telemetry = deque(maxlen=500)

@app.get("/")
def index(): return FileResponse(ROOT/"static"/"index.html")

@app.get("/api/health")
def health(): return {"status":"ok", "model":"symbol-level allocation abstraction", "version":"1.0.0"}

@app.post("/api/compare")
def comparison(config: Config): return compare(config)

class TraceRequest(BaseModel):
    config: Config
    csv: str = Field(max_length=4000000)

@app.post("/api/trace")
def trace(body: TraceRequest):
    try:
        rows = list(csv.DictReader(io.StringIO(body.csv)))
        return compare(body.config, validate_trace(rows,body.config), "user-imported packet trace; power remains modelled")
    except (ValueError, KeyError, TypeError) as e: raise HTTPException(422, str(e))

@app.get("/api/stream")
async def stream(request: Request, seed: int = 42, radio: str = "NR"):
    try: result = await asyncio.to_thread(compare,Config(seed=seed,radio=radio))
    except ValidationError as e: raise HTTPException(422,str(e))
    async def events():
        for i, item in enumerate(result["runs"]["compact"]["timeline"]):
            if await request.is_disconnected(): break
            yield "data: " + json.dumps({"sequence":i,"mode":"paced simulation replay",**item}) + "\n\n"
            await asyncio.sleep(.05)
    return StreamingResponse(events(),media_type="text/event-stream",headers={"Cache-Control":"no-cache"})

class AllocationFrame(BaseModel):
    source: str = Field(min_length=1,max_length=80)
    timestamp_ms: float = Field(ge=0,allow_inf_nan=False)
    radio: str = "NR"
    grid: list[list[int]] = Field(min_length=14,max_length=14,description="14 time rows, PRB columns; -1 control, 0 idle, 1–6 UE")

@app.post("/api/telemetry")
def ingest(frame: AllocationFrame):
    try: c = Config(radio=frame.radio)
    except ValidationError as e: raise HTTPException(422,str(e))
    if any(len(row)!=c.prbs or any(v < -1 or v > 6 for v in row) for row in frame.grid):
        raise HTTPException(422,"Expected 14 x PRB grid (-1 control, 0 idle, UE IDs 1–6)")
    grid = np.array(frame.grid)
    power, states, _ = power_trace(grid,c,True)
    record = dict(source=frame.source,timestamp_ms=frame.timestamp_ms,radio=frame.radio,
        grid=grid.T.tolist(),states=states.tolist(),prbs=c.prbs,
        estimated_power_w=round(float(power.mean()),3),utilization=float(np.mean(grid>0)),
        power_provenance="estimated using default uncalibrated model; allocation supplied by client")
    telemetry.append(record)
    return {"accepted":True,"buffer_size":len(telemetry),"record":record}

@app.get("/api/telemetry")
def latest(): return {"frames":list(telemetry)[-40:],"capacity":500}
