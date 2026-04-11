# filename: app/vision.py
# purpose: Deterministic local vision pipeline for OCR, CLIP features, color palette extraction, and brand consistency scoring.
# dependencies: os, json, numpy, cv2, pytesseract, open_clip, torch, PIL

from __future__ import annotations

import json
import os
from typing import Any

import cv2
import numpy as np
import open_clip
import pytesseract
import torch
from PIL import Image


_CLIP_MODEL: Any = None
_CLIP_PREPROCESS: Any = None
_CLIP_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    if a.size == 0 or b.size == 0:
        return 0.0
    if a.shape != b.shape:
        return 0.0
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def _load_clip() -> tuple[Any, Any]:
    global _CLIP_MODEL, _CLIP_PREPROCESS
    if _CLIP_MODEL is None or _CLIP_PREPROCESS is None:
        model, _, preprocess = open_clip.create_model_and_transforms(
            "ViT-B-32", pretrained="laion2b_s34b_b79k"
        )
        model.eval()
        model.to(_CLIP_DEVICE)
        _CLIP_MODEL = model
        _CLIP_PREPROCESS = preprocess
    return _CLIP_MODEL, _CLIP_PREPROCESS


def run_ocr(image_path: str) -> dict[str, Any]:
    """Run Tesseract OCR and return text blocks, confidence, and text density."""
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Unable to read image at path: {image_path}")

    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    blocks: list[str] = []
    confidences: list[float] = []

    for text, conf in zip(data.get("text", []), data.get("conf", [])):
        text_clean = str(text).strip()
        if not text_clean:
            continue
        blocks.append(text_clean)
        try:
            conf_value = float(conf)
            if conf_value >= 0:
                confidences.append(conf_value / 100.0)
        except (TypeError, ValueError):
            continue

    height, width = image.shape[:2]
    area = max(width * height, 1)
    total_chars = sum(len(block) for block in blocks)
    text_density = float(total_chars / area)
    confidence = float(sum(confidences) / len(confidences)) if confidences else 0.0

    return {
        "text_blocks": blocks,
        "confidence": confidence,
        "text_density": text_density,
    }


def run_clip(image_path: str) -> dict[str, Any]:
    """Extract CLIP embedding and simple layout/visual-tone tags."""
    model, preprocess = _load_clip()

    image = Image.open(image_path).convert("RGB")
    image_tensor = preprocess(image).unsqueeze(0).to(_CLIP_DEVICE)

    with torch.no_grad():
        features = model.encode_image(image_tensor)
        features = features / features.norm(dim=-1, keepdim=True)
    embedding = features[0].cpu().numpy().astype(float)

    width, height = image.size
    ratio = width / max(height, 1)
    if ratio > 1.2:
        layout_tag = "landscape"
    elif ratio < 0.8:
        layout_tag = "portrait"
    else:
        layout_tag = "square"

    image_np = np.array(image)
    hsv = cv2.cvtColor(image_np, cv2.COLOR_RGB2HSV)
    mean_hue = float(np.mean(hsv[:, :, 0]))
    mean_brightness = float(np.mean(hsv[:, :, 2]))

    if mean_brightness < 70:
        visual_tone = "dark"
    elif mean_hue < 30 or mean_hue > 150:
        visual_tone = "warm"
    elif 60 <= mean_hue <= 140:
        visual_tone = "cool"
    else:
        visual_tone = "neutral"

    return {
        "embedding": embedding.tolist(),
        "layout_tag": layout_tag,
        "visual_tone": visual_tone,
    }


def extract_colors(image_path: str) -> dict[str, Any]:
    """Extract dominant palette and ratios using OpenCV k-means (k=5)."""
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Unable to read image at path: {image_path}")

    pixels = cv2.cvtColor(image, cv2.COLOR_BGR2RGB).reshape((-1, 3)).astype(np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.2)
    k = 5
    _compactness, labels, centers = cv2.kmeans(
        pixels,
        k,
        None,
        criteria,
        10,
        cv2.KMEANS_PP_CENTERS,
    )

    labels_flat = labels.flatten()
    total = max(len(labels_flat), 1)
    palette: list[str] = []
    ratios: list[float] = []

    for idx, center in enumerate(centers.astype(np.uint8)):
        r, g, b = int(center[0]), int(center[1]), int(center[2])
        palette.append(f"#{r:02x}{g:02x}{b:02x}")
        ratios.append(float(np.sum(labels_flat == idx) / total))

    order = sorted(range(len(ratios)), key=lambda i: ratios[i], reverse=True)
    sorted_palette = [palette[i] for i in order]
    sorted_ratios = [ratios[i] for i in order]

    return {
        "palette": sorted_palette,
        "ratios": sorted_ratios,
    }


def analyze_image(image_path: str) -> dict[str, Any]:
    """Run OCR, CLIP, and color extraction and compute brand consistency score."""
    ocr = run_ocr(image_path)
    clip = run_clip(image_path)
    colors = extract_colors(image_path)

    embedding = np.array(clip["embedding"], dtype=float)
    brand_raw = os.getenv("BRAND_EMBEDDING_JSON", "[]")
    try:
        brand_vector = np.array(json.loads(brand_raw), dtype=float)
    except json.JSONDecodeError:
        brand_vector = np.array([], dtype=float)

    score = _cosine_similarity(embedding, brand_vector)

    merged: dict[str, Any] = {}
    merged.update(ocr)
    merged.update(clip)
    merged.update(colors)
    merged["brand_consistency_score"] = score
    return merged
