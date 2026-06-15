import streamlit as st
import requests
import pandas as pd
import time

API_URL = "http://localhost:8000"

st.set_page_config(page_title="CampusWater AI", page_icon="💧", layout="wide")

st.markdown("""
<style>
.big-font { font-size:24px !important; font-weight: bold; }
.card { background: #f0f7ff; border-radius: 10px; padding: 20px; margin: 10px 0; border: 1px solid #d0e3f7; }
.alert-high { background: #ffe0e0; border-left: 4px solid #ff4444; padding: 10px; border-radius: 5px; margin: 5px 0; }
.alert-med { background: #fff3e0; border-left: 4px solid #ff9800; padding: 10px; border-radius: 5px; margin: 5px 0; }
.chat-msg-user { background: #e3f2fd; padding: 10px 15px; border-radius: 15px 15px 5px 15px; margin: 5px 0; }
.chat-msg-bot { background: #f5f5f5; padding: 10px 15px; border-radius: 15px 15px 15px 5px; margin: 5px 0; }
</style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("💧 CampusWater AI")
    st.caption("AI-Powered Water Usage Monitoring & Conservation Assistant")
    st.caption("Government SKSJTI KR Circle, Bengaluru | 1M1B AI for Sustainability Internship")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🚨 Anomaly Alerts", "🤖 AI Chatbot", "ℹ️ About"])

with tab1:
    try:
        stats = requests.get(f"{API_URL}/api/stats", timeout=5).json()
        if "error" not in stats:
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Water Used", f"{stats['total_usage_liters']:,} L")
            m2.metric("Avg Daily Usage", f"{stats['avg_daily_liters']:,} L")
            m3.metric("Buildings Monitored", stats["total_buildings"])
            m4.metric("Data Span", f"{stats['data_days']} days")
        usage = requests.get(f"{API_URL}/api/usage/all", params={"period": "90d"}, timeout=5).json()
        if "records" in usage:
            st.subheader("📈 Campus Water Usage (Last 90 Days)")
            df = pd.DataFrame(usage["records"])
            df["date"] = pd.to_datetime(df["date"])
            st.line_chart(df.set_index("date"))
    except Exception as e:
        st.warning(f"Backend not running. Start it with: python -m backend.api")

with tab2:
    st.subheader("🚨 Anomaly Detection")
    try:
        anom = requests.get(f"{API_URL}/api/anomalies", params={"days": 30}, timeout=5).json()
        if "stats" in anom:
            s = anom["stats"]
            a1, a2, a3 = st.columns(3)
            a1.metric("Anomalies Detected", s["anomalies_detected"])
            a2.metric("Buildings Affected", s["buildings_with_alerts"])
            a3.metric("Anomaly Rate", f"{s['anomaly_rate_pct']}%")
        st.divider()
        if anom.get("alerts"):
            st.subheader(f"Recent Alerts ({len(anom['alerts'])})")
            for alert in anom["alerts"]:
                sev = alert["severity"]
                cls = "alert-high" if sev == "HIGH" else "alert-med"
                st.markdown(
                    f'<div class="{cls}">'
                    f"<b>{alert['building']}</b> — {alert['date']} — "
                    f"Usage: <b>{alert['usage']:,}L</b> (expected < {alert['expected_upper']:,}L) "
                    f"<span style='color:{\"red\" if sev==\"HIGH\" else \"orange\"}'><b>[{sev}]</b></span>"
                    f"</div>", unsafe_allow_html=True
                )
        else:
            st.info("No anomalies detected in the last 7 days. ✅")
    except Exception as e:
        st.warning(f"Backend not running: {e}")

with tab3:
    st.subheader("🤖 Water Conservation Assistant")
    st.caption("Ask anything about water usage on campus")
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hi! I'm CampusWater AI. Ask me about water usage, conservation tips, or anomalies on campus!"}
        ]
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    if prompt := st.chat_input("Ask about water usage..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            try:
                resp = requests.get(f"{API_URL}/api/chat", params={"q": prompt}, timeout=30).json()
                answer = resp.get("answer", "Sorry, I couldn't process that.")
                st.markdown(answer)
                if resp.get("sources"):
                    with st.expander("📚 Sources"):
                        for s in resp["sources"]:
                            st.write(f"- {s}")
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                err = f"⚠️ Backend not available. Start the API server first. (Error: {e})"
                st.error(err)
                st.session_state.messages.append({"role": "assistant", "content": err})

with tab4:
    st.subheader("📋 Project: CampusWater AI")
    st.markdown("""
    **SDG 6:** Clean Water and Sanitation  
    **College:** Government SKSJTI KR Circle, Bengaluru  
    **Student:** Vishwanath Sanapur  

    **Tech Stack:**
    - **LLM:** Qwen3.5 (via Ollama)
    - **Embeddings:** Nomic Embed Text / Sentence Transformers
    - **RAG:** Vector retrieval with FAISS
    - **Backend:** FastAPI
    - **Frontend:** Streamlit
    - **Anomaly Detection:** Rolling z-score (14-day window)

    **Features:**
    - Real-time water usage monitoring
    - AI-powered anomaly detection & alerts
    - Conversational RAG chatbot for queries
    - Personalized conservation recommendations
    - Campus-wide aggregated data (no PII)
    """)

st.divider()
st.caption("1M1B AI for Sustainability Virtual Internship | In Collaboration with IBM SkillsBuild & AICTE")
