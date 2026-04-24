"""Image processing functions for electrophoresis gel analysis."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class LaneDetection:
    """Detected lane boundaries and confidence metrics."""

    lane_id: int
    x_start: int
    x_end: int
    center_x: int
    score: float


@dataclass
class BandDetection:
    """Detected band geometry and signal metrics."""

    lane_id: int
    band_id: int
    y: int
    thickness_px: int
    intensity: float
    confidence: float


def _moving_average(signal: np.ndarray, window_size: int) -> np.ndarray:
    """Compute a simple moving average for 1D signals."""
    if window_size <= 1:
        return signal.copy()
    kernel = np.ones(window_size, dtype=float) / float(window_size)
    return np.convolve(signal, kernel, mode="same")


def preprocess_image(
    image: np.ndarray,
    *,
    blur_kernel: int = 5,
    clahe_clip_limit: float = 2.5,
    clahe_grid_size: int = 8,
) -> np.ndarray:
    """Reduce noise and enhance local contrast for band visibility.

    Returns a uint8 grayscale image where brighter pixels indicate stronger signals.
    """
    if image.ndim != 2:
        raise ValueError("preprocess_image expects a 2D grayscale image.")

    img = image.astype(np.uint8)
    blur_kernel = max(1, int(blur_kernel) | 1)
    denoised = cv2.GaussianBlur(img, (blur_kernel, blur_kernel), 0)

    clahe = cv2.createCLAHE(clipLimit=clahe_clip_limit, tileGridSize=(clahe_grid_size, clahe_grid_size))
    enhanced = clahe.apply(denoised)

    # In many gel images bands are bright on dark background. We keep this convention.
    return enhanced


def detect_lanes(
    preprocessed: np.ndarray,
    *,
    smooth_window: int = 21,
    threshold_ratio: float = 0.35,
    min_lane_width: int = 12,
) -> list[LaneDetection]:
    """Detect lane regions from vertical intensity projection."""
    if preprocessed.ndim != 2:
        raise ValueError("detect_lanes expects a 2D grayscale image.")

    column_projection = preprocessed.mean(axis=0).astype(float)
    smooth_window = max(3, int(smooth_window) | 1)
    projection_smooth = _moving_average(column_projection, smooth_window)

    dynamic_floor = np.percentile(projection_smooth, 40)
    dynamic_peak = float(projection_smooth.max())
    threshold = dynamic_floor + threshold_ratio * (dynamic_peak - dynamic_floor)

    mask = projection_smooth >= threshold
    lanes: list[LaneDetection] = []
    start: int | None = None
    lane_id = 1

    for x, active in enumerate(mask):
        if active and start is None:
            start = x
        elif not active and start is not None:
            end = x - 1
            if end - start + 1 >= min_lane_width:
                segment = projection_smooth[start : end + 1]
                center = int((start + end) / 2)
                score = float((segment.mean() - dynamic_floor) / (dynamic_peak - dynamic_floor + 1e-6))
                lanes.append(LaneDetection(lane_id, start, end, center, max(0.0, min(1.0, score))))
                lane_id += 1
            start = None

    if start is not None:
        end = preprocessed.shape[1] - 1
        if end - start + 1 >= min_lane_width:
            segment = projection_smooth[start : end + 1]
            center = int((start + end) / 2)
            score = float((segment.mean() - dynamic_floor) / (dynamic_peak - dynamic_floor + 1e-6))
            lanes.append(LaneDetection(lane_id, start, end, center, max(0.0, min(1.0, score))))

    return lanes


def detect_bands_in_lane(
    preprocessed: np.ndarray,
    lane: LaneDetection,
    *,
    smooth_window: int = 11,
    min_prominence_ratio: float = 0.12,
    min_band_gap_px: int = 6,
) -> list[BandDetection]:
    """Detect bands in a lane by finding local maxima in vertical profiles."""
    roi = preprocessed[:, lane.x_start : lane.x_end + 1]
    profile = roi.mean(axis=1).astype(float)

    smooth_window = max(3, int(smooth_window) | 1)
    profile_smooth = _moving_average(profile, smooth_window)

    base = np.percentile(profile_smooth, 35)
    top = float(profile_smooth.max())
    min_height = base + min_prominence_ratio * (top - base)

    candidates: list[tuple[int, float]] = []
    for y in range(1, len(profile_smooth) - 1):
        prev_v = profile_smooth[y - 1]
        cur_v = profile_smooth[y]
        next_v = profile_smooth[y + 1]
        if cur_v >= prev_v and cur_v >= next_v and cur_v >= min_height:
            prominence = cur_v - max(base, min(prev_v, next_v))
            candidates.append((y, float(prominence)))

    candidates.sort(key=lambda it: it[0])

    # Non-maximum suppression by distance to avoid overcounting thick bands.
    selected: list[tuple[int, float]] = []
    for y, prom in candidates:
        if not selected or y - selected[-1][0] >= min_band_gap_px:
            selected.append((y, prom))
        elif prom > selected[-1][1]:
            selected[-1] = (y, prom)

    band_detections: list[BandDetection] = []
    for band_id, (y, prom) in enumerate(selected, start=1):
        peak = profile_smooth[y]
        half_height = base + 0.5 * (peak - base)

        top_y = y
        while top_y > 0 and profile_smooth[top_y] > half_height:
            top_y -= 1
        bottom_y = y
        while bottom_y < len(profile_smooth) - 1 and profile_smooth[bottom_y] > half_height:
            bottom_y += 1

        thickness = max(1, bottom_y - top_y)
        confidence = float(prom / (top - base + 1e-6))

        band_detections.append(
            BandDetection(
                lane_id=lane.lane_id,
                band_id=band_id,
                y=int(y),
                thickness_px=int(thickness),
                intensity=float(peak),
                confidence=max(0.0, min(1.0, confidence)),
            )
        )

    return band_detections


def detect_bands(preprocessed: np.ndarray, lanes: list[LaneDetection]) -> dict[int, list[BandDetection]]:
    """Run band detection for all lanes."""
    return {lane.lane_id: detect_bands_in_lane(preprocessed, lane) for lane in lanes}


def render_annotations(
    preprocessed: np.ndarray,
    lanes: list[LaneDetection],
    bands_by_lane: dict[int, list[BandDetection]],
) -> np.ndarray:
    """Render lane boxes and band markers on top of processed gel image."""
    canvas = cv2.cvtColor(preprocessed, cv2.COLOR_GRAY2BGR)

    for lane in lanes:
        cv2.rectangle(canvas, (lane.x_start, 0), (lane.x_end, preprocessed.shape[0] - 1), (0, 255, 255), 1)
        cv2.putText(
            canvas,
            f"L{lane.lane_id}",
            (lane.x_start, 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (0, 255, 255),
            1,
            cv2.LINE_AA,
        )

        for band in bands_by_lane.get(lane.lane_id, []):
            cv2.line(canvas, (lane.x_start, band.y), (lane.x_end, band.y), (0, 0, 255), 1)
            cv2.putText(
                canvas,
                f"B{band.band_id}",
                (lane.x_end + 2, max(10, band.y - 2)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.35,
                (255, 180, 0),
                1,
                cv2.LINE_AA,
            )

    return canvas
