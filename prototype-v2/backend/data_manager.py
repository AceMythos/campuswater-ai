import os
import json
import csv
import pandas as pd
import numpy as np
from io import StringIO

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

class DataManager:
    def __init__(self):
        self.weather = self._load_weather()
        self.buildings = self._load_buildings()
        self.benchmarks = self._load_benchmarks()
        self.water_data = None
        self._load_water_data()

    def _load_weather(self):
        path = os.path.join(DATA_DIR, "weather_bengaluru.json")
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return {"daily": {"time": [], "temperature_2m_mean": [], "precipitation_sum": []}}

    def _load_buildings(self):
        path = os.path.join(DATA_DIR, "buildings.json")
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return []

    def _load_benchmarks(self):
        path = os.path.join(DATA_DIR, "benchmarks.json")
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return {}

    def _load_water_data(self):
        path = os.path.join(DATA_DIR, "real_water_data.csv")
        if os.path.exists(path):
            df = pd.read_csv(path)
            df["date"] = pd.to_datetime(df["date"])
            zone_map = {"North": "Hostel Zone", "South": "Academic Zone", "East": "Admin Zone", "West": "Recreation Zone", "Central": "Academic Zone"}
            type_map = {"North": "hostel", "South": "academic", "East": "admin", "West": "utility", "Central": "academic"}
            occ_map = {"North": 300, "South": 400, "East": 80, "West": 150, "Central": 200}
            df["zone"] = df["region"].map(zone_map)
            df["building_type"] = df["region"].map(type_map)
            df["occupants"] = df["region"].map(occ_map)
            df["is_anomaly"] = 0
            df = df.rename(columns={"region": "building", "consumption_liters": "usage_liters"})
            self.water_data = df
            print(f"Loaded REAL dataset: {len(df)} records, {df['building'].nunique()} regions, {df['date'].nunique()} days")
        else:
            path = os.path.join(DATA_DIR, "sample_water_usage.csv")
            if os.path.exists(path):
                self.water_data = pd.read_csv(path)
                self.water_data["date"] = pd.to_datetime(self.water_data["date"])

    def get_weather(self, days=30):
        dates = self.weather["daily"]["time"][-days:]
        temps = self.weather["daily"]["temperature_2m_mean"][-days:]
        rains = self.weather["daily"]["precipitation_sum"][-days:]
        return pd.DataFrame({
            "date": pd.to_datetime(dates),
            "temperature_c": temps,
            "rainfall_mm": [r or 0 for r in rains]
        })

    def import_csv(self, csv_content):
        df = pd.read_csv(StringIO(csv_content))
        required = ["date", "building", "usage_liters"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            return {"success": False, "error": f"Missing columns: {', '.join(missing)}. Required: date, building, usage_liters"}

        df["date"] = pd.to_datetime(df["date"])
        df["usage_liters"] = pd.to_numeric(df["usage_liters"], errors="coerce")

        valid_buildings = [b["name"] for b in self.buildings]
        invalid = df[~df["building"].isin(valid_buildings)]["building"].unique()
        if len(invalid) > 0:
            return {"success": False, "error": f"Unknown buildings: {list(invalid)}. Valid: {valid_buildings}"}

        na_rows = df["usage_liters"].isna().sum()
        if na_rows > 0:
            return {"success": False, "error": f"{na_rows} rows have non-numeric usage_liters. Check your data."}

        with open(os.path.join(DATA_DIR, "imported_water_usage.csv"), "w", newline="") as f:
            df.to_csv(f, index=False)

        self.water_data = df

        return {
            "success": True,
            "rows": len(df),
            "buildings": list(df["building"].unique()),
            "date_range": f"{df['date'].min().date()} to {df['date'].max().date()}",
            "total_liters": int(df["usage_liters"].sum())
        }

    def add_reading(self, date, building, usage_liters, notes=""):
        entry = {
            "date": pd.to_datetime(date),
            "building": building,
            "zone": next((b["zone"] for b in self.buildings if b["name"] == building), ""),
            "occupants": next((b["occupants"] for b in self.buildings if b["name"] == building), 0),
            "building_type": next((b["type"] for b in self.buildings if b["name"] == building), ""),
            "usage_liters": float(usage_liters),
            "temperature_c": np.nan,
            "rainfall_mm": np.nan,
            "is_anomaly": 0,
            "notes": notes
        }

        new_row = pd.DataFrame([entry])
        if self.water_data is not None:
            self.water_data = pd.concat([self.water_data, new_row], ignore_index=True)
        else:
            self.water_data = new_row

        path = os.path.join(DATA_DIR, "imported_water_usage.csv")
        self.water_data.to_csv(path, index=False)
        return {"success": True, "total_records": len(self.water_data)}

    def get_stats(self):
        if self.water_data is None or self.water_data.empty:
            return {"error": "No water data loaded. Import a CSV or add readings."}
        df = self.water_data
        total = int(df["usage_liters"].sum())
        avg_daily = int(df.groupby("date")["usage_liters"].sum().mean())
        bldg_usage = df.groupby("building")["usage_liters"].sum().sort_values(ascending=False)
        return {
            "total_usage_liters": total,
            "avg_daily_liters": avg_daily,
            "buildings": int(df["building"].nunique()),
            "zones": int(df["zone"].nunique()),
            "data_days": int(df["date"].nunique()),
            "top_building": str(bldg_usage.index[0]),
            "top_building_usage": int(bldg_usage.iloc[0]),
            "total_occupants": sum(b["occupants"] for b in self.buildings),
            "lpcd_avg": round(total / (sum(b["occupants"] for b in self.buildings) * df["date"].nunique()), 1),
            "data_source": "REAL: Kaggle Water Consumption Forecasting Dataset (sahideseker)" if os.path.exists(os.path.join(DATA_DIR, "real_water_data.csv")) else "Sample data"
        }

    def get_building_usage(self, building, days=30):
        if self.water_data is None:
            return {"error": "No data"}
        df = self.water_data
        if building != "all":
            df = df[df["building"] == building]
        df = df.tail(days * (1 if building != "all" else df["building"].nunique()))
        records = df.groupby("date").agg({"usage_liters": "sum"}).reset_index()
        return {
            "building": building,
            "records": records.to_dict(orient="records"),
            "avg_daily": int(records["usage_liters"].mean()),
            "total": int(records["usage_liters"].sum())
        }

    def get_anomalies(self, window=14, std_mult=2.0):
        if self.water_data is None:
            return {"alerts": [], "stats": {}}
        df = self.water_data.copy()
        df = df.sort_values(["building", "date"])
        buildings = []
        for bldg, group in df.groupby("building"):
            group = group.copy()
            group["rolling_mean"] = group["usage_liters"].rolling(window, min_periods=3).mean()
            group["rolling_std"] = group["usage_liters"].rolling(window, min_periods=3).std()
            group["upper"] = group["rolling_mean"] + std_mult * group["rolling_std"]
            group["lower"] = (group["rolling_mean"] - std_mult * group["rolling_std"]).clip(lower=0)
            group["anomaly"] = ((group["usage_liters"] > group["upper"]) | (group["usage_liters"] < group["lower"])).astype(int)
            buildings.append(group)
        df = pd.concat(buildings)
        total = len(df)
        anom_count = int(df["anomaly"].sum())
        alerts = df[df["anomaly"] == 1].tail(10)
        alert_list = []
        for _, row in alerts.iterrows():
            alert_list.append({
                "building": row["building"],
                "date": str(row["date"])[:10],
                "usage": int(row["usage_liters"]),
                "expected_upper": int(row["upper"]) if pd.notna(row["upper"]) else 0,
                "severity": "HIGH" if row["usage_liters"] > row["upper"] * 1.5 else "MEDIUM"
            })
        return {
            "alerts": alert_list,
            "stats": {
                "total_records": total,
                "anomalies_detected": anom_count,
                "anomaly_rate_pct": round(anom_count / total * 100, 1) if total else 0,
                "buildings_with_alerts": int(df[df["anomaly"] == 1]["building"].nunique())
            }
        }
