# filename: services/import_parser.py
# purpose: Parse CSV/JSON onboarding archives and stage records into import_staging.
# dependencies: csv, io, json, uuid, asyncpg

from __future__ import annotations

import csv
import io
import json
import uuid
from typing import Any

import asyncpg

from db.connection import set_tenant

IMPORT_STAGING_MIGRATION_SQL = """
CREATE TABLE import_staging (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
  platform TEXT NOT NULL,
  text TEXT NOT NULL,
  raw JSONB,
  import_id UUID NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
""".strip()


class ImportParser:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self.pool = pool

    def _parse_rows(self, file_bytes: bytes, filename: str) -> list[dict[str, Any]]:
        lower = filename.lower()
        if lower.endswith(".csv"):
            content = file_bytes.decode("utf-8")
            reader = csv.DictReader(io.StringIO(content))
            return [dict(row) for row in reader]

        if lower.endswith(".json"):
            content = json.loads(file_bytes.decode("utf-8"))
            if isinstance(content, list):
                return [dict(item) for item in content if isinstance(item, dict)]
            if isinstance(content, dict):
                rows = content.get("rows", [])
                if isinstance(rows, list):
                    return [dict(item) for item in rows if isinstance(item, dict)]
            raise ValueError("JSON payload must be a list of objects or an object with 'rows'")

        raise ValueError("Unsupported file extension; expected .csv or .json")

    async def parse_and_stage(self, company_id: str, file_bytes: bytes, filename: str) -> dict[str, Any]:
        rows = self._parse_rows(file_bytes, filename)
        import_id = str(uuid.uuid4())

        insert_query = """
        INSERT INTO import_staging (company_id, platform, text, raw, import_id)
        VALUES ($1::uuid, $2, $3, $4::jsonb, $5::uuid)
        """

        staged_count = 0
        skipped_count = 0
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, company_id)
                for row in rows:
                    text = str(row.get("text", "")).strip()
                    platform = str(row.get("platform", "")).strip()
                    if not text or not platform:
                        skipped_count += 1
                        continue
                    await conn.execute(
                        insert_query,
                        company_id,
                        platform,
                        text,
                        json.dumps(row),
                        import_id,
                    )
                    staged_count += 1

        return {
            "import_id": import_id,
            "staged_count": staged_count,
            "skipped_count": skipped_count,
        }
