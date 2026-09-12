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
# GLOBAL CSS — MODERN SAAS DASHBOARD THEME
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ---------- RESET ---------- */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {
        padding: 1.5rem 2rem 2rem 2rem;
        max-width: 100%;
    }
    .stApp { background: #f7f8fc; }

    /* ---------- SIDEBAR (DARK) ---------- */
    [data-testid="stSidebar"] {
        background: #1a1a2e;
        padding-top: 1rem;
        min-width: 260px !important;
        max-width: 260px !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        background: #1a1a2e;
        padding-top: 0.5rem;
    }
    [data-testid="stSidebar"] * {
        color: #cbd5e1 !important;
    }
    [data-testid="stSidebar"] .stRadio > label {
        display: none;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] {
        gap: 4px;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {
        background: transparent;
        padding: 10px 16px;
        border-radius: 10px;
        cursor: pointer;
        transition: all 0.2s;
        font-weight: 500;
        font-size: 0.9rem;
        width: 100%;
        border: none;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover {
        background: rgba(255,255,255,0.06) !important;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"],
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:has(input:checked) {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        box-shadow: 0 4px 12px rgba(99,102,241,0.35);
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:has(input:checked) * {
        color: #ffffff !important;
    }
    /* Hide radio dots */
    [data-testid="stSidebar"] .stRadio input[type="radio"] {
        display: none;
    }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label > div:first-child {
        display: none;
    }

    /* ---------- SIDEBAR BRAND ---------- */
    .brand {
        display: flex;
        align-items: center;
        gap: 0.7rem;
        padding: 0.5rem 1rem 1.5rem 1rem;
        border-bottom: 1px solid rgba(255,255,255,0.08);
        margin-bottom: 1rem;
    }
    .brand-logo {
        width: 38px; height: 38px;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        box-shadow: 0 4px 12px rgba(99,102,241,0.4);
    }
    .brand-name {
        font-weight: 700;
        font-size: 1.05rem;
        color: #ffffff !important;
        letter-spacing: -0.3px;
    }

    /* ---------- TOP BAR ---------- */
    .topbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.8rem;
        gap: 1rem;
        flex-wrap: wrap;
    }
    .search-box {
        flex: 1;
        max-width: 480px;
        display: flex;
        align-items: center;
        gap: 0.6rem;
        background: white;
        padding: 0.6rem 1rem;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .search-box input {
        border: none;
        outline: none;
        background: transparent;
        width: 100%;
        font-size: 0.9rem;
        color: #374151;
    }
    .search-icon { color: #9ca3af; }
    .user-chip {
        display: flex;
        align-items: center;
        gap: 0.7rem;
        background: white;
        padding: 0.45rem 0.9rem 0.45rem 0.5rem;
        border-radius: 50px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .avatar {
        width: 34px; height: 34px;
        border-radius: 50%;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .user-info { line-height: 1.1; }
    .user-name { font-size: 0.85rem; font-weight: 600; color: #111827; }
    .user-role { font-size: 0.7rem; color: #9ca3af; }

    /* ---------- PAGE HEADER ---------- */
    .page-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
        flex-wrap: wrap;
        gap: 0.8rem;
    }
    .page-title {
        font-size: 1.6rem;
        font-weight: 800;
        color: #111827;
        letter-spacing: -0.5px;
        margin: 0;
    }
    .page-sub {
        font-size: 0.85rem;
        color: #6b7280;
        margin-top: 0.2rem;
    }
    .pill-btn {
        background: white;
        border: 1px solid #e5e7eb;
        padding: 0.5rem 1rem;
        border-radius: 10px;
        font-size: 0.82rem;
        font-weight: 600;
        color: #374151;
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
    }

    /* ---------- KPI CARDS ---------- */
    .kpi-card {
        background: white;
        padding: 1.2rem 1.3rem;
        border-radius: 16px;
        border: 1px solid #eef0f4;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        transition: all 0.25s ease;
        height: 100%;
        position: relative;
    }
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 24px -10px rgba(99,102,241,0.2);
        border-color: #e0e7ff;
    }
    .kpi-icon {
        width: 42px; height: 42px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        margin-bottom: 0.9rem;
    }
    .kpi-icon.purple { background: #f3e8ff; }
    .kpi-icon.orange { background: #ffedd5; }
    .kpi-icon.blue   { background: #dbeafe; }
    .kpi-icon.green  { background: #d1fae5; }
    .kpi-icon.red    { background: #fee2e2; }

    .kpi-label {
        font-size: 0.78rem;
        color: #6b7280;
        font-weight: 500;
        margin-bottom: 0.3rem;
    }
    .kpi-value {
        font-size: 1.75rem;
        font-weight: 800;
        color: #111827;
        line-height: 1.1;
        letter-spacing: -0.5px;
    }
    .kpi-trend {
        font-size: 0.72rem;
        font-weight: 600;
        margin-top: 0.5rem;
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
    }
    .kpi-trend.up { color: #10b981; }
    .kpi-trend.down { color: #ef4444; }
    .kpi-trend.neutral { color: #6b7280; }

    /* ---------- SECTION CARDS ---------- */
    .section-card {
        background: white;
        border-radius: 16px;
        border: 1px solid #eef0f4;
        padding: 1.3rem 1.4rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.03);
        margin-bottom: 1.2rem;
    }
    .section-card-title {
        font-size: 1rem;
        font-weight: 700;
        color: #111827;
        margin: 0 0 1rem 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .section-card-title small {
        font-size: 0.75rem;
        color: #6b7280;
        font-weight: 500;
    }

    /* ---------- DATA TABLE ---------- */
    .data-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-size: 0.85rem;
    }
    .data-table thead th {
        text-align: left;
        padding: 0.75rem 0.9rem;
        font-size: 0.72rem;
        font-weight: 600;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        border-bottom: 1px solid #f1f3f7;
        background: #fafbfd;
    }
    .data-table thead th:first-child { border-radius: 10px 0 0 0; }
    .data-table thead th:last-child { border-radius: 0 10px 0 0; }
    .data-table tbody td {
        padding: 0.9rem 0.9rem;
        color: #374151;
        border-bottom: 1px solid #f5f6fa;
        vertical-align: middle;
    }
    .data-table tbody tr:hover td {
        background: #fafbff;
    }
    .data-table tbody tr:last-child td { border-bottom: none; }
    .data-table td.name-cell {
        font-weight: 600;
        color: #111827;
    }

    /* ---------- STATUS BADGES ---------- */
    .status {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        text-align: center;
        min-width: 82px;
    }
    .status-completed { background: #d1fae5; color: #065f46; }
    .status-pending   { background: #fef3c7; color: #92400e; }
    .status-progress  { background: #dbeafe; color: #1e40af; }
    .status-risk      { background: #fee2e2; color: #991b1b; }
    .status-delayed   { background: #fce7f3; color: #9d174d; }

    /* ---------- PROGRESS BAR ---------- */
    .progress-track {
        background: #f1f3f7;
        border-radius: 10px;
        height: 8px;
        overflow: hidden;
        width: 100%;
    }
    .progress-fill {
        height: 100%;
        border-radius: 10px;
        background: linear-gradient(90deg, #6366f1, #8b5cf6);
        transition: width 0.4s ease;
    }
    .progress-fill.green { background: linear-gradient(90deg, #10b981, #34d399); }
    .progress-fill.orange { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
    .progress-fill.red { background: linear-gradient(90deg, #ef4444, #f87171); }

    .progress-pct {
        font-size: 0.78rem;
        font-weight: 700;
        color: #111827;
        margin-top: 0.3rem;
        display: inline-block;
    }

    /* ---------- GAUGE ---------- */
    .gauge-container {
        text-align: center;
        padding: 0.5rem 0;
    }
    .gauge-value {
        font-size: 2.6rem;
        font-weight: 800;
        color: #111827;
        line-height: 1;
        letter-spacing: -1px;
    }
    .gauge-label {
        font-size: 0.78rem;
        color: #6b7280;
        margin-top: 0.3rem;
    }
    .gauge-stats {
        display: flex;
        justify-content: space-around;
        margin-top: 1.2rem;
        padding-top: 1rem;
        border-top: 1px solid #f1f3f7;
    }
    .gauge-stat-item { text-align: center; }
    .gauge-stat-value {
        font-size: 1.1rem;
        font-weight: 800;
        line-height: 1;
    }
    .gauge-stat-value.green { color: #10b981; }
    .gauge-stat-value.orange { color: #f59e0b; }
    .gauge-stat-value.red { color: #ef4444; }
    .gauge-stat-value.blue { color: #3b82f6; }
    .gauge-stat-label {
        font-size: 0.7rem;
        color: #9ca3af;
        margin-top: 0.3rem;
        font-weight: 500;
    }

    /* ---------- BUTTONS ---------- */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 0.5rem 1.1rem;
        transition: all 0.2s ease;
        border: 1px solid #e5e7eb;
        background: white;
        color: #374151;
    }
    .stButton > button:hover {
        border-color: #c7d2fe;
        color: #4f46e5;
        transform: translateY(-1px);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        border: none;
        color: white;
        box-shadow: 0 4px 12px -4px rgba(99,102,241,0.5);
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 8px 20px -6px rgba(99,102,241,0.6);
        color: white;
    }

    /* ---------- INPUTS ---------- */
    .stTextInput input, .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"] > div,
    .stNumberInput input {
        border-radius: 10px !important;
        border-color: #e5e7eb !important;
        font-size: 0.88rem !important;
        background: white !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.1) !important;
    }

    /* ---------- FILE UPLOADER ---------- */
    [data-testid="stFileUploader"] {
        border-radius: 14px;
        border: 2px dashed #c7d2fe;
        background: #f8faff;
        padding: 1rem;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #6366f1;
        background: #eef2ff;
    }

    /* ---------- EXPANDER ---------- */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 0.9rem;
        color: #374151;
        background: #fafbfd !important;
        border-radius: 10px !important;
    }

    /* ---------- METRIC (SIDEBAR) ---------- */
    [data-testid="stSidebar"] [data-testid="stMetric"] {
        background: rgba(255,255,255,0.04);
        padding: 0.7rem 0.9rem;
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.06);
        margin-bottom: 0.5rem;
    }
    [data-testid="stSidebar"] [data-testid="stMetricLabel"] * {
        color: #94a3b8 !important;
        font-size: 0.75rem !important;
    }
    [data-testid="stSidebar"] [data-testid="stMetricValue"] * {
        color: #ffffff !important;
        font-size: 1.3rem !important;
        font-weight: 700 !important;
    }

    /* ---------- TABS ---------- */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: white;
        padding: 5px;
        border-radius: 12px;
        border: 1px solid #eef0f4;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        margin-bottom: 1.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 38px;
        border-radius: 8px;
        padding: 0 16px;
        font-weight: 600;
        font-size: 0.85rem;
        color: #6b7280;
        background: transparent;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important;
    }
    .stTabs [data-baseweb="tab-highlight"] { background-color: transparent; }

    /* ---------- EMPTY STATE ---------- */
    .empty-state {
        text-align: center;
        padding: 3.5rem 1rem;
        color: #9ca3af;
    }
    .empty-state-icon {
        font-size: 3rem;
        margin-bottom: 0.7rem;
        opacity: 0.4;
    }

    /* ---------- RESPONSIVE ---------- */
    @media (max-width: 1024px) {
        .block-container { padding: 1rem !important; }
        .kpi-value { font-size: 1.4rem; }
        .page-title { font-size: 1.3rem; }
    }
    @media (max-width: 768px) {
        [data-testid="stSidebar"] {
            min-width: 240px !important;
            max-width: 240px !important;
        }
        .kpi-value { font-size: 1.25rem; }
        .gauge-value { font-size: 2rem; }
        .topbar { flex-direction: column; align-items: stretch; }
        .search-box { max-width: 100%; }
    }
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

STATUS_MAP = {
    "Pending": "status-pending",
    "Resolved": "status-completed",
}

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("""
    <div class="brand">
        <div class="brand-logo">🏙️</div>
        <div class="brand-name">Civic Reporter</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        ["📊  Dashboard", "📸  Report Issue", "📋  All Reports", "🛠️  Admin Panel"],
        label_visibility="collapsed"
    )

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div style="padding:0 1rem; font-size:0.7rem; text-transform:uppercase; letter-spacing:1px; color:#64748b; font-weight:600; margin-bottom:0.5rem;">Quick Stats</div>', unsafe_allow_html=True)

    stats = get_stats()
    st.metric("Total Reports", stats["total"])
    st.metric("Pending", stats["pending"])
    st.metric("Resolved", stats["resolved"])

# ============================================================
# TOP BAR
# ============================================================
top1, top2 = st.columns([3, 1])
with top1:
    st.markdown("""
    <div class="search-box">
        <span class="search-icon">🔍</span>
        <input placeholder="Search reports, locations, IDs..." />
    </div>
    """, unsafe_allow_html=True)
with top2:
    st.markdown("""
    <div style="display:flex; justify-content:flex-end;">
        <div class="user-chip">
            <div class="avatar">CR</div>
            <div class="user-info">
                <div class="user-name">Civic Admin</div>
                <div class="user-role">City Official</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================
# PAGE ROUTING
# ============================================================

# ==================== DASHBOARD ====================
if page == "📊  Dashboard":
    st.markdown("""
    <div class="page-header">
        <div>
            <h1 class="page-title">Overview</h1>
            <div class="page-sub">Live civic issue tracking & analytics</div>
        </div>
        <div class="pill-btn">📅 Last 30 days</div>
    </div>
    """, unsafe_allow_html=True)

    df = get_all_reports()

    # ----- KPI CARDS -----
    c1, c2, c3, c4 = st.columns(4)
    total = len(df) if not df.empty else 0
    pending = int((df["status"] == "Pending").sum()) if not df.empty else 0
    resolved = int((df["status"] == "Resolved").sum()) if not df.empty else 0
    high = int((df["priority"] == "High").sum()) if not df.empty else 0
    upvotes = int(df["upvotes"].sum()) if not df.empty else 0

    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon purple">📋</div>
            <div class="kpi-label">Total Reports</div>
            <div class="kpi-value">{total}</div>
            <div class="kpi-trend up">↗ Active civic engagement</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon orange">⏳</div>
            <div class="kpi-label">Pending</div>
            <div class="kpi-value">{pending}</div>
            <div class="kpi-trend down">↘ Awaiting action</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon green">✅</div>
            <div class="kpi-label">Resolved</div>
            <div class="kpi-value">{resolved}</div>
            <div class="kpi-trend up">↗ On track</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-icon red">🔥</div>
            <div class="kpi-label">High Priority</div>
            <div class="kpi-value">{high}</div>
            <div class="kpi-trend down">↗ Urgent attention</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ----- TABLE + GAUGE -----
    left, right = st.columns([2, 1])

    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-card-title">Recent Reports <small>Last 5 submissions</small></div>', unsafe_allow_html=True)

        if df.empty:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <p>No reports yet. Start by reporting an issue.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            recent = df.head(5)
            rows = ""
            for _, r in recent.iterrows():
                status_cls = STATUS_MAP.get(r["status"], "status-pending")
                priority_color = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#10b981"}.get(r["priority"], "#6b7280")
                rows += f"""
                <tr>
                    <td class="name-cell">{r['report_id']}</td>
                    <td>{r['issue_type']}</td>
                    <td>{r['location'][:28]}{'...' if len(r['location']) > 28 else ''}</td>
                    <td><span style="color:{priority_color}; font-weight:600;">{r['priority']}</span></td>
                    <td><span class="status {status_cls}">{r['status']}</span></td>
                </tr>
                """
            st.markdown(f"""
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Report ID</th>
                        <th>Issue Type</th>
                        <th>Location</th>
                        <th>Priority</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-card" style="height:100%;">', unsafe_allow_html=True)
        st.markdown('<div class="section-card-title">Resolution Rate</div>', unsafe_allow_html=True)

        pct = int((resolved / total * 100)) if total else 0
        # gauge color
        if pct >= 70:
            gauge_color = "#10b981"
            gauge_cls = "green"
        elif pct >= 40:
            gauge_color = "#f59e0b"
            gauge_cls = "orange"
        else:
            gauge_color = "#ef4444"
            gauge_cls = "red"

        st.markdown(f"""
        <div class="gauge-container">
            <svg viewBox="0 0 200 110" style="width:100%; max-width:220px;">
                <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#f1f3f7" stroke-width="16" stroke-linecap="round"/>
                <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="{gauge_color}" stroke-width="16" stroke-linecap="round"
                      stroke-dasharray="{pct * 2.51} 251" />
            </svg>
            <div class="gauge-value">{pct}%</div>
            <div class="gauge-label">Reports Resolved</div>
        </div>
        <div class="gauge-stats">
            <div class="gauge-stat-item">
                <div class="gauge-stat-value blue">{total}</div>
                <div class="gauge-stat-label">Total</div>
            </div>
            <div class="gauge-stat-item">
                <div class="gauge-stat-value green">{resolved}</div>
                <div class="gauge-stat-label">Resolved</div>
            </div>
            <div class="gauge-stat-item">
                <div class="gauge-stat-value orange">{pending}</div>
                <div class="gauge-stat-label">Pending</div>
            </div>
            <div class="gauge-stat-item">
                <div class="gauge-stat-value red">{high}</div>
                <div class="gauge-stat-label">High</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ----- CHART + TOP UPVOTES -----
    ch1, ch2 = st.columns([1, 1])
    with ch1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-card-title">Issues by Type</div>', unsafe_allow_html=True)
        if not df.empty:
            st.bar_chart(df["issue_type"].value_counts(), use_container_width=True, height=260)
        else:
            st.markdown('<div class="empty-state"><div class="empty-state-icon">📊</div><p>No data</p></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with ch2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-card-title">Top Upvoted Issues</div>', unsafe_allow_html=True)
        if not df.empty:
            top = df.nlargest(5, "upvotes")[["issue_type", "location", "upvotes"]]
            rows = ""
            for _, r in top.iterrows():
                rows += f"""
                <tr>
                    <td class="name-cell">{r['issue_type']}</td>
                    <td>{r['location'][:24]}{'...' if len(r['location']) > 24 else ''}</td>
                    <td><b style="color:#6366f1;">👍 {r['upvotes']}</b></td>
                </tr>
                """
            st.markdown(f"""
            <table class="data-table">
                <thead><tr><th>Issue</th><th>Location</th><th>Upvotes</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="empty-state"><div class="empty-state-icon">🏆</div><p>No data</p></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ----- MAP -----
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-card-title">Issue Heatmap</div>', unsafe_allow_html=True)
    if not df.empty:
        map_data = df[["latitude", "longitude"]].rename(columns={"latitude": "lat", "longitude": "lon"})
        st.map(map_data, zoom=10, use_container_width=True, height=400)
    else:
        st.markdown('<div class="empty-state"><div class="empty-state-icon">🗺️</div><p>No location data</p></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== REPORT ISSUE ====================
elif page == "📸  Report Issue":
    st.markdown("""
    <div class="page-header">
        <div>
            <h1 class="page-title">Report an Issue</h1>
            <div class="page-sub">Upload a photo — AI will classify and route it automatically</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-card-title">📸 Upload Photo</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Drag & drop or click to browse",
            type=["jpg", "jpeg", "png"],
            label_visibility="collapsed"
        )

        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, use_container_width=True)

            with st.spinner("🤖 AI analyzing image..."):
                ai_type, confidence, all_scores = classify_image(image)
                severity = estimate_severity(image, ai_type)

            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #eef2ff, #f5f3ff); border:1px solid #c7d2fe; padding:1rem 1.2rem; border-radius:12px; margin-top:0.8rem;">
                <div style="font-size:0.7rem; text-transform:uppercase; letter-spacing:0.8px; color:#6366f1; font-weight:700;">🎯 AI Detection</div>
                <div style="font-size:1.2rem; font-weight:700; color:#1e1b4b; margin-top:0.2rem;">{DEPARTMENTS[ai_type]['icon']} {ai_type}</div>
                <div style="font-size:0.82rem; color:#6366f1; margin-top:0.3rem;">
                    Confidence: <b>{confidence*100:.1f}%</b> &nbsp;•&nbsp; Severity: <b>{severity}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("🔍 View all AI scores"):
                for k, v in sorted(all_scores.items(), key=lambda x: -x[1]):
                    st.markdown(f"**{k}** — `{v*100:.1f}%`")
                    st.progress(v)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-card-title">📍 Location Details</div>', unsafe_allow_html=True)

        location = st.text_input("Address / Landmark", placeholder="e.g., MG Road, near City Mall")
        c1, c2 = st.columns(2)
        with c1:
            latitude = st.number_input("Latitude", value=28.6139, format="%.6f")
        with c2:
            longitude = st.number_input("Longitude", value=77.2090, format="%.6f")

        st.markdown('<div style="margin-top:1rem; font-size:0.85rem; font-weight:600; color:#374151; margin-bottom:0.5rem;">🏷️ Issue Type</div>', unsafe_allow_html=True)

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
        <div style="background:#ecfdf5; border:1px solid #a7f3d0; padding:0.8rem 1rem; border-radius:10px; margin-top:0.8rem; display:flex; align-items:center; gap:0.7rem;">
            <div style="font-size:1.4rem;">{info['icon']}</div>
            <div>
                <div style="font-size:0.7rem; color:#047857; font-weight:600; text-transform:uppercase; letter-spacing:0.5px;">Auto-routed to</div>
                <div style="font-size:0.9rem; font-weight:700; color:#064e3b;">{info['dept']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
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
                    "reporter": "Anonymous"
                }
                add_report(report)
                st.success(f"✅ Report submitted!  **ID: {report_id}**")
                st.balloons()
                st.info(f"📨 Auto-routed to **{DEPARTMENTS[issue_type]['dept']}**")
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== ALL REPORTS ====================
elif page == "📋  All Reports":
    st.markdown("""
    <div class="page-header">
        <div>
            <h1 class="page-title">All Reports</h1>
            <div class="page-sub">Browse, filter and manage all civic issues</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    df = get_all_reports()

    if df.empty:
        st.markdown("""
        <div class="section-card">
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <h3 style="color:#374151;">No reports yet</h3>
                <p>Go to "Report Issue" and submit the first one.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
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
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        rows = ""
        for _, r in filtered.iterrows():
            status_cls = STATUS_MAP.get(r["status"], "status-pending")
            priority_color = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#10b981"}.get(r["priority"], "#6b7280")
            icon = DEPARTMENTS.get(r["issue_type"], {}).get("icon", "📌")
            rows += f"""
            <tr>
                <td class="name-cell">{r['report_id']}</td>
                <td>{icon} {r['issue_type']}</td>
                <td>{r['location'][:32]}{'...' if len(r['location']) > 32 else ''}</td>
                <td>{r['department']}</td>
                <td><span style="color:{priority_color}; font-weight:600;">{r['priority']}</span></td>
                <td><span class="status {status_cls}">{r['status']}</span></td>
                <td><b style="color:#6366f1;">👍 {r['upvotes']}</b></td>
            </tr>
            """
        st.markdown(f"""
        <table class="data-table">
            <thead>
                <tr>
                    <th>Report ID</th>
                    <th>Type</th>
                    <th>Location</th>
                    <th>Department</th>
                    <th>Priority</th>
                    <th>Status</th>
                    <th>Upvotes</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Upvote buttons
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-card-title">👍 Upvote a Report</div>', unsafe_allow_html=True)
        uv_cols = st.columns(3)
        report_ids = filtered["report_id"].tolist()[:6]
        for i, rid in enumerate(report_ids):
            with uv_cols[i % 3]:
                if st.button(f"👍 Upvote {rid}", key=f"uv_{rid}", use_container_width=True):
                    upvote(rid)
                    st.success(f"Upvoted {rid}")
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️  Download CSV", csv, "civic_reports.csv", "text/csv")

# ==================== ADMIN ====================
elif page == "🛠️  Admin Panel":
    st.markdown("""
    <div class="page-header">
        <div>
            <h1 class="page-title">Admin Panel</h1>
            <div class="page-sub">For city officials — update report statuses</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    df = get_all_reports()
    pending = df[df["status"] == "Pending"] if not df.empty else pd.DataFrame()

    if pending.empty:
        st.markdown("""
        <div class="section-card">
            <div class="empty-state">
                <div class="empty-state-icon">🎉</div>
                <h3 style="color:#10b981;">All caught up!</h3>
                <p>No pending reports awaiting action.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info(f"**{len(pending)}** pending reports awaiting action.")

        for _, r in pending.iterrows():
            priority_emoji = {"High": "🔴", "Medium": "🟠", "Low": "🟢"}.get(r["priority"], "⚪")
            with st.expander(f"{priority_emoji}  {r['report_id']}  —  {r['issue_type']}  @  {r['location']}"):
                cc1, cc2 = st.columns([3, 1])
                with cc1:
                    st.markdown(f"**Department:** {r['department']}")
                    st.markdown(f"**Priority:** {r['priority']}")
                    st.markdown(f"**Description:** {r['description']}")
                    st.markdown(f"**Reported on:** {r['date']}")
                    st.markdown(f"**Reporter:** {r.get('reporter', 'Anonymous')}")
                with cc2:
                    if st.button("✅  Mark Resolved", key=f"res_{r['report_id']}", use_container_width=True, type="primary"):
                        update_status(r["report_id"], "Resolved")
                        st.success(f"Resolved {r['report_id']}")
                        st.rerun()

# ============================================================
# FOOTER
# ============================================================
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center; color:#9ca3af; font-size:0.78rem; padding:1rem 0;">
    Civic Issue Reporter &nbsp;•&nbsp; Built with Streamlit, CLIP AI & SQLite
</div>
""", unsafe_allow_html=True)
