# FILE: apps/content-analysis/services/ingestion_parser.py
from __future__ import annotations

from models.input import ContentAnalysisInput


class IngestionParser:
    def __init__(self) -> None:
        pass

    async def process(self, payload: ContentAnalysisInput) -> list[str]:
        """Normalize and trim incoming text samples for downstream NLP stages."""
        texts: list[str] = []
        for post in payload.sample_posts:
            cleaned = " ".join(post.text.split())
            if cleaned:
                texts.append(cleaned)
        return texts
