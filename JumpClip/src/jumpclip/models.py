from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class ReferenceImage:
    provider: str
    identifier: str
    title: str
    image_url: str | None = None
    source_url: str | None = None
    license_name: str | None = None
    creator: str | None = None
    tags: list[str] = field(default_factory=list)
    width: int | None = None
    height: int | None = None
    local_path: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DesignProfile:
    grid_size: int
    palette: list[str]
    silhouette_coverage: float
    edge_density: float
    proportion_profile: dict[str, float]
    line_weight_profile: dict[str, float]
    grid_relativities: list[list[float]]
    providers: list[str]
    tags: list[str]
    source_count: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AnimationSpec:
    name: str
    frame_count: int
    motion: str
    silhouette_bias: float
    squash_stretch: float
    impact: float


@dataclass
class RenderRequest:
    character: str
    prompt: str
    animation: AnimationSpec
    canvas_size: int = 64
    upscale: int = 4
    output_path: Path | None = None
