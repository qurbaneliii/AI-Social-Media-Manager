# FILE: apps/visual-understanding/services/image_preprocessor.py
from __future__ import annotations

import base64
from io import BytesIO

import httpx
from PIL import Image


class ImagePreprocessor:
    def __init__(self, llm_client: httpx.AsyncClient) -> None:
        self.llm_client = llm_client

    async def process(self, image_url: str | None, image_base64: str | None) -> Image.Image:
        """Load image from URL or base64, convert RGB, resize longest edge to 1024 with LANCZOS."""
        if image_url:
            response = await self.llm_client.get(image_url)
            response.raise_for_status()
            raw = response.content
        else:
            raw = base64.b64decode(image_base64 or "")

        img = Image.open(BytesIO(raw)).convert("RGB")
        width, height = img.size
        longest = max(width, height)
        if longest > 1024:
            scale = 1024 / float(longest)
            img = img.resize((int(width * scale), int(height * scale)), Image.Resampling.LANCZOS)
        return img
