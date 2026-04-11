# FILE: apps/visual-understanding/services/color_extractor.py
from __future__ import annotations

import cv2
import numpy as np
from PIL import Image


class ColorExtractor:
    def __init__(self, k: int = 6) -> None:
        self.k = k

    async def process(self, image: Image.Image) -> list[tuple[str, float]]:
        """Cluster colors with OpenCV k-means in LAB and return ratios sorted descending."""
        rgb = np.array(image)
        lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
        pixels = lab.reshape((-1, 3)).astype(np.float32)

        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.2)
        _, labels, centers = cv2.kmeans(pixels, self.k, None, criteria, 10, cv2.KMEANS_PP_CENTERS)

        counts = np.bincount(labels.flatten(), minlength=self.k).astype(np.float64)
        ratios = counts / counts.sum()

        rgb_centers = cv2.cvtColor(centers.reshape((1, self.k, 3)).astype(np.uint8), cv2.COLOR_LAB2RGB).reshape((self.k, 3))
        items = []
        for idx, ratio in sorted(enumerate(ratios.tolist()), key=lambda x: x[1], reverse=True):
            r, g, b = rgb_centers[idx]
            items.append((f"#{int(r):02X}{int(g):02X}{int(b):02X}", float(ratio)))
        return items
