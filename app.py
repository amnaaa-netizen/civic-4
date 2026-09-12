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

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Civic Issue Reporter",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)
init_db()

# ============================================================
# GLOBAL CSS - PROFESSIONAL THEME
# ============================================================
st.markdown("""
<style>
    /* ---------- FONTS ---------- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ---------- HIDE STREAMLIT DEFAULTS ---------- */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 2rem; padding-bottom: 2rem; max-width: 1400px;}

    /* ---------- BACKGROUND ---------- */
    .stApp {
        background: linear-gradient(180deg, #f8fafc 0%, #eef2f7 100%);
    }

    /* ---------- HERO ---------- */
    .hero {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #6366f1 100%);
        padding: 2.5rem 2rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px -20px rgba(79, 70, 229, 0.4);
        position: relative;
        overflow: hidden;
    }
    .hero::before {
        content: "";
        position: absolute;
        top: -50%; right: -20%;
        width: 400px; height: 400px;
        background: radial-gradient(circle, rgba(255,255,255,0.15), transparent 70%);
        border-radius: 50%;
    }
    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        opacity: 0.92;
        margin-top: 0.5rem;
        font-weight: 400;
    }
    .hero-badge {
        display: inline-block;
        background: rgba(255,255,255,0.2);
        backdrop-filter: blur(10px);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 1rem;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    /* ---------- STAT CARDS ---------- */
    .stat-card {
        background: white;
        padding: 1.25rem 1.5rem;
        border-radius: 14px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        transition: all 0.2s ease;
        height: 100%;
    }
    .stat-card:hover {
        box-shadow: 0 8px 20px -8px rgba(79, 70, 229, 0.25);
        transform: translateY(-2px);
        border-color: #c7d2fe;
    }
    .stat-label {
        font-size: 0.75rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        font-weight: 600;
        margin-bottom: 0.4rem;
    }
    .stat-value {
        font-size: 1.9rem;
        font-weight: 800;
        color: #111827;
        line-height: 1;
    }
    .stat-value.pending { color: #f59e0b; }
    .stat-value.resolved { color: #10b981; }
    .stat-value.high { color: #ef4444; }
    .stat-icon {
        font-size: 1.4rem;
        margin-bottom: 0.3rem;
    }

    /* ---------- SECTION HEADINGS ---------- */
    .section-heading {
        font-size: 1.15rem;
        font-weight: 700;
        color: #111827;
        margin: 0.5rem 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #f3f4f6;
    }

    /* ---------- REPORT CARDS ---------- */
    .report-card {
        background: white;
        padding: 1.1rem 1.3rem;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        margin-bottom: 0.75rem;
        border-left: 4px solid #6366f1;
        transition: all 0.2s ease;
    }
    .report-card:hover {
        box-shadow: 0 6px 16px -6px rgba(0,0,0,0.1);
        border-color: #d1d5db;
    }
    .report-card.priority-High { border-left-color: #ef4444; }
    .report-card.priority-Medium { border-left-color: #f59e0b; }
    .report-card.priority-Low { border-left-color: #10b981; }

    .report-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.5rem;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    .report-id {
        font-weight: 700;
        color: #4f46e5;
        font-size: 0.85rem;
        letter-spacing: 0.3px;
    }
    .report-type {
        font-weight: 600;
        color: #111827;
        font-size: 1rem;
        margin: 0.2rem 0;
    }
    .report-meta {
        font-size: 0.82rem;
        color: #6b7280;
        margin-top: 0.3rem;
    }

    /* ---------- BADGES ---------- */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.4px;
        text-transform: uppercase;
    }
    .badge-pending { background: #fef3c7; color: #92400e; }
    .badge-resolved { background: #d1fae5; color: #065f46; }
    .badge-high { background: #fee2e2; color: #991b1b; }
    .badge-medium { background: #fef3c7; color: #92400e; }
    .badge-low { background: #dbeafe; color: #1e40af; }

    /* ---------- BUTTONS ---------- */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.9rem;
        padding: 0.55rem 1.2rem;
        transition: all 0.2s ease;
        border: 1px solid #e5e7eb;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        border: none;
        color: white;
        box-shadow: 0 4px 12px -4px rgba(79, 70, 229, 0.5);
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 8px 20px -6px rgba(79, 70, 229, 0.6);
        transform: translateY(-1px);
    }
    .stButton > button:hover {
        border-color: #c7d2fe;
        color: #4f46e5;
    }

    /* ---------- TABS ---------- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: white;
        padding: 6px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 8px;
        padding: 0 18px;
        font-weight: 600;
        font-size: 0.9rem;
        color: #6b7280;
        background: transparent;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
        color: white !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: transparent;
    }

    /* ---------- INPUTS ---------- */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
        border-radius: 10px !important;
        border-color: #e5e7eb !important;
        font-size: 0.9rem;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
    }

    /* ---------- FILE UPLOADER ---------- */
    [data-testid="stFileUploader"] {
        border-radius: 12px;
        border: 2px dashed #c7d2fe;
        background: #f5f3ff;
        padding: 1rem;
    }

    /* ---------- SIDEBAR ---------- */
    [data-testid="stSidebar"] {
        background: white;
        border-right: 1px solid #e5e7eb;
    }
    [data-testid="stSidebar"] .stMetric {
        background: #f9fafb;
        padding: 0.8rem 1rem;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
    }

    /* ---------- EXPANDER ---------- */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 0.9rem;
        color: #374151;
    }

    /* ---------- AI RESULT CARD ---------- */
    .ai-card {
        background: linear-gradient(135deg, #eef2ff, #f5f3ff);
        border: 1px solid #c7d2fe;
        padding: 1rem 1.2rem;
        border-radius: 12px;
        margin-top: 1rem;
    }
    .ai-card-title {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: #6366f1;
        font-weight: 700;
        margin-bottom: 0.3rem;
    }
    .ai-card-value {
        font-size: 1.2rem;
        font-weight: 700;
        color: #1e1b4b;
    }

    /* ---------- ROUTING CARD ---------- */
    .routing-card {
        background: #ecfdf5;
        border: 1px solid #a7f3d0;
        padding: 0.9rem 1.1rem;
        border-radius: 10px;
        display: flex;
        align-items: center;
        gap: 0.7rem;
        margin-top: 0.8rem;
    }
    .routing-icon { font-size: 1.5rem; }
    .routing-label { font-size: 0.75rem; color: #047857; font-weight: 600; text-transform: uppercase; }
    .routing-value { font-size: 0.95rem; font-weight: 700; color: #064e3b; }

    /* ---------- EMPTY STATE ---------- */
    .empty-state {
        text-align: center;
        padding: 3rem 1rem;
        color: #9ca3af;
    }
    .empty-state-icon { font-size: 3rem; margin-bottom: 0.5rem; opacity: 0.5; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# CONSTANTS
# ============================================================
DEPARTMENTS = {
    "Pothole": {"dept": "Roads & Public Works", "icon": "🛣️"},
    "Broken Streetlight": {"dept": "Electricity Department", "icon": "💡"},
    "Garbage Dump": {"dept": "Sanitation Department", "icon": "🗑️"},
    "Water Leak": {"dept": "Water Supply Board", "icon": "💧"},
    "Other": {"dept": "General Complaint Cell", "icon": "📋"}
}

# ============================================================
# HERO HEADER
# ============================================================
st.markdown("""
<div class="hero">
    <div class="hero-title">🏙️ Civic Issue Reporter</div>
    <div class="hero-subtitle">Snap a photo. AI classifies it. Auto-routed to the right department.</div>
    <span class="hero-badge">⚡ AI-Powered Civic Tech</span>
</div>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("### 📊 Live Metrics")
    stats = get_stats()
    st.metric("Total Reports", stats["total"])
    st.metric("Pending", stats["pending"])
    st.metric("Resolved", stats["resolved"])
    st.metric("High Priority", stats["high"])

    st.divider()
    st.markdown("### 👤 Reporter")
    reporter_name = st.text_input("Your name (optional)", value="Anonymous", label_visibility="collapsed", placeholder="Your name...")

    st.divider()
    st.caption("💡 **Tip:** Upload a clear photo for best AI accuracy.")
    st.caption("Civic Issue Reporter v2.0")

# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📸  Report Issue", "📊  Dashboard", "📋  All Reports", "🛠️  Admin"
])

# ============================================================
# TAB 1: REPORT
# ============================================================
with tab1:
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown('<div class="section-heading">📸 Upload Photo</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Drag & drop or click to browse",
            type=["jpg", "jpeg", "png"],
            label_visibility="collapsed"
        )

        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="", use_container_width=True)

            with st.spinner("🤖 AI analyzing image..."):
                ai_type, confidence, all_scores = classify_image(image)
                severity = estimate_severity(image, ai_type)

            st.markdown(f"""
            <div class="ai-card">
                <div class="ai-card-title">🎯 AI Detection</div>
                <div class="ai-card-value">{DEPARTMENTS[ai_type]['icon']} {ai_type}</div>
                <div style="font-size:0.85rem; color:#6366f1; margin-top:0.2rem;">
                    Confidence: <b>{confidence*100:.1f}%</b> &nbsp;•&nbsp; 
                    Severity: <b>{severity}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("🔍 View all AI scores"):
                for k, v in sorted(all_scores.items(), key=lambda x: -x[1]):
                    st.markdown(f"**{k}** — `{v*100:.1f}%`")
                    st.progress(v)

    with col2:
        st.markdown('<div class="section-heading">📍 Location Details</div>', unsafe_allow_html=True)
        location = st.text_input("Address / Landmark", placeholder="e.g., MG Road, near City Mall")

        c1, c2 = st.columns(2)
        with c1:
            latitude = st.number_input("Latitude", value=28.6139, format="%.6f")
        with c2:
            longitude = st.number_input("Longitude", value=77.2090, format="%.6f")

        st.markdown('<div class="section-heading" style="margin-top:1rem;">🏷️ Issue Type</div>', unsafe_allow_html=True)

        if uploaded_file:
            issue_type = st.selectbox(
                "Confirm or change",
                list(DEPARTMENTS.keys()),
                index=list(DEPARTMENTS.keys()).index(ai_type),
                label_visibility="collapsed"
            )
        else:
            issue_type = st.selectbox(
                "Select issue type",
                list(DEPARTMENTS.keys()),
                label_visibility="collapsed"
            )

        info = DEPARTMENTS[issue_type]
        st.markdown(f"""
        <div class="routing-card">
            <div class="routing-icon">{info['icon']}</div>
            <div>
                <div class="routing-label">Auto-routed to</div>
                <div class="routing-value">{info['dept']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    description = st.text_area(
        "📝 Additional description (optional)",
        placeholder="Describe the issue — size, duration, safety concern...",
        height=90
    )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀  Submit Report", type="primary", use_container_width=True):
        if not uploaded_file:
            st.error("❌ Please upload a photo of the issue.")
        elif not location.strip():
            st.error("❌ Please enter the location.")
        else:
            dup = find_duplicate(latitude, longitude, issue_type)
            if dup:
                st.warning(f"⚠️ Similar issue already reported nearby: **{dup}**")
                upvote(dup)
                st.info(f"👍 Your upvote was added to **{dup}** instead.")
            else:
                report_id = "CIR-" + hashlib.md5(
                    f"{location}{datetime.now()}".encode()
                ).hexdigest()[:6].upper()

                report = {
                    "report_id": report_id,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "issue_type": issue_type,
                    "department": DEPARTMENTS[issue_type]["dept"],
                    "priority": severity if uploaded_file else "Medium",
                    "severity": severity if uploaded_file else "Medium",
                    "location": location,
                    "latitude": latitude,
                    "longitude": longitude,
                    "description": description or "-",
                    "reporter": reporter_name
                }
                add_report(report)
                st.success(f"✅ Report submitted successfully!  **ID: {report_id}**")
                st.balloons()
                st.info(f"📨 Auto-routed to **{DEPARTMENTS[issue_type]['dept']}**")

# ============================================================
# TAB 2: DASHBOARD
# ============================================================
with tab2:
    df = get_all_reports()

    if df.empty:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📭</div>
            <h3>No reports yet</h3>
            <p>Head to the "Report Issue" tab to submit the first one.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # ---- STAT CARDS ----
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-icon">📋</div>
                <div class="stat-label">Total Reports</div>
                <div class="stat-value">{len(df)}</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-icon">⏳</div>
                <div class="stat-label">Pending</div>
                <div class="stat-value pending">{(df['status']=='Pending').sum()}</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-icon">✅</div>
                <div class="stat-label">Resolved</div>
                <div class="stat-value resolved">{(df['status']=='Resolved').sum()}</div>
            </div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-icon">🔥</div>
                <div class="stat-label">High Priority</div>
                <div class="stat-value high">{(df['priority']=='High').sum()}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ---- CHARTS ----
        cc1, cc2 = st.columns(2, gap="large")
        with cc1:
            st.markdown('<div class="section-heading">📈 Issues by Type</div>', unsafe_allow_html=True)
            st.bar_chart(df["issue_type"].value_counts(), use_container_width=True, height=280)
        with cc2:
            st.markdown('<div class="section-heading">🏢 Issues by Department</div>', unsafe_allow_html=True)
            st.bar_chart(df["department"].value_counts(), use_container_width=True, height=280)

        st.markdown("<br>", unsafe_allow_html=True)

        # ---- TOP UPVOTED ----
        st.markdown('<div class="section-heading">🔥 Top Upvoted Issues</div>', unsafe_allow_html=True)
        top = df.nlargest(5, "upvotes")[["report_id", "issue_type", "location", "upvotes", "status"]]
        st.dataframe(
            top,
            use_container_width=True,
            hide_index=True,
            column_config={
                "report_id": "Report ID",
                "issue_type": "Type",
                "location": "Location",
                "upvotes": st.column_config.NumberColumn("👍 Upvotes", format="%d"),
                "status": "Status"
            }
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # ---- MAP ----
        st.markdown('<div class="section-heading">🗺️ Issue Heatmap</div>', unsafe_allow_html=True)
        map_data = df[["latitude", "longitude"]].rename(
            columns={"latitude": "lat", "longitude": "lon"}
        )
        st.map(map_data, zoom=10, use_container_width=True)

# ============================================================
# TAB 3: ALL REPORTS
# ============================================================
with tab3:
    df = get_all_reports()

    if df.empty:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📭</div>
            <h3>No reports yet</h3>
        </div>
        """, unsafe_allow_html=True)
    else:
        # ---- FILTERS ----
        f1, f2, f3 = st.columns([1, 1, 2])
        with f1:
            status_filter = st.selectbox("Status", ["All", "Pending", "Resolved"])
        with f2:
            type_filter = st.selectbox("Issue Type", ["All"] + list(DEPARTMENTS.keys()))
        with f3:
            search = st.text_input("🔍 Search location", placeholder="Type to filter...")

        filtered = df.copy()
        if status_filter != "All":
            filtered = filtered[filtered["status"] == status_filter]
        if type_filter != "All":
            filtered = filtered[filtered["issue_type"] == type_filter]
        if search.strip():
            filtered = filtered[filtered["location"].str.contains(search, case=False, na=False)]

        st.caption(f"Showing **{len(filtered)}** of **{len(df)}** reports")

        st.markdown("<br>", unsafe_allow_html=True)

        # ---- REPORT LIST ----
        for _, row in filtered.iterrows():
            status_cls = "badge-resolved" if row["status"] == "Resolved" else "badge-pending"
            priority_cls = f"badge-{row['priority'].lower()}"

            st.markdown(f"""
            <div class="report-card priority-{row['priority']}">
                <div class="report-header">
                    <span class="report-id">🆔 {row['report_id']}</span>
                    <div>
                        <span class="badge {priority_cls}">{row['priority']}</span>
                        <span class="badge {status_cls}">{row['status']}</span>
                    </div>
                </div>
                <div class="report-type">{DEPARTMENTS.get(row['issue_type'], {}).get('icon','📌')} {row['issue_type']}</div>
                <div class="report-meta">
                    📍 {row['location']} &nbsp;•&nbsp; 
                    🏢 {row['department']} &nbsp;•&nbsp; 
                    📅 {row['date']} &nbsp;•&nbsp; 
                    👍 {row['upvotes']} upvotes
                </div>
            </div>
            """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns([1, 1, 6])
            with c1:
                if st.button("👍 Upvote", key=f"up_{row['report_id']}", use_container_width=True):
                    upvote(row["report_id"])
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()

        # ---- EXPORT ----
        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️  Download CSV",
            csv,
            "civic_reports.csv",
            "text/csv",
            use_container_width=False
        )

# ============================================================
# TAB 4: ADMIN
# ============================================================
with tab4:
    st.markdown('<div class="section-heading">🛠️ Admin Panel</div>', unsafe_allow_html=True)
    st.caption("For city officials — update report statuses here.")

    df = get_all_reports()
    pending = df[df["status"] == "Pending"] if not df.empty else pd.DataFrame()

    if pending.empty:
        st.success("🎉 All reports are resolved. Great work!")
    else:
        st.info(f"**{len(pending)}** pending reports awaiting action.")

        for _, row in pending.iterrows():
            priority_emoji = {"High": "🔴", "Medium": "🟠", "Low": "🟢"}.get(row["priority"], "⚪")
            with st.expander(f"{priority_emoji}  {row['report_id']}  —  {row['issue_type']}  @  {row['location']}"):
                cc1, cc2 = st.columns([2, 1])
                with cc1:
                    st.markdown(f"**Department:** {row['department']}")
                    st.markdown(f"**Priority:** {row['priority']}")
                    st.markdown(f"**Description:** {row['description']}")
                    st.markdown(f"**Reported on:** {row['date']}")
                    st.markdown(f"**Reporter:** {row['reporter']}")
                with cc2:
                    if st.button("✅  Mark Resolved", key=f"res_{row['report_id']}", use_container_width=True, type="primary"):
                        update_status(row["report_id"], "Resolved")
                        st.success(f"Resolved {row['report_id']}")
                        st.rerun()

# ============================================================
# FOOTER
# ============================================================
st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; color:#9ca3af; font-size:0.8rem; padding:1rem 0;">
    Civic Issue Reporter v2.0 &nbsp;•&nbsp; Built with Streamlit, CLIP AI & SQLite
</div>
""", unsafe_allow_html=True)
