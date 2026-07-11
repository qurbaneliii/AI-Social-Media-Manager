from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ai.memory import BrandProfileNotFoundError
from ai.persistence import AIPersistenceRepository
from ai.schemas.brand import (
    BrandProfile,
    BrandProfileResponse,
    BrandProfileValidationResult,
    ProductContext,
    validate_brand_profile_completeness,
)
from api.dependencies import get_persistence_repository


router = APIRouter(prefix="/internal/ai", tags=["workspace"])


class BrandProfileUpsertRequest(BaseModel):
    profile: BrandProfile


class BrandProfileValidationRequest(BaseModel):
    profile: BrandProfile
    using_default_context: bool = False


def _brand_profile_response(profile: BrandProfile, *, persisted: bool = True) -> BrandProfileResponse:
    return BrandProfileResponse(
        profile=profile,
        validation=validate_brand_profile_completeness(profile),
        persisted=persisted,
    )


@router.get("/workspace-context", response_model=ProductContext)
def get_workspace_context() -> ProductContext:
    return ProductContext()


@router.get("/brand-profile/{brand_id}", response_model=BrandProfileResponse)
async def get_brand_profile(
    brand_id: str,
    repository: AIPersistenceRepository = Depends(get_persistence_repository),
) -> BrandProfileResponse:
    profile = await repository.load_brand_profile(brand_id)
    if profile is None:
        raise BrandProfileNotFoundError(brand_id)
    return _brand_profile_response(profile)


@router.post("/brand-profile", response_model=BrandProfileResponse)
async def upsert_brand_profile(
    payload: BrandProfileUpsertRequest,
    repository: AIPersistenceRepository = Depends(get_persistence_repository),
) -> BrandProfileResponse:
    await repository.save_brand_profile(payload.profile)
    return _brand_profile_response(payload.profile)


@router.put("/brand-profile/{brand_id}", response_model=BrandProfileResponse)
async def update_brand_profile(
    brand_id: str,
    payload: BrandProfileUpsertRequest,
    repository: AIPersistenceRepository = Depends(get_persistence_repository),
) -> BrandProfileResponse:
    if payload.profile.brand_id != brand_id:
        raise HTTPException(status_code=400, detail="brand_id path parameter must match profile.brand_id.")
    await repository.save_brand_profile(payload.profile)
    return _brand_profile_response(payload.profile)


@router.post("/brand-profile/validate", response_model=BrandProfileValidationResult)
async def validate_brand_profile(payload: BrandProfileValidationRequest) -> BrandProfileValidationResult:
    return validate_brand_profile_completeness(
        payload.profile,
        using_default_context=payload.using_default_context,
    )
