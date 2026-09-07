import numpy as np
from typing import List, Tuple, Dict, Any


def calculate_motion_magnitude(landmarks_sequence: List[np.ndarray]) -> float:
    """
    Computes the average Euclidean displacement of key upper-body landmarks across consecutive frames.
    """
    if len(landmarks_sequence) < 2:
        return 0.0

    displacements = []
    for i in range(1, len(landmarks_sequence)):
        diff = landmarks_sequence[i] - landmarks_sequence[i - 1]
        dist = np.linalg.norm(diff)
        displacements.append(dist)

    avg_mag = float(np.mean(displacements))
    return round(avg_mag, 4)


def calculate_movement_frequency(displacements: List[float], threshold: float = 0.02, fps: float = 30.0) -> float:
    """
    Calculates movement frequency: number of significant movement shifts per second.
    """
    if not displacements:
        return 0.0

    shifts = sum(1 for d in displacements if d > threshold)
    duration_sec = len(displacements) / fps
    if duration_sec == 0:
        return 0.0

    freq = shifts / duration_sec
    return round(float(freq), 2)
