"""Utility helpers for electrophoresis gel analysis."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


class GelAnalysisError(Exception):
    """Base exception for analysis failures."""


class ImageLoadError(GelAnalysisError):
    """Raised when an image cannot be loaded."""


@dataclass
class AnalysisWarning:
    """Structured warning emitted during processing."""

    code: str
    message: str


def ensure_output_dir(path: str | Path) -> Path:
    """Create output directory if needed and return resolved Path."""
    output_path = Path(path)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def load_image_grayscale(image_path: str | Path):
    """Load an image in grayscale mode with clear error reporting."""
    import cv2

    image_path = Path(image_path)
    if not image_path.exists():
        raise ImageLoadError(f"Image file not found: {image_path}")

    image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ImageLoadError(
            f"Unable to decode image: {image_path}. Supported formats include PNG/JPG/TIFF."
        )

    return image


def save_json(data: dict[str, Any], output_path: str | Path) -> None:
    """Save dictionary content as pretty-printed JSON."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def save_text_report(lines: list[str], output_path: str | Path) -> None:
    """Save a plain text report from line items."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def normalize_to_uint8(image):
    """Normalize image values to uint8 [0,255] for safe visualization."""
    import cv2

    if image.size == 0:
        raise GelAnalysisError("Cannot normalize an empty image array.")

    normalized = cv2.normalize(image, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
    return normalized.astype("uint8")
