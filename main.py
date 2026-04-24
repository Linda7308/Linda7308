"""Main entry point for electrophoresis gel analysis (step-wise implementation)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from utils import ImageLoadError, ensure_output_dir, load_image_grayscale, save_json, save_text_report


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Electrophoresis gel analyzer")
    parser.add_argument("--image", required=False, help="Path to gel image")
    parser.add_argument("--output-dir", default="outputs", help="Directory to store reports")
    parser.add_argument(
        "--gel-type",
        choices=["agarose", "sds-page"],
        default="agarose",
        help="Type of gel to interpret",
    )
    parser.add_argument(
        "--ladder-lane",
        type=int,
        default=1,
        help="Lane ID containing ladder/marker bands (1-indexed).",
    )
    parser.add_argument(
        "--ladder-sizes",
        default="10000,8000,6000,5000,4000,3000,2000,1500,1000,700,500",
        help="Comma-separated ladder sizes (bp for agarose, kDa for SDS-PAGE).",
    )
    parser.add_argument(
        "--config",
        help="Optional JSON config file. If provided, values override CLI defaults.",
    )
    return parser.parse_args()


def _parse_ladder_sizes(raw: str) -> list[float]:
    values = [x.strip() for x in raw.split(",") if x.strip()]
    if not values:
        raise ValueError("No ladder sizes provided.")
    return [float(v) for v in values]


def _apply_config(args: argparse.Namespace) -> argparse.Namespace:
    if not args.config:
        return args

    config_path = Path(args.config)
    if not config_path.exists():
        raise ValueError(f"Config file not found: {config_path}")

    payload = json.loads(config_path.read_text(encoding="utf-8"))
    for key in ["image", "output_dir", "gel_type", "ladder_lane", "ladder_sizes"]:
        if key in payload:
            setattr(args, key if key != "output_dir" else "output_dir", payload[key])
    return args


def run_pipeline(
    image_path: str,
    output_dir: str,
    gel_type: str,
    ladder_lane: int,
    ladder_sizes: list[float],
) -> tuple[dict, Path]:
    """Run the full pipeline up to biological interpretation."""
    from analysis import interpret_gel
    from image_processing import detect_bands, detect_lanes, preprocess_image, render_annotations
    import cv2

    raw_image = load_image_grayscale(image_path)
    processed_image = preprocess_image(raw_image)

    lanes = detect_lanes(processed_image)
    bands_by_lane = detect_bands(processed_image, lanes)

    lane_payload = [
        {
            "lane_id": lane.lane_id,
            "x_start": lane.x_start,
            "x_end": lane.x_end,
            "center_x": lane.center_x,
            "detection_score": round(lane.score, 3),
            "bands": [
                {
                    "band_id": band.band_id,
                    "y": band.y,
                    "thickness_px": band.thickness_px,
                    "intensity": round(band.intensity, 3),
                    "confidence": round(band.confidence, 3),
                }
                for band in bands_by_lane.get(lane.lane_id, [])
            ],
        }
        for lane in lanes
    ]

    interpretation = interpret_gel(
        lane_payload,
        gel_type=gel_type,
        ladder_lane_id=ladder_lane,
        ladder_sizes=ladder_sizes,
    )
    interpretation["input_image"] = str(Path(image_path))
    interpretation["image_shape"] = list(processed_image.shape)
    interpretation["lane_count"] = len(lanes)

    annotated = render_annotations(processed_image, lanes, bands_by_lane)
    output_dir_path = Path(output_dir)
    annotated_path = output_dir_path / "annotated_gel.png"
    cv2.imwrite(str(annotated_path), annotated)

    return interpretation, annotated_path


def main() -> int:
    """CLI wrapper with explicit error handling."""
    args = parse_args()

    try:
        args = _apply_config(args)
        if not args.image:
            raise ValueError("No input image provided. Use --image or --config.")

        output_dir = ensure_output_dir(args.output_dir)
        ladder_sizes = _parse_ladder_sizes(args.ladder_sizes)
        report, annotated_path = run_pipeline(
            args.image,
            args.output_dir,
            args.gel_type,
            args.ladder_lane,
            ladder_sizes,
        )
    except (ValueError, ModuleNotFoundError) as exc:
        print(f"[ERROR] {exc}")
        return 3
    except ImageLoadError as exc:
        print(f"[ERROR] {exc}")
        return 2
    except Exception as exc:  # noqa: BLE001 - keep user-friendly CLI errors
        print(f"[ERROR] Unexpected failure: {exc}")
        return 1

    report_json_path = output_dir / "report.json"
    report_txt_path = output_dir / "report.txt"

    save_json(report, report_json_path)

    lane_lines = []
    for lane in report["lanes"]:
        lane_lines.append(
            f"Lane {lane['lane_id']}: {lane['status']} (bands={len(lane.get('bands', []))}, score={lane.get('detection_score', 'NA')})"
        )

    save_text_report(
        [
            "Electrophoresis analysis report (step 6 example-ready)",
            f"Input image: {report['input_image']}",
            f"Gel type: {report['gel_type']}",
            f"Image shape: {report['image_shape']}",
            f"Lanes detected: {report['lane_count']}",
            f"Global status: {report['status']}",
            f"Calibration R²: {report['calibration']['r2']}",
            *lane_lines,
            f"Annotated image: {annotated_path}",
        ],
        report_txt_path,
    )

    print(f"[OK] Report JSON: {report_json_path}")
    print(f"[OK] Report TXT: {report_txt_path}")
    print(f"[OK] Annotated image: {annotated_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
