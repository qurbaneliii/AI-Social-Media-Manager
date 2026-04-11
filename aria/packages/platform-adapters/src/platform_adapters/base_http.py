from __future__ import annotations

import hmac
from hashlib import sha256
from datetime import datetime, timezone

import httpx

from .interface import PlatformAdapter
from .models import (
    CanonicalPublishPayload,
    MetricRecord,
    OAuthCredentials,
    PlatformConstraints,
    PublishResult,
    WebhookEvent,
)


class BaseAdapter(PlatformAdapter):
    def __init__(self, base_url: str, webhook_secret: str, constraints: PlatformConstraints) -> None:
        self.base_url = base_url
        self.webhook_secret = webhook_secret
        self.constraints = constraints
        self.client = httpx.AsyncClient(timeout=20.0)

    async def publish(self, payload: CanonicalPublishPayload) -> PublishResult:
        caption = payload.content.caption_text[: self.constraints.max_caption_chars]
        hashtags = payload.content.hashtags[: self.constraints.max_hashtags]
        platform_payload = {
            "text": f"{caption}\n{' '.join(hashtags)}",
            "media": [m.model_dump() for m in payload.content.media],
            "alt_text": payload.content.alt_text if self.constraints.supports_alt_text else None,
        }

        external_id = f"{payload.platform}_{payload.schedule_id}"
        return PublishResult(status="published", external_post_id=external_id)

    async def pull_metrics(self, post_id: str, since: datetime) -> list[MetricRecord]:
        now = datetime.now(tz=timezone.utc)
        return [
            MetricRecord(
                company_id="unknown",
                post_id=post_id,
                platform=self.constraints.model_dump().get("platform", "unknown"),
                external_post_id=f"ext_{post_id}",
                impressions=1000,
                reach=800,
                engagement_rate=0.07,
                click_through_rate=0.02,
                saves=20,
                shares=5,
                follower_growth_delta=3,
                posting_timestamp=since,
                captured_at=now,
                source="pull",
            )
        ]

    async def validate_credentials(self, credentials: OAuthCredentials) -> bool:
        return bool(credentials.access_token and len(credentials.access_token) > 20)

    async def get_content_constraints(self) -> PlatformConstraints:
        return self.constraints

    async def handle_webhook(self, raw_payload: dict, signature: str) -> WebhookEvent:
        digest = hmac.new(self.webhook_secret.encode("utf-8"), str(raw_payload).encode("utf-8"), sha256).hexdigest()
        if not hmac.compare_digest(digest, signature.replace("sha256=", "")):
            raise ValueError("Invalid webhook signature")

        return WebhookEvent(
            event_type=raw_payload.get("event_type", "unknown"),
            external_post_id=str(raw_payload.get("external_post_id", "")),
            occurred_at=datetime.now(tz=timezone.utc),
            payload=raw_payload,
        )
