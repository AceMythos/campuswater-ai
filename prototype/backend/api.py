import sys
import os
import json
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

from backend.rag_pipeline import RAGPipeline
from backend.anomaly_detector import AnomalyDetector
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CampusWater AI API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

rag = None
detector = AnomalyDetector()
df_cache = None

def load_data():
    global df_cache, rag
    if df_cache is None:
        path = os.path.join(DATA_DIR, "water_usage.csv")
        df_cache = pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()
        print(f"Loaded {len(df_cache)} records")
    if rag is None:
        rag = RAGPipeline()
    return df_cache

@app.on_event("startup")
def startup():
    load_data()

@app.get("/")
def root():
    return {"service": "CampusWater AI", "status": "running"}

@app.get("/api/stats")
def stats():
    df = load_data()
    if df.empty:
        return {"error": "No data"}
    total = int(df["usage_liters"].sum())
    avg_daily = int(df.groupby("date")["usage_liters"].sum().mean())
    building_usage = df.groupby("building")["usage_liters"].sum().sort_values(ascending=False)
    return {
        "total_usage_liters": total,
        "avg_daily_liters": avg_daily,
        "total_buildings": int(df["building"].nunique()),
        "total_zones": int(df["zone"].nunique()),
        "data_days": int(df["date"].nunique()),
        "top_building": str(building_usage.index[0]),
        "top_building_usage": int(building_usage.iloc[0])
    }

@app.get("/api/anomalies")
def anomalies(days: int = Query(7)):
    df = load_data()
    if df.empty:
        return {"alerts": []}
    df_anom = detector.detect(df)
    alerts = detector.get_recent_alerts(df_anom, days)
    stats = detector.get_stats(df_anom)
    return {"alerts": alerts, "stats": stats}

@app.get("/api/usage/{building}")
def building_usage(building: str, period: str = Query("30d")):
    df = load_data()
    if df.empty:
        return {"error": "No data"}
    if building != "all" and building not in df["building"].unique():
        return {"error": f"Building '{building}' not found. Options: {list(df['building'].unique())}"}
    bdf = df if building == "all" else df[df["building"] == building]
    days = int(period.replace("d", ""))
    bdf = bdf.tail(days * (1 if building != "all" else len(df["building"].unique())))
    records = bdf.groupby("date").agg({"usage_liters": "sum"}).reset_index()
    return {
        "building": building,
        "records": records.to_dict(orient="records"),
        "avg_daily": int(records["usage_liters"].mean()),
        "total": int(records["usage_liters"].sum())
    }

@app.get("/api/chat")
def chat(q: str = Query("")):
    df = load_data()
    if not q:
        return {"answer": "Ask me something about water usage on campus!", "sources": []}
    context = ""
    if not df.empty:
        recent = df.tail(30)
        context = recent.to_string()
    result = rag.query(q, context_data=context)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
