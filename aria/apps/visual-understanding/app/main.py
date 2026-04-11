from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from typing import Any

import cv2
import httpx
import numpy as np
import pytesseract
import redis
from fastapi import Depends, FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from PIL import Image
from pydantic import BaseModel
from sqlalchemy import create_engine


class VisualInput(BaseModel):
    tenant_id: str
    company_id: str
    media_id: str
    image_url: str


class VisualOutput(BaseModel):
    palette: list[str]
    typography: dict[str, Any]
    layout: dict[str, Any]
    ocr_text: str
    emitted_event: dict[str, Any]


class Dependencies:
    def __init__(self) -> None:
        self.db = create_engine("postgresql+psycopg://postgres:postgres@localhost:5432/aria", pool_pre_ping=True)
        self.cache = redis.Redis.from_url("redis://localhost:6379/0")
        self.vector = self.db


def get_deps() -> Dependencies:
    return Dependencies()


app = FastAPI(title="ARIA Visual Understanding Service")
FastAPIInstrumentor.instrument_app(app)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "visual-understanding"}


@app.post("/run", response_model=VisualOutput)
def run_visual(payload: VisualInput, deps: Dependencies = Depends(get_deps)) -> VisualOutput:
    image_bytes = httpx.get(payload.image_url, timeout=15.0).content
    pil_img = Image.open(BytesIO(image_bytes)).convert("RGB")
    arr = np.array(pil_img)

    h, w, _ = arr.shape
    resized = cv2.resize(arr, (max(1, w // 2), max(1, h // 2)))
    flat = resized.reshape(-1, 3)
    unique, counts = np.unique(flat, axis=0, return_counts=True)
    top_idx = np.argsort(counts)[-5:][::-1]
    palette = [f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}" for rgb in unique[top_idx]]

    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    density = float(np.sum(edges > 0) / edges.size)

    ocr_text = pytesseract.image_to_string(pil_img)[:2000]

    typography = {
        "ocr_char_count": len(ocr_text),
        "estimated_text_density": round(len(ocr_text) / max(h * w, 1), 6),
    }
    layout = {
        "width": int(w),
        "height": int(h),
        "edge_density": round(density, 6),
    }

    deps.cache.setex(f"visual:{payload.media_id}", 3600, str({"palette": palette, "layout": layout}))

    event = {
        "event_id": f"evt-{payload.media_id}-{int(datetime.now(tz=timezone.utc).timestamp())}",
        "event_type": "brand.visual.ready.v1",
        "tenant_id": payload.tenant_id,
        "company_id": payload.company_id,
        "schema_version": 1,
        "emitted_at": datetime.now(tz=timezone.utc).isoformat(),
        "payload": {
            "media_id": payload.media_id,
            "analysis_id": payload.media_id,
            "ready_at": datetime.now(tz=timezone.utc).isoformat(),
        },
    }

    return VisualOutput(
        palette=palette,
        typography=typography,
        layout=layout,
        ocr_text=ocr_text,
        emitted_event=event,
    )
