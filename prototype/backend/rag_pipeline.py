import json
import os
import numpy as np
import ollama
from sentence_transformers import SentenceTransformer

EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "gemma3:4b"

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

class RAGPipeline:
    def __init__(self):
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.kb_docs = []
        self.kb_embeddings = None
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        kb_path = os.path.join(DATA_DIR, "knowledge_base.json")
        if os.path.exists(kb_path):
            with open(kb_path) as f:
                self.kb_docs = json.load(f)
            texts = [d["content"] for d in self.kb_docs]
            self.kb_embeddings = self.embedder.encode(texts)
            print(f"Loaded {len(self.kb_docs)} knowledge base documents")

    def retrieve(self, query, top_k=3):
        if not self.kb_docs:
            return []
        query_emb = self.embedder.encode([query])
        scores = np.dot(self.kb_embeddings, query_emb.T).flatten()
        top_indices = np.argsort(scores)[-top_k:][::-1]
        results = []
        for idx in top_indices:
            results.append({
                "topic": self.kb_docs[idx]["topic"],
                "content": self.kb_docs[idx]["content"],
                "score": float(scores[idx])
            })
        return results

    def query(self, user_query, context_data=None):
        retrieved = self.retrieve(user_query)

        context = ""
        if retrieved:
            context = "Reference Knowledge:\n" + "\n".join(
                [f"- {r['content']}" for r in retrieved]
            )

        data_context = ""
        if context_data is not None:
            data_context = f"Water Usage Data Context:\n{context_data}"

        system_prompt = """You are CampusWater AI, a helpful water conservation assistant for Government SKSJTI KR Circle Bengaluru campus. You help students and staff understand water usage patterns, detect waste, and suggest conservation measures. Be concise, friendly, and use data when available. If you don't know something, say so."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{context}\n\n{data_context}\n\nUser Query: {user_query}"}
        ]

        response = ollama.chat(model=LLM_MODEL, messages=messages, stream=False)
        answer = response["message"]["content"]

        return {
            "answer": answer,
            "sources": [r["topic"] for r in retrieved] if retrieved else []
        }

if __name__ == "__main__":
    rag = RAGPipeline()
    result = rag.query("How can we save water on campus?")
    print(f"Q: How can we save water on campus?\nA: {result['answer']}\n")
    print(f"Sources: {result['sources']}")
