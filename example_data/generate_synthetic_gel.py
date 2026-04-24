"""Generate a simple synthetic agarose gel image for manual testing.

Requires: numpy, opencv-python
"""

from __future__ import annotations

import cv2
import numpy as np


def draw_band(img: np.ndarray, x0: int, x1: int, y: int, intensity: int = 220, thickness: int = 3) -> None:
    cv2.rectangle(img, (x0, y - thickness), (x1, y + thickness), intensity, -1)


def main() -> None:
    h, w = 420, 560
    gel = np.zeros((h, w), dtype=np.uint8)

    lane_width = 45
    spacing = 25
    x_start = 40
    lanes = []
    for i in range(6):
        x0 = x_start + i * (lane_width + spacing)
        x1 = x0 + lane_width
        lanes.append((x0, x1))
        cv2.rectangle(gel, (x0, 20), (x1, h - 30), 30, -1)

    ladder_y = [70, 95, 120, 145, 170, 200, 235, 265, 300, 335, 365]
    for y in ladder_y:
        draw_band(gel, lanes[0][0] + 2, lanes[0][1] - 2, y, intensity=245, thickness=2)

    sample1 = [130, 210, 320]
    sample2 = [90, 180, 275, 350]
    sample3 = [160, 260]
    sample4 = [110, 190, 260, 340]
    sample5 = [140]

    for ys, lane in zip([sample1, sample2, sample3, sample4, sample5], lanes[1:]):
        for y in ys:
            draw_band(gel, lane[0] + 2, lane[1] - 2, y, intensity=230, thickness=3)

    noise = np.random.normal(0, 6, size=gel.shape).astype(np.int16)
    gel = np.clip(gel.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    cv2.imwrite("example_data/synthetic_gel.png", gel)
    print("[OK] Generated example_data/synthetic_gel.png")


if __name__ == "__main__":
    main()
