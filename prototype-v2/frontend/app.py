import streamlit as st
import requests
import pandas as pd
from datetime import date

API_URL = "http://localhost:8001"

st.set_page_config(page_title="CampusWater AI v2", page_icon="💧", layout="wide")

st.markdown("""
<style>
.metric-card { background:#f0f7ff; border-radius:10px; padding:15px; border:1px solid #d0e3f7; }
.alert-h { background:#ffe0e0; border-left:4px solid #f44; padding:10px; border-radius:5px; }
.alert-m { background:#fff3e0; border-left:4px solid #f90; padding:10px; border-radius:5px; }
.tag-real { background:#4caf50; color:white; padding:2px 10px; border-radius:12px; font-size:12px; }
tag-sample { background:#ff9800; color:white; padding:2px 10px; border-radius:12px; font-size:12px; }
</style>
""", unsafe_allow_html=True)

st.title("💧 CampusWater AI v2")
st.caption("Legitimate Data Version | Government SKSJTI KR Circle, Bengaluru")

try:
    root = requests.get(f"{API_URL}/", timeout=3).json()
    data_mode = root.get("data_mode", "unknown")
    badge = "🟢 REAL DATA" if "Imported" in data_mode else "🟡 SAMPLE DATA"
    st.caption(f"{badge} — {data_mode}")
except:
    st.error("Backend not running. Start with: python3 -m backend.api")
    st.stop()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "📥 Import Data", "➕ Add Reading", "🤖 AI Chat", "ℹ️ About"])

with tab1:
    try:
        stats = requests.get(f"{API_URL}/api/stats", timeout=3).json()
        if "error" not in stats:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Water Used", f"{stats['total_usage_liters']:,} L")
            c2.metric("Avg Daily Usage", f"{stats['avg_daily_liters']:,} L")
            c3.metric("LPCD Average", f"{stats['lpcd_avg']} L/person/day")
            c4.metric("Data Span", f"{stats['data_days']} days")

            st.subheader("📈 Water Usage Trend")
            usage = requests.get(f"{API_URL}/api/usage/all", params={"days": 90}, timeout=5).json()
            if "records" in usage:
                df = pd.DataFrame(usage["records"])
                df["date"] = pd.to_datetime(df["date"])
                st.line_chart(df.set_index("date"))

        st.subheader("📋 Reference Benchmarks (Government Standards)")
        benches = requests.get(f"{API_URL}/api/benchmarks", timeout=3).json()
        bdf = pd.DataFrame([
            {"Standard": k, "Value": v["value"], "Source": v["source"]}
            for k, v in benches.items()
        ])
        st.dataframe(bdf, use_container_width=True, hide_index=True)

        st.subheader("🌤 Real Weather Data (Bengaluru - Open-Meteo API)")
        w = requests.get(f"{API_URL}/api/weather", params={"days": 30}, timeout=5).json()
        if "records" in w:
            wdf = pd.DataFrame(w["records"])
            wdf["date"] = pd.to_datetime(wdf["date"])
            st.line_chart(wdf.set_index("date")[["temperature_c", "rainfall_mm"]])

        st.subheader("🚨 Anomaly Detection")
        anom = requests.get(f"{API_URL}/api/anomalies", timeout=3).json()
        if anom.get("alerts"):
            for a in anom["alerts"]:
                cls = "alert-h" if a["severity"] == "HIGH" else "alert-m"
                st.markdown(f'<div class="{cls}"><b>{a["building"]}</b> — {a["date"]} — Usage: {a["usage"]:,}L (expected < {a["expected_upper"]:,}L) <b>[{a["severity"]}]</b></div>', unsafe_allow_html=True)
        else:
            st.info("No anomalies detected ✅")
    except Exception as e:
        st.warning(f"Backend error: {e}")

with tab2:
    st.subheader("📥 Import Real Campus Data")

    st.markdown("""
    **How to add your college's real data:**
    1. Download the CSV template below
    2. Fill it with your actual meter readings from each building
    3. Upload the completed CSV here
    4. The system will replace sample data with your real readings
    """)

    if st.button("📄 Download CSV Template"):
        resp = requests.get(f"{API_URL}/api/template", timeout=5)
        st.download_button(
            "Save Template", data=resp.content,
            file_name="campuswater_data_template.csv",
            mime="text/csv"
        )

    uploaded = st.file_uploader("Upload completed CSV", type=["csv"])
    if uploaded is not None:
        content = uploaded.getvalue().decode()
        resp = requests.post(f"{API_URL}/api/import", json={"content": content}, timeout=10)
        result = resp.json()
        if result.get("success"):
            st.success(f"✅ Imported {result['rows']} records from {len(result['buildings'])} buildings ({result['date_range']}). Total: {result['total_liters']:,}L")
            st.rerun()
        else:
            st.error(f"❌ {result.get('error', 'Unknown error')}")

with tab3:
    st.subheader("➕ Add a Manual Reading")
    st.caption("Enter a meter reading for any building")

    bldgs = requests.get(f"{API_URL}/api/buildings", timeout=3).json()
    bldg_names = [b["name"] for b in bldgs]

    with st.form("reading_form"):
        col_a, col_b = st.columns(2)
        with col_a:
            r_date = st.date_input("Date", value=date.today())
            r_building = st.selectbox("Building", bldg_names)
        with col_b:
            r_usage = st.number_input("Usage (Liters)", min_value=1, step=100)
            r_notes = st.text_input("Notes (optional)", placeholder="e.g., Meter reading 1234")

        if st.form_submit_button("Save Reading"):
            resp = requests.post(f"{API_URL}/api/reading", json={
                "date": str(r_date),
                "building": r_building,
                "usage_liters": r_usage,
                "notes": r_notes
            }, timeout=5)
            result = resp.json()
            if result.get("success"):
                st.success(f"✅ Reading saved! Total records: {result['total_records']}")
            else:
                st.error(f"❌ {result}")

with tab4:
    st.subheader("🤖 Water Conservation Assistant")
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hi! I'm CampusWater AI. Ask me about water usage, conservation tips, government benchmarks, or how to upload your college's real data!"}
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
                ans = resp.get("answer", "Sorry, couldn't process that.")
                st.markdown(ans)
                if resp.get("sources"):
                    with st.expander("📚 Sources"):
                        for s in resp["sources"]:
                            st.write(f"- {s}")
                st.session_state.messages.append({"role": "assistant", "content": ans})
            except Exception as e:
                err = f"⚠️ Error: {e}"
                st.error(err)
                st.session_state.messages.append({"role": "assistant", "content": err})

with tab5:
    st.subheader("📋 Project: CampusWater AI v2")
    st.markdown(f"""
    **Student:** Vishwanath Sanapur  
    **College:** Government SKSJTI, KR Circle, Bengaluru  

    **SDG 6:** Clean Water and Sanitation  

    **What's legit about this version:**
    - 🌤 **Weather data:** Real historical Bengaluru data from Open-Meteo API (897 days)
    - 📋 **Benchmarks:** Government standards from CPHEEO, BIS, BWSSB, NITI Aayog
    - 🏢 **Buildings:** Actual SKSJTI campus buildings configured
    - 📥 **Data import:** Upload your college's real meter readings via CSV
    - ✏️ **Manual entry:** Add readings one by one
    - 🚨 **Anomaly detection:** Flags unusual patterns against rolling baselines
    - 🤖 **AI chatbot:** RAG-powered with Gemma3

    **How to make it fully real:**
    1. Get meter readings from your college's buildings
    2. Fill the CSV template (Download → Import tab)
    3. Upload — sample data gets replaced
    """)

st.divider()
st.caption("1M1B AI for Sustainability Internship | IBM SkillsBuild & AICTE | Open-Meteo Weather Data")
