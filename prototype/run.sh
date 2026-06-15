#!/bin/bash
echo "=== CampusWater AI Prototype ==="
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "[1/3] Generating data..."
python3 data/generator.py

echo ""
echo "[2/3] Starting API server..."
cd "$SCRIPT_DIR"
python3 -m uvicorn backend.api:app --host 0.0.0.0 --port 8000 &
API_PID=$!
echo "API running (PID: $API_PID) on http://localhost:8000"

sleep 3

echo ""
echo "[3/3] Starting Streamlit frontend..."
python3 -m streamlit run frontend/app.py --server.port 8501 &
FRONTEND_PID=$!
echo "Frontend running (PID: $FRONTEND_PID) on http://localhost:8501"

echo ""
echo "=== All services started ==="
echo "API:      http://localhost:8000"
echo "Frontend: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop all services"

trap "kill $API_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
