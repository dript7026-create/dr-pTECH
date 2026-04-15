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
    lift_scale: float = 1.0


@dataclass
class LearningInfluence:
    subject: str | None = None
    godai: dict[str, float] = field(default_factory=dict)
    style_signals: dict[str, object] = field(default_factory=dict)
    motion_signals: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RenderRequest:
    character: str
    prompt: str
    animation: AnimationSpec
    canvas_size: int = 64
    upscale: int = 4
    output_path: Path | None = None
    art_preset: str | None = None
    style_family: str | None = None
    silhouette_emphasis: float | None = None
    texture_detail: float | None = None
    palette_limit: int | None = None
    cel_shading: float | None = None
    outline_weight: float | None = None
    accessory_density: float | None = None
    tracing_bias: float | None = None
    motion_silhouette_bias: float | None = None
    motion_squash_stretch: float | None = None
    motion_impact: float | None = None
    motion_lift: float | None = None
    learning_profile: str | None = None
    learning_weight: float | None = None


@dataclass
class DesignDirective:
    art_preset: str | None
    style_family: str
    silhouette_emphasis: float
    texture_detail: float
    palette_limit: int
    shading_bands: int
    outline_weight: float
    accessory_density: float
    cel_shading: float
    tracing_bias: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GamePipelineConfig:
    pipeline_name: str = "generic-2d"
    engine: str = "custom"
    target_frame_size: int = 64
    pixels_per_unit: int = 16
    frame_duration_ms: int = 90
    max_sheet_width: int = 1024
    pivot_x: float = 0.5
    pivot_y: float = 1.0
    emit_preview_gif: bool = True
    emit_frame_sequence: bool = False
    emit_visual_regression: bool = False
    visual_regression_columns: int = 4
    emitters: list[str] = field(default_factory=lambda: ["generic"])

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class BundleJob:
    name: str
    character: str
    animation: str
    prompt: str
    design_template: str | None = None
    motion_template: str | None = None
    art_preset: str | None = None
    profile: str | None = None
    grid_size: int | None = None
    download_dir: str | None = None
    canvas_size: int | None = None
    upscale: int | None = None
    style_family: str | None = None
    silhouette_emphasis: float | None = None
    texture_detail: float | None = None
    palette_limit: int | None = None
    cel_shading: float | None = None
    outline_weight: float | None = None
    accessory_density: float | None = None
    tracing_bias: float | None = None
    motion_silhouette_bias: float | None = None
    motion_squash_stretch: float | None = None
    motion_impact: float | None = None
    motion_lift: float | None = None
    learning_profile: str | None = None
    learning_weight: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)
