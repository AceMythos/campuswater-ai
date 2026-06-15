import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from backend.data_manager import DataManager
from backend.rag_pipeline import RAGPipeline
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="CampusWater AI v2 - Legitimate Data")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

dm = DataManager()
rag = RAGPipeline()

class ReadingInput(BaseModel):
    date: str
    building: str
    usage_liters: float
    notes: str = ""

class CSVImport(BaseModel):
    content: str

@ app.on_event("startup")
def startup():
    print(f"v2 loaded: {len(dm.buildings)} buildings, {len(dm.weather['daily']['time'])} weather days, {len(dm.benchmarks)} benchmarks")
    if dm.water_data is not None:
        print(f"Water data: {len(dm.water_data)} records")

@ app.get("/")
def root():
    return {"service": "CampusWater AI v2", "status": "running", "data_mode": dm.get_stats().get("data_source", "sample")}

@ app.get("/api/stats")
def stats():
    return dm.get_stats()

@ app.get("/api/buildings")
def buildings():
    return dm.buildings

@ app.get("/api/benchmarks")
def benchmarks():
    return dm.benchmarks

@ app.get("/api/weather")
def weather(days: int = Query(30)):
    w = dm.get_weather(days)
    return {"records": w.to_dict(orient="records")}

@ app.get("/api/usage/{building}")
def building_usage(building: str, days: int = Query(30)):
    result = dm.get_building_usage(building, days)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result

@ app.get("/api/anomalies")
def anomalies(days: int = Query(7)):
    return dm.get_anomalies()

@ app.post("/api/import")
def import_data(data: CSVImport):
    result = dm.import_csv(data.content)
    if not result["success"]:
        raise HTTPException(400, result["error"])
    return result

@ app.post("/api/reading")
def add_reading(reading: ReadingInput):
    return dm.add_reading(reading.date, reading.building, reading.usage_liters, reading.notes)

@ app.get("/api/template")
def download_template():
    from fastapi.responses import FileResponse
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "data_entry_template.csv")
    return FileResponse(path, filename="campuswater_data_template.csv", media_type="text/csv")

@ app.get("/api/chat")
def chat(q: str = Query("")):
    if not q:
        return {"answer": "Ask me about water usage, conservation, or benchmarks!", "sources": []}
    context = ""
    stats = dm.get_stats()
    if "error" not in stats:
        context = f"Campus Stats: {stats}"
    result = rag.query(q, context_data=context)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
