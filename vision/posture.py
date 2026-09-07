import numpy as np
from typing import Dict, Any, Optional, Tuple


def calculate_shoulder_alignment(left_shoulder: Tuple[float, float], right_shoulder: Tuple[float, float]) -> float:
    """
    Calculates the angle (in degrees) of the shoulder line relative to the horizontal axis.
    An ideal upright sitting posture has an angle close to 0 degrees.
    """
    dx = right_shoulder[0] - left_shoulder[0]
    dy = right_shoulder[1] - left_shoulder[1]
    if dx == 0:
        return 90.0
    angle_rad = np.arctan(abs(dy) / abs(dx))
    angle_deg = float(np.degrees(angle_rad))
    return angle_deg


def compute_posture_stability_score(shoulder_angles: list) -> float:
    """
    Computes a 0-100% stability score based on standard deviation of shoulder angles across frames.
    Low variance = high stability.
    """
    if not shoulder_angles:
        return 100.0
    std = float(np.std(shoulder_angles))
    # Score decreases as angular variance increases
    score = max(0.0, min(100.0, 100.0 - (std * 5.0)))
    return round(score, 1)
