import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

np.random.seed(42)

BUILDINGS = ["Block A", "Block B", "Block C", "Block D", "Admin Block", "Library", "Cafeteria"]
ZONES = ["Hostel Zone", "Academic Zone", "Admin Zone", "Recreation Zone"]
BUILDING_TO_ZONE = {
    "Block A": "Hostel Zone", "Block B": "Hostel Zone",
    "Block C": "Hostel Zone", "Block D": "Hostel Zone",
    "Admin Block": "Admin Zone", "Library": "Academic Zone",
    "Cafeteria": "Recreation Zone"
}

BASE_USAGE = {
    "Block A": 48000, "Block B": 51000, "Block C": 46000, "Block D": 49000,
    "Admin Block": 12000, "Library": 8000, "Cafeteria": 15000
}

def generate_usage_data(days=365):
    records = []
    base_date = datetime(2026, 1, 1)
    for i in range(days):
        date = base_date + timedelta(days=i)
        month = date.month
        for bldg in BUILDINGS:
            base = BASE_USAGE[bldg]
            seasonal = 1 + 0.3 * np.sin(2 * np.pi * (month - 3) / 12)
            weekday = 1.2 if date.weekday() < 5 else 0.8
            noise = np.random.normal(1, 0.08)
            usage = base * seasonal * weekday * noise
            usage = round(max(usage, base * 0.3))

            is_anomaly = 0
            if np.random.random() < 0.02:
                usage = int(usage * (1.5 + np.random.random() * 0.8))
                is_anomaly = 1

            temp = round(25 + 10 * np.sin(2 * np.pi * (month - 6) / 12) + np.random.normal(0, 3), 1)
            rainfall = round(max(0, np.random.gamma(2, 10) * (0.5 + 0.5 * np.sin(2 * np.pi * (month - 6) / 12))), 1)

            records.append({
                "date": date.strftime("%Y-%m-%d"),
                "building": bldg,
                "zone": BUILDING_TO_ZONE[bldg],
                "usage_liters": usage,
                "temperature_c": temp,
                "rainfall_mm": rainfall,
                "is_anomaly": is_anomaly,
                "day_of_week": date.strftime("%A"),
                "month": date.strftime("%B")
            })
    return pd.DataFrame(records)

def generate_knowledge_base():
    return [
        {"topic": "overview", "content": "CampusWater AI monitors water usage across Government SKSJTI KR Circle Bengaluru campus. It tracks 7 buildings across 4 zones, processing daily consumption data to detect anomalies and provide conservation insights."},
        {"topic": "water sources", "content": "The campus water supply comes from BWSSB mains (70%) and a borewell (30%). Total daily capacity is approximately 250,000 liters. Peak demand months are March-May."},
        {"topic": "conservation tips", "content": "1) Fix leaking taps immediately - a dripping tap wastes 15L/day. 2) Use dual-flush toilets. 3) Report leaks via the chatbot. 4) Rainwater harvesting recharges the borewell. 5) Water gardens in early morning to reduce evaporation."},
        {"topic": "sdg", "content": "This project aligns with SDG 6 (Clean Water and Sanitation) - Target 6.4: Water-use efficiency, and SDG 11 (Sustainable Cities and Communities) - Target 11.6: Environmental impact."},
        {"topic": "buildings", "content": "Block A (hostel, 300 students), Block B (hostel, 350 students), Block C (hostel, 280 students), Block D (hostel, 320 students), Admin Block, Library, and Cafeteria."},
        {"topic": "anomaly", "content": "Anomalies are detected when daily usage exceeds 2 standard deviations above the 14-day rolling average. Common causes: pipe leaks, stuck valves, unattended taps, or construction activity."},
    ]

if __name__ == "__main__":
    os.makedirs(os.path.dirname(__file__), exist_ok=True)
    df = generate_usage_data()
    df.to_csv(os.path.join(os.path.dirname(__file__), "water_usage.csv"), index=False)
    kb = generate_knowledge_base()
    with open(os.path.join(os.path.dirname(__file__), "knowledge_base.json"), "w") as f:
        json.dump(kb, f, indent=2)
    print(f"Generated {len(df)} records and {len(kb)} knowledge base entries")
