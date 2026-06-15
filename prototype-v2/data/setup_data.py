import json
import csv
import os
from datetime import datetime, timedelta

DATA_DIR = os.path.dirname(__file__)

# Legitimate reference: average water consumption in Indian hostels
# Source: CPHEEO Manual on Water Supply (Govt of India) - 135 LPCD for institutions
# Source: Bureau of Indian Standards IS 1172:1993
LPCD_INSTITUTIONAL = 135
LPCD_HOSTEL = 100

BENCHMARKS = {
    "cpheeo_institutional_lpcd": {
        "value": 135,
        "source": "CPHEEO Manual on Water Supply & Treatment, Ministry of Housing & Urban Affairs, Govt of India",
        "note": "Recommended water supply for institutions with bathing facilities"
    },
    "bis_is1172_lpcd": {
        "value": 100,
        "source": "Bureau of Indian Standards IS 1172:1993",
        "note": "Minimum water requirement for hostels"
    },
    "bwssb_bengaluru_supply_lpcd": {
        "value": 130,
        "source": "BWSSB Annual Report 2023-24",
        "note": "Average per-capita supply in BWSSB areas"
    },
    "niti_aayog_water_index": {
        "value": "1,121 billion cubic meters",
        "source": "NITI Aayog Composite Water Management Index 2019",
        "note": "India's total annual water demand projected for 2025"
    }
}

BUILDINGS = [
    {"name": "Boys Hostel - Block A", "type": "hostel", "occupants": 240, "zone": "Hostel Zone"},
    {"name": "Boys Hostel - Block B", "type": "hostel", "occupants": 280, "zone": "Hostel Zone"},
    {"name": "Girls Hostel", "type": "hostel", "occupants": 180, "zone": "Hostel Zone"},
    {"name": "Admin Block", "type": "admin", "occupants": 80, "zone": "Admin Zone"},
    {"name": "Academic Block", "type": "academic", "occupants": 600, "zone": "Academic Zone"},
    {"name": "Library", "type": "academic", "occupants": 200, "zone": "Academic Zone"},
    {"name": "Cafeteria", "type": "utility", "occupants": 150, "zone": "Recreation Zone"},
    {"name": "Workshop Lab", "type": "utility", "occupants": 60, "zone": "Academic Zone"},
]

def generate_template():
    headers = ["date", "building", "zone", "usage_liters", "meter_reading_kL", "notes"]
    path = os.path.join(DATA_DIR, "data_entry_template.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerow(["2026-06-01", "Boys Hostel - Block A", "Hostel Zone", "", "", "Enter reading from meter"])
        w.writerow(["2026-06-01", "Boys Hostel - Block B", "Hostel Zone", "", "", ""])
        w.writerow(["2026-06-01", "Girls Hostel", "Hostel Zone", "", "", ""])
        w.writerow(["2026-06-01", "Admin Block", "Admin Zone", "", "", ""])
        w.writerow(["2026-06-01", "Academic Block", "Academic Zone", "", "", ""])
        w.writerow(["2026-06-01", "Library", "Academic Zone", "", "", ""])
        w.writerow(["2026-06-01", "Cafeteria", "Recreation Zone", "", "", ""])
        w.writerow(["2026-06-01", "Workshop Lab", "Academic Zone", "", "", ""])
    print(f"Template created: {path}")
    return path

def create_sample_water_data():
    import random
    random.seed(123)
    records = []
    base_date = datetime(2026, 1, 1)

    with open(os.path.join(DATA_DIR, "weather_bengaluru.json")) as f:
        weather = json.load(f)

    weather_by_date = {}
    for i, d in enumerate(weather["daily"]["time"]):
        weather_by_date[d] = {
            "temp": weather["daily"]["temperature_2m_mean"][i],
            "rain": weather["daily"]["precipitation_sum"][i] or 0
        }

    for day_offset in range(166):  # Jan 1 to Jun 15 2026
        date = (base_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        w = weather_by_date.get(date, {"temp": 25, "rain": 0})

        for bldg in BUILDINGS:
            base = bldg["occupants"] * LPCD_HOSTEL if bldg["type"] == "hostel" else \
                   bldg["occupants"] * LPCD_INSTITUTIONAL * 0.6

            temp_factor = 1 + (max(0, w["temp"] - 25)) * 0.015
            weekday_factor = 1.15 if datetime.strptime(date, "%Y-%m-%d").weekday() < 5 else 0.75
            noise = random.uniform(0.9, 1.1)

            usage = base * temp_factor * weekday_factor * noise
            usage = round(max(usage, base * 0.4))

            is_anomaly = 0
            if random.random() < 0.015:
                usage = int(usage * random.uniform(1.6, 2.2))
                is_anomaly = 1

            records.append({
                "date": date,
                "building": bldg["name"],
                "zone": bldg["zone"],
                "occupants": bldg["occupants"],
                "building_type": bldg["type"],
                "usage_liters": usage,
                "temperature_c": round(w["temp"], 1),
                "rainfall_mm": round(w["rain"], 1),
                "is_anomaly": is_anomaly
            })

    path = os.path.join(DATA_DIR, "sample_water_usage.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=records[0].keys())
        w.writeheader()
        w.writerows(records)
    print(f"Sample water data: {len(records)} records across {len(BUILDINGS)} buildings, {day_offset+1} days")
    print("NOTE: This is SAMPLE data. Replace with real meter readings from your campus.")
    return path

if __name__ == "__main__":
    print("=== Generating prototype-v2 assets ===")
    print(f"Weather data: 897 days of real Bengaluru data (Open-Meteo API)")
    print(f"Buildings: {len(BUILDINGS)} campus buildings configured")
    print(f"Benchmarks: {len(BENCHMARKS)} reference standards loaded")

    t = generate_template()
    s = create_sample_water_data()

    with open(os.path.join(DATA_DIR, "benchmarks.json"), "w") as f:
        json.dump(BENCHMARKS, f, indent=2)

    with open(os.path.join(DATA_DIR, "buildings.json"), "w") as f:
        json.dump(BUILDINGS, f, indent=2)

    print("\nAll assets generated.")
    print("\n>> NEXT STEP: Download data_entry_template.csv, fill with your college's real meter readings, then upload via the app <<")
