import pandas as pd
import numpy as np

class AnomalyDetector:
    def __init__(self, window=14, std_mult=2.0):
        self.window = window
        self.std_mult = std_mult

    def detect(self, df):
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values(["building", "date"])
        buildings = []
        for bldg, group in df.groupby("building"):
            group = group.reset_index(drop=True)
            group["rolling_mean"] = group["usage_liters"].rolling(self.window, min_periods=3).mean()
            group["rolling_std"] = group["usage_liters"].rolling(self.window, min_periods=3).std()
            group["upper_bound"] = group["rolling_mean"] + self.std_mult * group["rolling_std"]
            group["lower_bound"] = (group["rolling_mean"] - self.std_mult * group["rolling_std"]).clip(lower=0)
            group["detected_anomaly"] = (
                (group["usage_liters"] > group["upper_bound"]) |
                (group["usage_liters"] < group["lower_bound"])
            ).astype(int)
            buildings.append(group)
        return pd.concat(buildings, ignore_index=True)

    def get_recent_alerts(self, df, days=7):
        df = df.copy()
        if "detected_anomaly" not in df.columns:
            df = self.detect(df)
        recent = df[df["detected_anomaly"] == 1]
        if len(recent) > 0:
            recent = recent.sort_values("date", ascending=False).head(10)
            alerts = []
            for _, row in recent.iterrows():
                alerts.append({
                    "building": row["building"],
                    "date": str(row["date"])[:10],
                    "usage": int(row["usage_liters"]),
                    "expected_upper": int(row["upper_bound"]),
                    "severity": "HIGH" if row["usage_liters"] > row["upper_bound"] * 1.5 else "MEDIUM"
                })
            return alerts
        return []

    def get_stats(self, df):
        df = df.copy()
        if "detected_anomaly" not in df.columns:
            df = self.detect(df)
        total = len(df)
        anomaly_count = int(df["detected_anomaly"].sum())
        anomaly_pct = round(anomaly_count / total * 100, 1) if total > 0 else 0
        return {
            "total_records": total,
            "anomalies_detected": anomaly_count,
            "anomaly_rate_pct": anomaly_pct,
            "buildings_with_alerts": df[df["detected_anomaly"] == 1]["building"].nunique()
        }
