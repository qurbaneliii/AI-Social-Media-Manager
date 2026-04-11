from .base_http import BaseAdapter
from .models import PlatformConstraints


class InstagramAdapter(BaseAdapter):
    def __init__(self, webhook_secret: str) -> None:
        super().__init__(
            base_url="https://graph.facebook.com/v20.0",
            webhook_secret=webhook_secret,
            constraints=PlatformConstraints(max_caption_chars=2200, max_hashtags=30, supports_alt_text=True, supports_multi_media=True),
        )
