import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import hashlib

from database import (
    init_db, add_report, get_all_reports,
    update_status, upvote, find_duplicate, get_stats
)
from ai_classifier import classify_image, estimate_severity

# ---------- INIT ----------
st.set_page_config(
    page_title="Civic Issue Reporter Pro",
    page_icon="🏙️",
    layout="wide"
)
init_db()

# ---------- STYLING ----------
st.markdown("""
<style>
    .main-title {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(90deg, #1f77b4, #4CAF50);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }
    .sub-title {
        text-align: center; color: #666;
        margin-bottom: 1.5rem; font-size: 1.1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem; border-radius: 12px; color: white;
        text-align: center;
    }
    .report-card {
        background: #f8f9fa; padding: 1rem;
        border-radius: 10px; margin-bottom: 0.7rem;
        border-left: 5px solid #1f77b4;
    }
    .priority-High { border-left-color: #e74c3c !important; }
    .priority-Medium { border-left-color: #f39c12 !important; }
    .priority-Low { border-left-color: #27ae60 !important; }
    .stButton>button { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🏙️ Civic Issue Reporter Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">AI-powered snap → auto-route to correct department</div>', unsafe_allow_html=True)

# ---------- DEPARTMENT MAP ----------
DEPARTMENTS = {
    "Pothole": {"dept": "Roads & Public Works", "icon": "🛣️"},
    "Broken Streetlight": {"dept": "Electricity Department", "icon": "💡"},
    "Garbage Dump": {"dept": "Sanitation Department", "icon": "🗑️"},
    "Water Leak": {"dept": "Water Supply Board", "icon": "💧"},
    "Other": {"dept": "General Complaint Cell", "icon": "📋"}
}

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("📊 Live Stats")
    stats = get_stats()
    st.metric("Total Reports", stats["total"])
    st.metric("Pending", stats["pending"])
    st.metric("Resolved", stats["resolved"])
    st.metric("High Priority", stats["high"])

    st.divider()
    st.subheader("👤 Reporter")
    reporter_name = st.text_input("Your name (optional)", value="Anonymous")

    st.divider()
    st.caption("Built with ❤️ using Streamlit + CLIP AI")

# ---------- TABS ----------
tab1, tab2, tab3, tab4 = st.tabs([
    "📸 Report Issue", "📊 Dashboard", "📋 All Reports", "🛠️ Admin"
])

# ================= TAB 1: REPORT =================
with tab1:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("1️⃣ Upload Photo")
        uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])

        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded", use_container_width=True)

            with st.spinner("🤖 AI analyzing image..."):
                ai_type, confidence, all_scores = classify_image(image)
                severity = estimate_severity(image, ai_type)

            st.success(f"🎯 **AI Detected:** {ai_type} ({confidence*100:.1f}% confidence)")
            st.info(f"⚡ **Severity:** {severity}")

            with st.expander("🔍 See all AI scores"):
                for k, v in sorted(all_scores.items(), key=lambda x: -x[1]):
                    st.write(f"- **{k}**: {v*100:.1f}%")

    with col2:
        st.subheader("2️⃣ Location")
        location = st.text_input("📍 Address / Landmark", placeholder="e.g., MG Road, Delhi")
        c1, c2 = st.columns(2)
        with c1:
            latitude = st.number_input("Latitude", value=28.6139, format="%.6f")
        with c2:
            longitude = st.number_input("Longitude", value=77.2090, format="%.6f")

        st.subheader("3️⃣ Confirm Issue Type")
        if uploaded_file:
            issue_type = st.selectbox(
                "AI suggested — change if wrong",
                list(DEPARTMENTS.keys()),
                index=list(DEPARTMENTS.keys()).index(ai_type)
            )
        else:
            issue_type = st.selectbox("Issue Type", list(DEPARTMENTS.keys()))

        info = DEPARTMENTS[issue_type]
        st.info(f"{info['icon']} **Routed to:** {info['dept']}")

    description = st.text_area("📝 Description (optional)")

    if st.button("🚀 Submit Report", type="primary", use_container_width=True):
        if not uploaded_file:
            st.error("❌ Please upload a photo.")
        elif not location.strip():
            st.error("❌ Please enter location.")
        else:
            # Duplicate check
            dup = find_duplicate(latitude, longitude, issue_type)
            if dup:
                st.warning(f"⚠️ Similar issue already reported nearby: **{dup}**. Upvoting it instead!")
                upvote(dup)
                st.info(f"✅ Upvoted report **{dup}**")
            else:
                report_id = "CIR-" + hashlib.md5(
                    f"{location}{datetime.now()}".encode()
                ).hexdigest()[:6].upper()

                report = {
                    "report_id": report_id,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "issue_type": issue_type,
                    "department": DEPARTMENTS[issue_type]["dept"],
                    "priority": severity if 'severity' in dir() else "Medium",
                    "severity": severity if uploaded_file else "Medium",
                    "location": location,
                    "latitude": latitude,
                    "longitude": longitude,
                    "description": description or "-",
                    "reporter": reporter_name
                }
                add_report(report)
                st.success(f"✅ Report submitted! ID: **{report_id}**")
                st.balloons()
                st.info(f"📨 Auto-routed to **{DEPARTMENTS[issue_type]['dept']}**")

# ================= TAB 2: DASHBOARD =================
with tab2:
    st.subheader("📊 Live Dashboard")
    df = get_all_reports()

    if df.empty:
        st.info("No reports yet.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", len(df))
        c2.metric("Pending", (df["status"] == "Pending").sum())
        c3.metric("Resolved", (df["status"] == "Resolved").sum())
        c4.metric("High Priority", (df["priority"] == "High").sum())

        st.divider()
        cc1, cc2 = st.columns(2)
        with cc1:
            st.write("**Issues by Type**")
            st.bar_chart(df["issue_type"].value_counts())
        with cc2:
            st.write("**Issues by Department**")
            st.bar_chart(df["department"].value_counts())

        st.divider()
        st.write("**🔥 Top Upvoted Issues**")
        top = df.nlargest(5, "upvotes")[["report_id", "issue_type", "location", "upvotes", "status"]]
        st.dataframe(top, use_container_width=True, hide_index=True)

        st.divider()
        st.write("**🗺️ Issue Map**")
        map_data = df[["latitude", "longitude"]].rename(columns={"latitude": "lat", "longitude": "lon"})
        st.map(map_data, zoom=10)

# ================= TAB 3: ALL REPORTS =================
with tab3:
    st.subheader("📋 All Reports")
    df = get_all_reports()

    if df.empty:
        st.info("No reports yet.")
    else:
        f1, f2 = st.columns(2)
        with f1:
            status_filter = st.selectbox("Status", ["All", "Pending", "Resolved"])
        with f2:
            type_filter = st.selectbox("Issue Type", ["All"] + list(DEPARTMENTS.keys()))

        filtered = df.copy()
        if status_filter != "All":
            filtered = filtered[filtered["status"] == status_filter]
        if type_filter != "All":
            filtered = filtered[filtered["issue_type"] == type_filter]

        for _, row in filtered.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="report-card priority-{row['priority']}">
                    <b>🆔 {row['report_id']}</b> &nbsp;|&nbsp; 
                    <b>{row['issue_type']}</b> &nbsp;|&nbsp;
                    Priority: <b>{row['priority']}</b> &nbsp;|&nbsp;
                    Status: <b>{row['status']}</b><br>
                    📍 {row['location']}<br>
                    🏢 {row['department']} &nbsp;|&nbsp; 
                    📅 {row['date']} &nbsp;|&nbsp; 
                    👍 {row['upvotes']} upvotes
                </div>
                """, unsafe_allow_html=True)

                c1, c2 = st.columns([1, 5])
                with c1:
                    if st.button(f"👍 Upvote", key=f"up_{row['report_id']}"):
                        upvote(row["report_id"])
                        st.rerun()

        st.divider()
        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, "civic_reports.csv", "text/csv")

# ================= TAB 4: ADMIN =================
with tab4:
    st.subheader("🛠️ Admin Panel")
    st.caption("For city officials — update report statuses")

    df = get_all_reports()
    pending = df[df["status"] == "Pending"] if not df.empty else pd.DataFrame()

    if pending.empty:
        st.success("🎉 No pending reports!")
    else:
        for _, row in pending.iterrows():
            with st.expander(f"🆔 {row['report_id']} — {row['issue_type']} @ {row['location']}"):
                st.write(f"**Department:** {row['department']}")
                st.write(f"**Priority:** {row['priority']}")
                st.write(f"**Description:** {row['description']}")
                st.write(f"**Reported on:** {row['date']}")
                if st.button(f"✅ Mark Resolved", key=f"res_{row['report_id']}"):
                    update_status(row["report_id"], "Resolved")
                    st.success(f"Resolved {row['report_id']}")
                    st.rerun()

# ---------- FOOTER ----------
st.divider()
st.caption("Civic Issue Reporter Pro v2.0 | AI-powered civic tech 🚀")
