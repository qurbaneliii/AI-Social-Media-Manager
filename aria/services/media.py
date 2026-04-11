# filename: services/media.py
# purpose: MinIO-backed media presign/upload URL operations with media_assets persistence.
# dependencies: os, uuid, datetime, boto3, asyncpg

from __future__ import annotations

import os
import uuid
from typing import Any

import asyncpg
import boto3

from db.connection import set_tenant


SERVICE_COMPANY_ID = "00000000-0000-0000-0000-000000000000"


class MediaService:
    def __init__(self, pool: asyncpg.Pool, s3_client: Any) -> None:
        self.pool = pool
        self.s3_client = s3_client
        self.bucket = os.getenv("MINIO_BUCKET", "aria-media")

    async def presign_upload(self, company_id: str, filename: str, content_type: str) -> dict[str, Any]:
        asset_id = str(uuid.uuid4())
        s3_key = f"{company_id}/{asset_id}/{filename}"
        url = self.s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.bucket,
                "Key": s3_key,
                "ContentType": content_type,
            },
            ExpiresIn=300,
        )

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, company_id)
                await conn.execute(
                    """
                    INSERT INTO media_assets (asset_id, company_id, filename, content_type, s3_key, status)
                    VALUES ($1::uuid, $2::uuid, $3, $4, $5, 'pending')
                    """,
                    asset_id,
                    company_id,
                    filename,
                    content_type,
                    s3_key,
                )

        return {
            "upload_url": url,
            "asset_id": asset_id,
            "expires_in": 300,
        }

    async def confirm_upload(self, asset_id: str) -> None:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, SERVICE_COMPANY_ID, role="service")
                await conn.execute(
                    "UPDATE media_assets SET status = 'uploaded' WHERE asset_id = $1::uuid",
                    asset_id,
                )

    async def get_asset_url(self, asset_id: str) -> str:
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await set_tenant(conn, SERVICE_COMPANY_ID, role="service")
                row = await conn.fetchrow(
                    "SELECT s3_key FROM media_assets WHERE asset_id = $1::uuid",
                    asset_id,
                )
        if row is None:
            raise ValueError("asset not found")

        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": str(row["s3_key"])},
            ExpiresIn=3600,
        )
