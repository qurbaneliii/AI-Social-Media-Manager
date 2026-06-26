from __future__ import annotations

from typing import Protocol

from ai.schemas.brand import BrandProfile


class BrandProfileStore(Protocol):
    async def load_brand_profile(self, brand_id: str) -> BrandProfile | None:
        ...

    async def save_brand_profile(self, profile: BrandProfile) -> dict:
        ...


class BrandProfileNotFoundError(LookupError):
    def __init__(self, brand_id: str) -> None:
        super().__init__(f"Brand profile not found: {brand_id}")
        self.brand_id = brand_id


class BrandMemory:
    """Schema-first brand memory facade with optional database-backed storage."""

    def __init__(self, store: BrandProfileStore | None = None, *, allow_profile_bootstrap: bool = True) -> None:
        self.store = store
        self.allow_profile_bootstrap = allow_profile_bootstrap

    async def load_brand_profile(self, profile: BrandProfile) -> BrandProfile:
        if self.store is None:
            return profile
        stored = await self.store.load_brand_profile(profile.brand_id)
        if stored is None:
            if self.allow_profile_bootstrap:
                await self.store.save_brand_profile(profile)
                return profile
            raise BrandProfileNotFoundError(profile.brand_id)
        return stored

    async def save_brand_profile(self, profile: BrandProfile) -> None:
        if self.store is None:
            return
        await self.store.save_brand_profile(profile)

