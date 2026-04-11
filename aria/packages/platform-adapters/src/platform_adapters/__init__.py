from .interface import PlatformAdapter
from .models import (
    CanonicalPublishPayload,
    MetricRecord,
    OAuthCredentials,
    PlatformConstraints,
    PublishResult,
    WebhookEvent,
)
from .instagram import InstagramAdapter
from .linkedin import LinkedInAdapter
from .facebook import FacebookAdapter
from .x_adapter import XAdapter
from .tiktok import TikTokAdapter


def adapter_registry(webhook_secret: str) -> dict[str, PlatformAdapter]:
    return {
        "instagram": InstagramAdapter(webhook_secret),
        "linkedin": LinkedInAdapter(webhook_secret),
        "facebook": FacebookAdapter(webhook_secret),
        "x": XAdapter(webhook_secret),
        "tiktok": TikTokAdapter(webhook_secret),
    }


__all__ = [
    "PlatformAdapter",
    "CanonicalPublishPayload",
    "MetricRecord",
    "OAuthCredentials",
    "PlatformConstraints",
    "PublishResult",
    "WebhookEvent",
    "InstagramAdapter",
    "LinkedInAdapter",
    "FacebookAdapter",
    "XAdapter",
    "TikTokAdapter",
    "adapter_registry",
]
