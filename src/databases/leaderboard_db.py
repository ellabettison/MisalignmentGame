import os

import asyncpg

# DB_CONFIG = {
#     "user": "ella",
#     "password": os.environ["DB_PASSWORD"],
#     "database": "leaderboard_db_wd6e",
#     "host": "localhost",
#     "port": 5432,
# }

DB_CONFIG = {
    "host": "aws-0-eu-west-2.pooler.supabase.com",
    "port": 6543,
    "database": "postgres",
    "user": "postgres.mhcxooasziiqidmjuplu",
    "password": os.environ["INTERACTIONS_DB_PW"],
    "statement_cache_size": 0  # <-- Prevent some Supabase-specific issues
}

pool = None


async def init_db(difficulty: str):
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(**DB_CONFIG)

    await pool.execute(f"""
        CREATE TABLE IF NOT EXISTS leaderboard_{difficulty} (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            score INTEGER NOT NULL,
            timestamp TIMESTAMPTZ DEFAULT NOW()
        )
    """)

async def insert_score(username: str, score: int, difficulty: str):
    global pool
    if not pool:
        raise RuntimeError("DB pool not initialized. Call init_db() first.")
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                f"INSERT INTO leaderboard_{difficulty} (username, score) VALUES ($1, $2)",
                username, score
            )

async def get_top_scores(difficulty: str, limit: int = 10):
    global pool
    if not pool:
        raise RuntimeError("DB pool not initialized. Call init_db() first.")
    async with pool.acquire() as conn:
        async with conn.transaction():
            return await conn.fetch(
        f"SELECT username, score, timestamp FROM leaderboard_{difficulty} ORDER BY score DESC LIMIT $1",
        limit
    )
