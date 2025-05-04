import asyncio
import os
from datetime import datetime
import asyncpg

DB_CONFIG = {
    "host": "aws-0-eu-west-2.pooler.supabase.com",
    "port": 6543,
    "database": "postgres",
    "user": "postgres.mhcxooasziiqidmjuplu",
    "password": os.environ["INTERACTIONS_DB_PW"],
    "statement_cache_size": 0  # <-- Prevent some Supabase-specific issues
}

pool = None  # Global connection pool

async def init_db():
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(**DB_CONFIG)

    await pool.execute("""
        CREATE TABLE IF NOT EXISTS interactions (
            id SERIAL PRIMARY KEY,
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

async def insert_interactions(username: str, score: float, interaction_log: list[dict]):
    global pool
    if not pool:
        raise RuntimeError("DB pool not initialized. Call init_db() first.")

    timestamp = datetime.utcnow().isoformat()

    async with pool.acquire() as conn:
        async with conn.transaction():
            for entry in interaction_log:
                await conn.execute("""
    INSERT INTO interactions (
        username, score, timestamp, agent, type, speaker, text, guess, correct, true_goal, agent_policy
    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
""",
                                   username,
                                   score,
                                   timestamp,
                                   entry.get("agent"),
                                   entry.get("type"),
                                   entry.get("speaker"),
                                   entry.get("text"),
                                   entry.get("guess"),
                                   entry.get("correct"),
                                   entry.get("true_goal"),
                                   entry.get("agent_policy"),
                                   )