from __future__ import annotations


def parallax_screen_x(world_x: float, camera_x: float, width: float, parallax: float) -> float:
    relative = (world_x - camera_x) * parallax
    return (width / 2.0) + relative


def lane_screen_y(height: float, lane_index: int, lane_count: int = 4) -> float:
    baseline = height * 0.66
    spacing = 26.0
    offset = (lane_count - lane_index - 1) * spacing
    return baseline - offset


def depth_scale(depth_bias: float) -> float:
    return max(0.55, 1.0 - (depth_bias * 0.08))


def sideview_screen_y(height: float, world_y: float, ground_ratio: float = 0.72) -> float:
    ground_line = height * ground_ratio
    return ground_line - (world_y * 28.0)