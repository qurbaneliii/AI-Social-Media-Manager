# FILE: apps/hashtag-seo/services/seo_metadata_generator.py
from __future__ import annotations

from config import Settings


class SeoMetadataGenerator:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def process(self, core_text: str, keywords: list[str]) -> dict:
        """Generate deterministic SEO metadata with strict character and keyword density constraints."""
        joined_kw = " ".join(keywords[:6])
        title = f"{joined_kw} | ARIA"[:60]
        description = (core_text[:130] + " " + joined_kw)[:160]
        alt_text = ("Image for " + joined_kw)[:220]

        primary = keywords[0].lower() if keywords else ""
        density = description.lower().count(primary) / max(len(description.split()), 1) if primary else 0.0
        if density < self.settings.primary_kw_density_min and primary:
            description = (description + f" {primary}")[:160]
        if density > self.settings.primary_kw_density_max and primary:
            words = [w for w in description.split() if w.lower() != primary]
            description = " ".join(words)[:160]

        return {"meta_title": title, "meta_description": description, "alt_text": alt_text}
