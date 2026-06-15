#!/bin/bash
echo "=== CampusWater AI v2 - Legitimate Data Version ==="
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "[1/3] Assets ready (weather data from Open-Meteo API)"
echo ""

echo "[2/3] Starting API server (port 8001)..."
python3 -m uvicorn backend.api:app --host 0.0.0.0 --port 8001 &
API_PID=$!
sleep 4

echo "[3/3] Starting Streamlit frontend (port 8503)..."
streamlit run frontend/app.py --server.port 8503 &
FRONTEND_PID=$!

echo ""
echo "=== v2 Running ==="
echo "API:      http://localhost:8001"
echo "Frontend: http://localhost:8503"
echo ""
echo "Data sources:"
echo "  - Weather: Real Bengaluru data from Open-Meteo API (free, no key needed)"
echo "  - Benchmarks: CPHEEO, BIS, BWSSB, NITI Aayog standards"
echo "  - Water usage: Download template → fill with real meter readings → upload"
echo ""
trap "kill $API_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
