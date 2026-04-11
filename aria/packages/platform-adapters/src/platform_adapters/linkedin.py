from .base_http import BaseAdapter
from .models import PlatformConstraints


class LinkedInAdapter(BaseAdapter):
    def __init__(self, webhook_secret: str) -> None:
        super().__init__(
            base_url="https://api.linkedin.com/v2",
            webhook_secret=webhook_secret,
            constraints=PlatformConstraints(max_caption_chars=3000, max_hashtags=5, supports_alt_text=True, supports_multi_media=False),
        )
