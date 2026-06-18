from __future__ import annotations

from ai.schemas.brand import BrandProfile


class BrandMemory:
    """Schema-first brand memory facade, ready for DB/vector lookup later."""

    async def load_brand_profile(self, profile: BrandProfile) -> BrandProfile:
        return profile

