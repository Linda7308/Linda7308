"""Biological interpretation for electrophoresis gel analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class CalibrationResult:
    """Linear calibration on log10(size) versus migration distance."""

    slope: float
    intercept: float
    r2: float
    points_used: int


class CalibrationError(Exception):
    """Raised when ladder-based calibration cannot be computed."""


def _fit_log_linear(distances_px: np.ndarray, sizes: np.ndarray) -> CalibrationResult:
    """Fit log10(size) = slope * distance + intercept."""
    if len(distances_px) < 2 or len(sizes) < 2:
        raise CalibrationError("At least two ladder bands are required for calibration.")

    x = distances_px.astype(float)
    y = np.log10(sizes.astype(float))

    slope, intercept = np.polyfit(x, y, deg=1)
    y_pred = slope * x + intercept

    ss_res = float(np.sum((y - y_pred) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    return CalibrationResult(float(slope), float(intercept), float(r2), int(len(x)))


def _estimate_size(distance_px: float, calibration: CalibrationResult) -> float:
    """Estimate fragment/protein size from migration distance."""
    return float(10 ** (calibration.slope * float(distance_px) + calibration.intercept))


def _lane_quality(bands: list[dict[str, Any]]) -> tuple[str, list[str]]:
    """Assign lane status with simple explainable criteria."""
    notes: list[str] = []
    if not bands:
        return "ratée", ["Aucune bande détectée."]

    confidences = np.array([float(b.get("confidence", 0.0)) for b in bands], dtype=float)
    thickness = np.array([float(b.get("thickness_px", 0.0)) for b in bands], dtype=float)

    mean_conf = float(np.mean(confidences))
    median_thickness = float(np.median(thickness))

    if mean_conf < 0.2:
        notes.append("Bandes très faibles (confiance moyenne basse).")
    if median_thickness > 18:
        notes.append("Bandes épaisses/traînées possibles (smear).")
    if len(bands) == 1:
        notes.append("Une seule bande détectée.")

    if mean_conf < 0.2 or (len(bands) == 0):
        return "ratée", notes
    if mean_conf < 0.45 or median_thickness > 18 or len(bands) < 2:
        return "moyenne", notes
    return "réussie", notes


def interpret_gel(
    lanes: list[dict[str, Any]],
    *,
    gel_type: str,
    ladder_lane_id: int,
    ladder_sizes: list[float],
) -> dict[str, Any]:
    """Calibrate with ladder and estimate sizes for each lane band.

    Args:
        lanes: Lane list produced by image processing module.
        gel_type: "agarose" or "sds-page".
        ladder_lane_id: Lane identifier containing size marker.
        ladder_sizes: Known marker sizes (bp for agarose, kDa for SDS-PAGE).
    """
    if not lanes:
        raise CalibrationError("No lanes available for interpretation.")
    if not ladder_sizes:
        raise CalibrationError("Empty ladder sizes list.")

    lane_map = {int(l["lane_id"]): l for l in lanes}
    if ladder_lane_id not in lane_map:
        raise CalibrationError(f"Ladder lane {ladder_lane_id} not found among detected lanes.")

    ladder_lane = lane_map[ladder_lane_id]
    ladder_bands = sorted(ladder_lane.get("bands", []), key=lambda b: float(b["y"]))
    if len(ladder_bands) < 2:
        raise CalibrationError("Not enough ladder bands detected for calibration.")

    # Pair ladder bands with known ladder sizes.
    # Top bands (small y) correspond to larger fragments/proteins.
    known_sizes_desc = sorted([float(x) for x in ladder_sizes], reverse=True)
    n = min(len(ladder_bands), len(known_sizes_desc))
    used_bands = ladder_bands[:n]
    used_sizes = np.array(known_sizes_desc[:n], dtype=float)
    used_distances = np.array([float(b["y"]) for b in used_bands], dtype=float)

    calibration = _fit_log_linear(used_distances, used_sizes)

    size_key = "size_bp" if gel_type == "agarose" else "mass_kda"
    all_statuses: list[str] = []

    interpreted_lanes: list[dict[str, Any]] = []
    for lane in lanes:
        lane_copy = dict(lane)
        lane_bands = [dict(b) for b in lane.get("bands", [])]

        for band in lane_bands:
            estimate = _estimate_size(float(band["y"]), calibration)
            band[size_key] = round(estimate, 2)

        lane_status, notes = _lane_quality(lane_bands)
        lane_copy["bands"] = lane_bands
        lane_copy["status"] = lane_status
        lane_copy["notes"] = notes
        interpreted_lanes.append(lane_copy)
        all_statuses.append(lane_status)

    if "ratée" in all_statuses:
        global_status = "moyenne"
    elif all(s == "réussie" for s in all_statuses):
        global_status = "réussie"
    else:
        global_status = "moyenne"

    return {
        "status": global_status,
        "gel_type": gel_type,
        "ladder_lane_id": ladder_lane_id,
        "calibration": {
            "model": "log10(size)=a*distance+b",
            "slope": round(calibration.slope, 6),
            "intercept": round(calibration.intercept, 6),
            "r2": round(calibration.r2, 4),
            "points_used": calibration.points_used,
        },
        "size_unit": "bp" if gel_type == "agarose" else "kDa",
        "lanes": interpreted_lanes,
    }


def build_report_stub() -> dict:
    """Backward-compatible placeholder, kept for incremental workflow support."""
    return {
        "status": "not_implemented",
        "message": "Biological interpretation will be implemented in the next steps.",
    }
