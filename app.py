import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
if not os.getenv("GROQ_API_KEY"):
    try:
        cloud_key = st.secrets.get("GROQ_API_KEY", "")
        if cloud_key:
            os.environ["GROQ_API_KEY"] = cloud_key
    except Exception:
        pass

from utils.database import (
    STATUS_OPTIONS,
    create_complaint,
    get_complaint,
    get_complaints,
    update_status,
)
from utils.rag import route_issue
from utils.vision import classify_image

st.set_page_config(page_title="Civic Issue Reporter", page_icon="🏙️", layout="wide")

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

st.markdown(
    """
    <style>
    .main { background: #f7f9fc; }
    [data-testid="stMetricValue"] { color: #123b5d; }
    .ticket { padding: 1rem; border-radius: 12px; background: #e8f3ff; border-left: 5px solid #1976d2; }
    </style>
    """,
    unsafe_allow_html=True,
)


def api_key_available() -> bool:
    return bool(os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", ""))


def render_sidebar() -> str:
    st.sidebar.title("Civic Issue Reporter")
    st.sidebar.caption("AI-assisted civic complaint routing")
    page = st.sidebar.radio("Navigate", ["Report Issue", "Track Complaints", "Dashboard"])
    st.sidebar.divider()
    st.sidebar.info(
        "Hackathon demo: upload a clear image, add coordinates, and receive an explainable department recommendation."
    )
    if not api_key_available():
        st.sidebar.warning("GROQ_API_KEY is not configured. Add it to .env or Streamlit secrets.")
    return page


def report_page() -> None:
    st.title("Report a civic issue")
    st.write("Upload evidence and the AI will classify, prioritize, and route your complaint.")

    with st.form("report_form"):
        image = st.file_uploader("Issue photo", type=["jpg", "jpeg", "png", "webp"])
        col1, col2 = st.columns(2)
        latitude = col1.number_input("Latitude", value=24.8607, format="%.6f", help="Example: Karachi")
        longitude = col2.number_input("Longitude", value=67.0011, format="%.6f")
        description = st.text_area("Additional details (optional)", placeholder="What did you observe, and how urgent is it?")
        submitted = st.form_submit_button("Analyze and submit complaint", type="primary", use_container_width=True)

    if not submitted:
        return
    if image is None:
        st.error("Please upload an issue photo.")
        return
    if not api_key_available():
        st.error("Add GROQ_API_KEY to .env or Streamlit Cloud secrets before submitting.")
        return

    image_bytes = image.getvalue()
    with st.spinner("Classifying the image and finding the responsible department..."):
        try:
            classification = classify_image(image_bytes, image.type, description)
            routing = route_issue(classification, description)
            safe_name = f"pending_{image.name.replace(' ', '_')}"
            image_path = UPLOAD_DIR / safe_name
            image_path.write_bytes(image_bytes)
            complaint = create_complaint(
                category=classification["category"],
                severity=classification["severity"],
                confidence=classification["confidence"],
                description=description or classification["description"],
                latitude=latitude,
                longitude=longitude,
                department=routing["department"],
                routing_reason=routing["reason"],
                recommended_action=routing["recommended_action"],
                image_path=str(image_path.relative_to(BASE_DIR)),
            )
        except Exception as exc:
            st.error(f"Submission failed: {exc}")
            return

    st.success("Complaint submitted successfully.")
    st.markdown(f'<div class="ticket"><strong>Ticket ID: {complaint["ticket_id"]}</strong><br>Save this ID to track the complaint.</div>', unsafe_allow_html=True)
    a, b, c = st.columns(3)
    a.metric("Category", complaint["category"].title())
    b.metric("Severity", complaint["severity"].title())
    c.metric("Assigned department", complaint["department"])
    st.info(f"Routing explanation: {complaint['routing_reason']}")
    st.caption(f"Recommended action: {complaint['recommended_action']}")


def complaint_details(complaint: dict) -> None:
    st.subheader(complaint["ticket_id"])
    col1, col2 = st.columns([1, 2])
    with col1:
        image_path = BASE_DIR / complaint["image_path"] if complaint.get("image_path") else None
        if image_path and image_path.exists():
            st.image(str(image_path), use_container_width=True)
    with col2:
        st.write(f"**Category:** {complaint['category'].title()}")
        st.write(f"**Severity:** {complaint['severity'].title()} | **AI confidence:** {complaint['confidence']:.0%}")
        st.write(f"**Department:** {complaint['department']}")
        st.write(f"**Location:** {complaint['latitude']:.6f}, {complaint['longitude']:.6f}")
        st.write(f"**Description:** {complaint['description'] or 'No additional description.'}")
        st.write(f"**Why routed here:** {complaint['routing_reason']}")
        st.write(f"**Suggested action:** {complaint['recommended_action']}")
        new_status = st.selectbox("Update status", STATUS_OPTIONS, index=STATUS_OPTIONS.index(complaint["status"]))
        if st.button("Save status", key=f"status_{complaint['ticket_id']}"):
            update_status(complaint["ticket_id"], new_status)
            st.success("Status updated.")
            st.rerun()


def track_page() -> None:
    st.title("Track complaints")
    rows = get_complaints()
    if not rows:
        st.info("No complaints have been submitted yet.")
        return
    ticket_ids = [row["ticket_id"] for row in rows]
    selected = st.selectbox("Select a ticket", ticket_ids)
    complaint_details(get_complaint(selected))


def dashboard_page() -> None:
    st.title("Civic operations dashboard")
    rows = get_complaints()
    if not rows:
        st.info("Submit a complaint to populate the dashboard.")
        return
    df = pd.DataFrame(rows)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total complaints", len(df))
    c2.metric("Open complaints", int((df["status"] != "Resolved").sum()))
    c3.metric("High severity", int((df["severity"] == "high").sum()))
    c4.metric("Resolved", int((df["status"] == "Resolved").sum()))
    left, right = st.columns(2)
    with left:
        st.subheader("Issues by category")
        st.bar_chart(df["category"].value_counts())
    with right:
        st.subheader("Issues by severity")
        st.bar_chart(df["severity"].value_counts())
    st.subheader("Complaint map")
    st.map(df.rename(columns={"latitude": "lat", "longitude": "lon"})[["lat", "lon"]])
    st.subheader("All complaints")
    st.dataframe(
        df[["ticket_id", "category", "severity", "department", "status", "latitude", "longitude", "created_at"]],
        use_container_width=True,
        hide_index=True,
    )


page = render_sidebar()
if page == "Report Issue":
    report_page()
elif page == "Track Complaints":
    track_page()
else:
    dashboard_page()
