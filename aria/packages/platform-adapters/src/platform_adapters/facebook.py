from .base_http import BaseAdapter
from .models import PlatformConstraints


class FacebookAdapter(BaseAdapter):
    def __init__(self, webhook_secret: str) -> None:
        super().__init__(
            base_url="https://graph.facebook.com/v20.0",
            webhook_secret=webhook_secret,
            constraints=PlatformConstraints(max_caption_chars=63206, max_hashtags=10, supports_alt_text=True, supports_multi_media=True),
        )
