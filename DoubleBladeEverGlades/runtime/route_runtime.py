from __future__ import annotations

from typing import Any


def build_route_runtime(manifest: dict[str, Any]) -> dict[str, Any]:
    rootknots = manifest["progression"]["rootknots"]
    segments = []
    total_distance = 0.0
    previous = None
    for rootknot in rootknots:
        if previous is not None:
            start = previous["diamond_position"]
            end = rootknot["diamond_position"]
            distance = ((end["x"] - start["x"]) ** 2 + (end["y"] - start["y"]) ** 2) ** 0.5
            total_distance += distance
            segments.append(
                {
                    "id": f"segment_{previous['id']}_{rootknot['id']}",
                    "from": previous["id"],
                    "to": rootknot["id"],
                    "distance": round(distance, 2),
                    "pressure": round((previous["progress"] + rootknot["progress"]) / 2, 3),
                    "encounter_lane": "inner" if rootknot["progress"] < 0.5 else "outer",
                }
            )
        previous = rootknot

    return {
        "world_shape": manifest["project"]["world_shape"],
        "total_world_area_sqft": manifest["project"]["world_area_sqft"],
        "route_total_distance": round(total_distance, 2),
        "segments": segments,
        "rootknot_order": [rootknot["id"] for rootknot in rootknots],
    }
