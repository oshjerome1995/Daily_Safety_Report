import sqlite3
from config import DATABASE

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        detailed_observation TEXT,
        picture_path TEXT,
        additional_picture_path TEXT,
        area_department TEXT,
        checked_by TEXT,
        action_done TEXT,
        date TEXT,
        so_timestamp TEXT,
        area_in_charge TEXT,
        category TEXT,
        status TEXT,
        osh_rule TEXT,
        safety_officer TEXT
    )
    """)
    conn.commit()
    conn.close()