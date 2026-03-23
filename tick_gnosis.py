from __future__ import annotations

from dataclasses import dataclass, field


def _clamp(value: float, minimum: float, maximum: float) -> float:
    if value < minimum:
        return minimum
    if value > maximum:
        return maximum
    return value


@dataclass(slots=True)
class TickGnosisSnapshot:
    module_id: str
    tick: int
    frame_delta_ms: float
    entity_count: int
    energy_total: float
    anchor_scale_constant: float
    recursion_depth: float
    camera_coherency: float
    sensory_entropy: float
    frame_buffer_relativity: float
    consensus_render_bias: float
    mitigation_bias: float
    moderation_bias: float
    modulation_bias: float


@dataclass(slots=True)
class TickGnosisState:
    module_id: str
    anchor_scale_constant: float = 1.0
    camera_coherency: float = 0.82
    frame_buffer_relativity: float = 0.78
    consensus_render_bias: float = 0.74
    mitigation_bias: float = 0.68
    moderation_bias: float = 0.66
    modulation_bias: float = 0.72
    sensory_entropy: float = 0.28
    last_snapshot: TickGnosisSnapshot | None = None
    history: list[TickGnosisSnapshot] = field(default_factory=list)

    def capture(
        self,
        *,
        tick: int,
        frame_delta_ms: float,
        entity_count: int,
        energy_total: float,
        camera_motion: float,
        input_pressure: float,
        recursion_depth: float,
    ) -> dict:
        safe_entity_count = max(1, entity_count)
        normalized_energy = energy_total / float(safe_entity_count)
        motion_bias = abs(camera_motion) * 0.18
        pressure_bias = abs(input_pressure) * 0.12
        recursion_bias = max(0.0, recursion_depth - 1.0) * 0.06

        self.anchor_scale_constant = _clamp(1.0 + normalized_energy * 0.0025 + recursion_bias, 0.82, 2.4)
        self.camera_coherency = _clamp(0.92 - motion_bias - pressure_bias * 0.4 + recursion_bias * 0.3, 0.24, 0.98)
        self.sensory_entropy = _clamp(0.18 + motion_bias + pressure_bias + recursion_bias * 0.5, 0.08, 0.96)
        self.frame_buffer_relativity = _clamp(0.58 + self.camera_coherency * 0.24 + recursion_bias * 0.3, 0.2, 1.12)
        self.consensus_render_bias = _clamp(0.44 + self.camera_coherency * 0.4, 0.2, 1.0)
        self.mitigation_bias = _clamp(0.38 + (1.0 - self.sensory_entropy) * 0.46, 0.15, 1.0)
        self.moderation_bias = _clamp(0.36 + self.frame_buffer_relativity * 0.4, 0.18, 1.0)
        self.modulation_bias = _clamp(0.34 + self.anchor_scale_constant * 0.25, 0.2, 1.0)

        snapshot = TickGnosisSnapshot(
            module_id=self.module_id,
            tick=tick,
            frame_delta_ms=round(frame_delta_ms, 3),
            entity_count=entity_count,
            energy_total=round(energy_total, 3),
            anchor_scale_constant=round(self.anchor_scale_constant, 4),
            recursion_depth=round(recursion_depth, 3),
            camera_coherency=round(self.camera_coherency, 4),
            sensory_entropy=round(self.sensory_entropy, 4),
            frame_buffer_relativity=round(self.frame_buffer_relativity, 4),
            consensus_render_bias=round(self.consensus_render_bias, 4),
            mitigation_bias=round(self.mitigation_bias, 4),
            moderation_bias=round(self.moderation_bias, 4),
            modulation_bias=round(self.modulation_bias, 4),
        )
        self.last_snapshot = snapshot
        self.history.append(snapshot)
        if len(self.history) > 16:
            self.history.pop(0)
        return {
            'module_id': snapshot.module_id,
            'tick': snapshot.tick,
            'frame_delta_ms': snapshot.frame_delta_ms,
            'entity_count': snapshot.entity_count,
            'energy_total': snapshot.energy_total,
            'anchor_scale_constant': snapshot.anchor_scale_constant,
            'recursion_depth': snapshot.recursion_depth,
            'camera_coherency': snapshot.camera_coherency,
            'sensory_entropy': snapshot.sensory_entropy,
            'frame_buffer_relativity': snapshot.frame_buffer_relativity,
            'consensus_render_bias': snapshot.consensus_render_bias,
            'mitigation_bias': snapshot.mitigation_bias,
            'moderation_bias': snapshot.moderation_bias,
            'modulation_bias': snapshot.modulation_bias,
        }


def build_tick_gnosis_frame(
    module_id: str,
    *,
    tick: int,
    frame_delta_ms: float,
    entity_count: int,
    energy_total: float,
    camera_motion: float,
    input_pressure: float,
    recursion_depth: float,
) -> dict:
    state = TickGnosisState(module_id)
    return state.capture(
        tick=tick,
        frame_delta_ms=frame_delta_ms,
        entity_count=entity_count,
        energy_total=energy_total,
        camera_motion=camera_motion,
        input_pressure=input_pressure,
        recursion_depth=recursion_depth,
    )