import sqlite3

def init_db():
    conn = sqlite3.connect("leaderboard.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leaderboard (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            score INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def insert_score(username, score):
    conn = sqlite3.connect("leaderboard.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO leaderboard (username, score) VALUES (?, ?)", (username, score))
    conn.commit()
    conn.close()

def get_top_scores(limit=10):
    conn = sqlite3.connect("leaderboard.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, score, timestamp FROM leaderboard ORDER BY score DESC LIMIT ?", (limit,))
    scores = cursor.fetchall()
    conn.close()
    return scores