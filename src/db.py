
import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path("data") / "soc_history.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS detection_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_time TEXT NOT NULL,
                file_name TEXT NOT NULL,
                model_name TEXT NOT NULL,
                threshold INTEGER NOT NULL,
                total_flows INTEGER NOT NULL,
                potential_attacks INTEGER NOT NULL,
                benign_flows INTEGER NOT NULL,
                high_critical_alerts INTEGER NOT NULL
            )
        """)


def save_analysis(
    file_name,
    model_name,
    threshold,
    total_flows,
    potential_attacks,
    benign_flows,
    high_critical_alerts,
):
    with get_connection() as connection:
        connection.execute("""
            INSERT INTO detection_history (
                analysis_time,
                file_name,
                model_name,
                threshold,
                total_flows,
                potential_attacks,
                benign_flows,
                high_critical_alerts
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            file_name,
            model_name,
            threshold,
            total_flows,
            potential_attacks,
            benign_flows,
            high_critical_alerts,
        ))


def get_history():
    with get_connection() as connection:
        return connection.execute("""
            SELECT
                id,
                analysis_time AS 'Analysis Time',
                file_name AS 'File',
                model_name AS 'Model',
                threshold AS 'Threshold (%)',
                total_flows AS 'Flows Analyzed',
                potential_attacks AS 'Potential Attacks',
                benign_flows AS 'Benign Flows',
                high_critical_alerts AS 'High/Critical Alerts'
            FROM detection_history
            ORDER BY id DESC
        """).fetchall()


def clear_history():
    with get_connection() as connection:
        connection.execute("DELETE FROM detection_history")
