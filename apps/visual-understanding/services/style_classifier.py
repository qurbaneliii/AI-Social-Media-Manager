# FILE: apps/visual-understanding/services/style_classifier.py
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import open_clip
import torch
from PIL import Image


class StyleClassifier:
    def __init__(self, centroid_file: str) -> None:
        self.model, _, self.preprocess = open_clip.create_model_and_transforms("ViT-B-32", pretrained="openai")
        self.tokenizer = open_clip.get_tokenizer("ViT-B-32")
        self.centroids = json.loads(Path(centroid_file).read_text(encoding="utf-8"))

    async def process(self, image: Image.Image) -> tuple[str, float]:
        """Compute CLIP embedding and match against configured style centroids by cosine similarity."""
        image_tensor = self.preprocess(image).unsqueeze(0)
        with torch.no_grad():
            emb = self.model.encode_image(image_tensor).cpu().numpy()[0]
        emb = emb / (np.linalg.norm(emb) + 1e-8)

        best_label = "corporate"
        best_score = -1.0
        for label, vec in self.centroids.items():
            centroid = np.array(vec, dtype=np.float32)
            centroid = centroid / (np.linalg.norm(centroid) + 1e-8)
            score = float(np.dot(emb[: centroid.shape[0]], centroid))
            if score > best_score:
                best_score = score
                best_label = label
        return best_label, max(0.0, min(1.0, (best_score + 1) / 2))
