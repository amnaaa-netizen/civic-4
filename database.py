"""
SQLite database helper for Civic Issue Reporter
"""

import sqlite3
from datetime import datetime
import os

DB_PATH = "civic_reports.db"


def init_db():
    """Create tables if not exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id TEXT UNIQUE,
            date TEXT,
            issue_type TEXT,
            department TEXT,
            priority TEXT,
            severity TEXT,
            location TEXT,
            latitude REAL,
            longitude REAL,
            description TEXT,
            status TEXT DEFAULT 'Pending',
            upvotes INTEGER DEFAULT 0,
            reporter TEXT DEFAULT 'Anonymous',
            resolved_date TEXT
        )
    """)
    conn.commit()
    conn.close()


def add_report(report):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO reports 
            (report_id, date, issue_type, department, priority, severity,
             location, latitude, longitude, description, status, reporter)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            report["report_id"], report["date"], report["issue_type"],
            report["department"], report["priority"], report["severity"],
            report["location"], report["latitude"], report["longitude"],
            report["description"], "Pending", report.get("reporter", "Anonymous")
        ))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_all_reports():
    conn = sqlite3.connect(DB_PATH)
    df = __import__("pandas").read_sql_query("SELECT * FROM reports ORDER BY id DESC", conn)
    conn.close()
    return df


def update_status(report_id, status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    resolved = datetime.now().strftime("%Y-%m-%d %H:%M") if status == "Resolved" else None
    c.execute(
        "UPDATE reports SET status=?, resolved_date=? WHERE report_id=?",
        (status, resolved, report_id)
    )
    conn.commit()
    conn.close()


def upvote(report_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE reports SET upvotes = upvotes + 1 WHERE report_id=?", (report_id,))
    conn.commit()
    conn.close()


def find_duplicate(latitude, longitude, issue_type, radius_deg=0.001):
    """Check if similar issue exists nearby (approx 100m)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT report_id FROM reports 
        WHERE issue_type=? 
        AND ABS(latitude - ?) < ? 
        AND ABS(longitude - ?) < ?
        AND status != 'Resolved'
    """, (issue_type, latitude, radius_deg, longitude, radius_deg))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM reports")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM reports WHERE status='Pending'")
    pending = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM reports WHERE status='Resolved'")
    resolved = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM reports WHERE priority='High'")
    high = c.fetchone()[0]
    conn.close()
    return {"total": total, "pending": pending, "resolved": resolved, "high": high}
