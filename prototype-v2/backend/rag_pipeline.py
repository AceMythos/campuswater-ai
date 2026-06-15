import json
import os
import numpy as np
import ollama
from sentence_transformers import SentenceTransformer

LLM_MODEL = "gemma3:4b"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

class RAGPipeline:
    def __init__(self):
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.docs = []
        self.embeddings = None
        self._load_kb()

    def _load_kb(self):
        kb = [
            {"topic": "overview", "content": "CampusWater AI monitors water usage at Government SKSJTI KR Circle Bengaluru. It covers 8 buildings across Hostel, Academic, Admin, and Recreation zones using real weather data from Open-Meteo and manual meter readings."},
            {"topic": "benchmarks", "content": "Standard water consumption benchmarks: CPHEEO recommends 135 LPCD for institutions with bathing. BIS IS 1172:1993 specifies 100 LPCD for hostels. BWSSB supplies ~130 LPCD in Bengaluru. Compare your campus usage against these government standards."},
            {"topic": "conservation", "content": "Water saving tips: 1) Fix dripping taps (15L/day each). 2) Use dual-flush toilets. 3) Report leaks via the chatbot. 4) Rainwater harvesting for gardening. 5) Water plants early morning. 6) Install aerators on taps. 7) Check for underground leaks if usage spikes."},
            {"topic": "sdg", "content": "SDG 6 - Clean Water and Sanitation, Target 6.4 (water-use efficiency). SDG 11 - Sustainable Cities. SDG 13 - Climate Action."},
            {"topic": "upload_data", "content": "To add real campus data: 1) Download the CSV template from /api/template. 2) Fill in meter readings from each building. 3) Upload via the Import tab in the dashboard. 4) The system will validate and replace sample data with your real readings."},
        ]

        texts = [d["content"] for d in kb]
        self.embeddings = self.embedder.encode(texts)
        self.docs = kb
        print(f"Loaded {len(self.docs)} knowledge base entries")

    def retrieve(self, query, top_k=3):
        if not self.docs:
            return []
        q_emb = self.embedder.encode([query])
        scores = np.dot(self.embeddings, q_emb.T).flatten()
        idxs = np.argsort(scores)[-top_k:][::-1]
        return [{"topic": self.docs[i]["topic"], "content": self.docs[i]["content"], "score": float(scores[i])} for i in idxs]

    def query(self, user_query, context_data=None):
        retrieved = self.retrieve(user_query)
        context = "\n".join([f"- {r['content']}" for r in retrieved]) if retrieved else ""

        system_prompt = "You are CampusWater AI, a water conservation assistant for Government SKSJTI KR Circle Bengaluru. Answer using the reference knowledge and data provided. Be concise, practical, and cite sources when possible."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Reference Knowledge:\n{context}\n\nData Context:\n{context_data or 'N/A'}\n\nUser: {user_query}"}
        ]

        response = ollama.chat(model=LLM_MODEL, messages=messages, stream=False)
        return {
            "answer": response["message"]["content"],
            "sources": [r["topic"] for r in retrieved]
        }
