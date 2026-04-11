# filename: api/media.py
# purpose: Media API endpoints for presigned upload and upload confirmation.
# dependencies: fastapi, pydantic, flows/services media

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict

from services.media import MediaService

router = APIRouter()


class PresignRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    company_id: str
    filename: str
    content_type: str


@router.post("/presign")
async def presign(payload: PresignRequest, request: Request) -> dict[str, Any]:
    service: MediaService = request.app.state.media_service
    return await service.presign_upload(
        company_id=payload.company_id,
        filename=payload.filename,
        content_type=payload.content_type,
    )


@router.post("/confirm/{asset_id}")
async def confirm(asset_id: str, request: Request) -> dict[str, str]:
    service: MediaService = request.app.state.media_service
    await service.confirm_upload(asset_id)
    return {"status": "uploaded"}
