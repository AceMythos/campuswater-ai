# CampusWater AI

**AI-Powered Water Usage Monitoring & Conservation Assistant**

1M1B AI for Sustainability Virtual Internship — in collaboration with IBM SkillsBuild & AICTE

**Student:** Vishwanath Sanapur  
**College:** Government SKSJTI, KR Circle, Bengaluru  

## Overview

CampusWater AI is an AI-driven solution for monitoring, predicting, and optimizing water consumption on college campuses. It uses a Retrieval-Augmented Generation (RAG) pipeline with LLMs to provide real-time insights, leak detection alerts, and personalized conservation recommendations.

## SDG Alignment

- **Primary:** SDG 6 — Clean Water and Sanitation
- **Secondary:** SDG 11 — Sustainable Cities and Communities
- **Secondary:** SDG 13 — Climate Action

## Working Prototype (`prototype/`)

A fully functional prototype is included with:

| Component | Technology | Description |
|---|---|---|
| **RAG Pipeline** | Ollama + Sentence Transformers + FAISS | Retrieves water data and KB context, generates natural-language answers |
| **LLM** | Gemma3:4b / Qwen3.5 (via Ollama) | Core language model for conversational AI |
| **Anomaly Detection** | Rolling z-score (14-day window) | Flags unusual usage patterns in real-time |
| **Backend API** | FastAPI (port 8000) | REST endpoints for stats, anomalies, usage data, and chat |
| **Frontend** | Streamlit (port 8501) | Dashboard with charts + chatbot interface |
| **Data** | Python generator | 1 year of realistic campus water usage across 7 buildings |

## How to Run

```bash
cd prototype
bash run.sh
# Or manually:
python3 data/generator.py                    # Generate data
python3 -m uvicorn backend.api:app --port 8000  # Start API
streamlit run frontend/app.py --server.port 8501  # Start UI
```

Then open **http://localhost:8501** in your browser.

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/stats` | Campus-wide water usage statistics |
| `GET /api/anomalies?days=7` | Recent anomaly alerts |
| `GET /api/usage/{building}?period=30d` | Usage history for a building |
| `GET /api/chat?q=question` | Ask the AI chatbot anything |

## Key Features

- Real-time water usage monitoring via conversational AI
- AI-powered anomaly detection for leak identification
- Usage insights based on historical data and weather patterns
- Personalized conservation recommendations
- Campus-wide aggregation (no individual PII collected)

## Deliverables

- `CampusWater_AI_Project.pdf` — Full project report (7 pages)
- `prototype/` — Working Python prototype (RAG + anomaly detection + chatbot)

## Tech Stack

- **LLM:** Gemma3/Qwen3.5 (via Ollama)
- **RAG:** Sentence Transformers + FAISS vector retrieval
- **Backend:** FastAPI + Python
- **Frontend:** Streamlit
- **Anomaly Detection:** Statistical rolling z-score
- **Data:** Synthetic campus water usage generator
