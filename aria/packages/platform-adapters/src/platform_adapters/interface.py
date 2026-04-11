from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from .models import (
    CanonicalPublishPayload,
    MetricRecord,
    OAuthCredentials,
    PlatformConstraints,
    PublishResult,
    WebhookEvent,
)


class PlatformAdapter(ABC):
    @abstractmethod
    async def publish(self, payload: CanonicalPublishPayload) -> PublishResult:
        raise NotImplementedError

    @abstractmethod
    async def pull_metrics(self, post_id: str, since: datetime) -> list[MetricRecord]:
        raise NotImplementedError

    @abstractmethod
    async def validate_credentials(self, credentials: OAuthCredentials) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_content_constraints(self) -> PlatformConstraints:
        raise NotImplementedError

    @abstractmethod
    async def handle_webhook(self, raw_payload: dict, signature: str) -> WebhookEvent:
        raise NotImplementedError
