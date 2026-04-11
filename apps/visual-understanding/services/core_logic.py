# FILE: apps/visual-understanding/services/core_logic.py
from __future__ import annotations

from datetime import datetime, timezone

import structlog

from config import Settings
from models.input import VisualUnderstandingInput
from models.output import ClusterColor, VisualUnderstandingOutput
from services.brand_score import BrandConsistencyScorer
from services.color_extractor import ColorExtractor
from services.image_preprocessor import ImagePreprocessor
from services.layout_classifier import LayoutClassifier
from services.style_classifier import StyleClassifier
from services.typography_inference import TypographyInference

log = structlog.get_logger(__name__)


class VisualUnderstandingService:
    def __init__(self, settings: Settings, llm_client: object) -> None:
        self.pre = ImagePreprocessor(llm_client)
        self.color = ColorExtractor(k=6)
        self.typography = TypographyInference()
        self.style = StyleClassifier("apps/visual-understanding/data/style_centroids.json")
        self.layout = LayoutClassifier()
        self.score = BrandConsistencyScorer(
            settings.color_weight,
            settings.typography_weight,
            settings.layout_weight,
            settings.logo_weight,
        )

    async def run(self, payload: VisualUnderstandingInput) -> VisualUnderstandingOutput:
        """Run ordered visual pipeline with no-image and low-resolution fallbacks."""
        log.info("request_received", company_id=str(payload.company_id))

        if not payload.image_url and not payload.image_base64:
            return VisualUnderstandingOutput(
                company_id=payload.company_id,
                style_label="unknown",
                layout_type="unknown",
                typography_style="unknown",
                colors=[],
                brand_consistency_score=0.0,
                confidence_score=0.10,
                degraded=True,
                generated_at=datetime.now(tz=timezone.utc),
            )

        image = await self.pre.process(str(payload.image_url) if payload.image_url else None, payload.image_base64)
        log.info("step_completed", step="image_preprocessing", size=image.size)

        colors = await self.color.process(image)
        log.info("step_completed", step="color_extraction", clusters=len(colors))

        typography_style, typography_conf = await self.typography.process(image)
        log.info("step_completed", step="typography_inference", typography_style=typography_style)

        style_label, style_similarity = await self.style.process(image)
        log.info("step_completed", step="clip_style_classifier", style_label=style_label)

        layout_type, layout_conf = await self.layout.process(image, style_similarity)
        log.info("step_completed", step="layout_classifier", layout_type=layout_type)

        color_alignment = min(1.0, sum(r for _, r in colors[:3]))
        logo_alignment = 0.9 if payload.logo_present_expected else 0.7
        brand_score = await self.score.process(color_alignment, typography_conf, layout_conf, logo_alignment)

        confidence = 0.5 * style_similarity + 0.25 * typography_conf + 0.25 * layout_conf
        degraded = False
        if image.size[0] < 512 or image.size[1] < 512:
            degraded = True
            confidence *= 0.70
            log.warning("fallback_activated", fallback="low_resolution", confidence_score=confidence)

        output = VisualUnderstandingOutput(
            company_id=payload.company_id,
            style_label=style_label,
            layout_type=layout_type,
            typography_style=typography_style,
            colors=[ClusterColor(hex=h, ratio=r) for h, r in colors],
            brand_consistency_score=brand_score,
            confidence_score=max(0.0, min(1.0, confidence)),
            degraded=degraded,
            generated_at=datetime.now(tz=timezone.utc),
        )
        if output.confidence_score <= 0.65:
            log.warning("low_confidence_result", confidence_score=output.confidence_score)
        log.info("response_returned", company_id=str(payload.company_id), confidence_score=output.confidence_score)
        return output
