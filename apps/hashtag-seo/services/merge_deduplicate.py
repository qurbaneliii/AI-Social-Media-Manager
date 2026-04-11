# FILE: apps/hashtag-seo/services/merge_deduplicate.py
from __future__ import annotations


class MergeDeduplicator:
    def __init__(self) -> None:
        pass

    async def process(self, llm_candidates: list[str], vector_candidates: list[dict]) -> list[str]:
        """Merge and deduplicate tags by normalized token (lowercase, no leading hash)."""
        merged = llm_candidates + [str(c.get("hashtag", "")) for c in vector_candidates]
        output: list[str] = []
        seen: set[str] = set()
        for tag in merged:
            token = tag.lower().strip().lstrip("#")
            if not token or token in seen:
                continue
            seen.add(token)
            output.append(token)
        return output
