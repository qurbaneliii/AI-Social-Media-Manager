from __future__ import annotations

from ai.schemas.content import GeneratedContentPackage


def requires_human_approval(package: GeneratedContentPackage) -> bool:
    return bool(package.risks) or package.quality_scores is None or package.quality_scores.approval_status != "approved"

