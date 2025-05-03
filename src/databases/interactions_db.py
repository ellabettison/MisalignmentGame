import sqlite3
from datetime import datetime

DB_NAME = "interactions.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            score REAL,
            timestamp TEXT,
            agent INTEGER,
            type TEXT,
            speaker TEXT,
            text TEXT,
            guess TEXT,
            correct BOOLEAN,
            true_goal TEXT,
            agent_policy TEXT
        )
    """)

    conn.commit()
    conn.close()

def insert_interactions(username: str, score: float, interaction_log: list):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    timestamp = datetime.utcnow().isoformat()

    for entry in interaction_log:
        common_data = {
            "username": username,
            "score": score,
            "timestamp": timestamp,
            "agent": entry.get("agent"),
            "type": entry.get("type"),
            "speaker": entry.get("speaker"),
            "text": entry.get("text"),
            "guess": entry.get("guess"),
            "correct": entry.get("correct"),
            "true_goal": entry.get("true_goal"),
            "agent_policy": entry.get("agent_policy"),
        }

        # Convert to tuple based on table column order
        cursor.execute("""
            INSERT INTO interactions (
                username, score, timestamp, agent, type, speaker, text, guess, correct, true_goal, agent_policy
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            common_data["username"],
            common_data["score"],
            common_data["timestamp"],
            common_data["agent"],
            common_data["type"],
            common_data["speaker"],
            common_data["text"],
            common_data["guess"],
            common_data["correct"],
            common_data["true_goal"],
            common_data["agent_policy"],
        ))

    conn.commit()
    conn.close()
