import os

import asyncpg

DB_CONFIG = {
    "user": "ella",
    "password": os.environ["DB_PASSWORD"],
    "database": "leaderboard_db_wd6e",
    "host": "localhost",
    "port": 5432,
}

async def init_db():
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS leaderboard (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            score INTEGER NOT NULL,
            timestamp TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    await conn.close()

async def insert_score(username: str, score: int):
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute(
        "INSERT INTO leaderboard (username, score) VALUES ($1, $2)",
        username, score
    )
    await conn.close()

async def get_top_scores(limit: int = 10):
    conn = await asyncpg.connect(**DB_CONFIG)
    rows = await conn.fetch(
        "SELECT username, score, timestamp FROM leaderboard ORDER BY score DESC LIMIT $1",
        limit
    )
    await conn.close()
    return rows
