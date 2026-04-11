from .base_http import BaseAdapter
from .models import PlatformConstraints


class TikTokAdapter(BaseAdapter):
    def __init__(self, webhook_secret: str) -> None:
        super().__init__(
            base_url="https://open.tiktokapis.com/v2",
            webhook_secret=webhook_secret,
            constraints=PlatformConstraints(max_caption_chars=2200, max_hashtags=12, supports_alt_text=False, supports_multi_media=False),
        )
