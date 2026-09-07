import numpy as np
from typing import Tuple, Dict, Any


def estimate_head_center_offset(nose: Tuple[float, float], frame_shape: Tuple[int, int]) -> float:
    """
    Computes normalized horizontal offset of the nose landmark from the center of the frame (0.5).
    0.0 = perfectly centered.
    """
    center_x = 0.5
    offset = abs(nose[0] - center_x)
    return round(float(offset), 4)


def compute_head_stability(nose_positions: list) -> float:
    """
    Computes head stability (0 to 100%) based on horizontal and vertical displacement.
    """
    if len(nose_positions) < 2:
        return 100.0

    diffs = []
    for i in range(1, len(nose_positions)):
        dx = nose_positions[i][0] - nose_positions[i - 1][0]
        dy = nose_positions[i][1] - nose_positions[i - 1][1]
        dist = np.sqrt(dx**2 + dy**2)
        diffs.append(dist)

    avg_disp = float(np.mean(diffs))
    score = max(0.0, min(100.0, 100.0 - (avg_disp * 300.0)))
    return round(score, 1)
