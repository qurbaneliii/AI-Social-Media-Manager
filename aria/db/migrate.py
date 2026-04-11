# filename: db/migrate.py
# purpose: Async SQL migration runner for db/migrations using schema_migrations tracking table.
# dependencies: os, pathlib, asyncpg, asyncio

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import asyncpg


async def run_migrations() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    migrations_dir = Path(__file__).resolve().parent / "migrations"
    files = sorted(path for path in migrations_dir.glob("*.sql"))

    conn = await asyncpg.connect(database_url)
    try:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename TEXT PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )

        applied_rows = await conn.fetch("SELECT filename FROM schema_migrations")
        applied = {row["filename"] for row in applied_rows}

        for file in files:
            if file.name in applied:
                print(f"[SKIP] {file.name}")
                continue

            sql = file.read_text(encoding="utf-8")
            async with conn.transaction():
                await conn.execute(sql)
                await conn.execute(
                    "INSERT INTO schema_migrations (filename) VALUES ($1)",
                    file.name,
                )
            print(f"[OK] {file.name}")
    finally:
        await conn.close()


def main() -> None:
    asyncio.run(run_migrations())


if __name__ == "__main__":
    main()
