# FILE: apps/scheduler/services/webhook_validator.py
from __future__ import annotations

import hashlib
import hmac
import json
from uuid import UUID

import asyncpg


class WebhookValidator:
    def __init__(self, db_pool: asyncpg.Pool) -> None:
        self.db_pool = db_pool

    async def process(self, company_id: UUID, platform: str, payload: dict, signature: str, kms_secret: str) -> bool:
        """Validate HMAC-SHA256 signature and write audit log on mismatch."""
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        expected = hmac.new(kms_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        valid = hmac.compare_digest(expected, signature.replace("sha256=", ""))

        if not valid:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO audit_logs (tenant_id, company_id, action, resource_type, resource_id, metadata_json)
                    VALUES ($1, $2, 'webhook_signature_rejected', 'webhook', $3, $4::jsonb)
                    """,
                    company_id,
                    company_id,
                    platform,
                    json.dumps(payload),
                )
        return valid
