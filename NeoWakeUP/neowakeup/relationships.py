"""
Egosphere-inspired interpersonal modeling for NeoWakeUP.

This stays lightweight and portable on purpose. The model translates repeated
interactions into relationship traits the AI can reuse while choosing actions
or exporting learning state.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import time


@dataclass
class RelationshipNode:
    name: str
    archetype: str
    trust: float = 0.0
    rivalry: float = 0.5
    fear: float = 0.25
    dominance: float = 0.0
    adaptability: float = 0.5
    reciprocity: float = 0.5
    interactions: int = 0
    last_event_ts: float = 0.0


class EgoSphereSocialModel:
    def __init__(self, sensitivity: float = 1.0):
        self.sensitivity = max(0.1, float(sensitivity))
        self._nodes: dict[str, RelationshipNode] = {}

    def _clamp(self, value: float, low: float = 0.0, high: float = 1.0) -> float:
        return max(low, min(high, float(value)))

    def ensure(self, name: str, archetype: str = "unknown") -> RelationshipNode:
        node = self._nodes.get(name)
        if node is None:
            node = RelationshipNode(name=name, archetype=archetype, last_event_ts=time.time())
            self._nodes[name] = node
        elif archetype and node.archetype == "unknown":
            node.archetype = archetype
        return node

    def observe_action(
        self,
        name: str,
        archetype: str,
        action: str,
        threat: float,
        self_progress: float,
        objective_progress: float,
    ) -> dict:
        node = self.ensure(name, archetype)
        node.interactions += 1
        node.last_event_ts = time.time()
        stress_intensity = self._clamp(0.35 + 0.65 * threat) * self.sensitivity
        vulnerability = self._clamp(1.0 - float(self_progress))
        finishing_window = self._clamp(1.0 - float(objective_progress))

        if action == "ATTACK":
            node.dominance = self._clamp(node.dominance + 0.035 * (0.5 + finishing_window))
            node.rivalry = self._clamp(node.rivalry + 0.02 * stress_intensity)
            node.fear = self._clamp(node.fear - 0.015 * (1.0 - vulnerability))
        elif action == "DODGE":
            node.fear = self._clamp(node.fear + 0.025 * stress_intensity)
            node.adaptability = self._clamp(node.adaptability + 0.02 * stress_intensity)
        elif action in ("LEFT", "RIGHT"):
            node.adaptability = self._clamp(node.adaptability + 0.015 * stress_intensity)
            node.reciprocity = self._clamp(node.reciprocity + 0.01 * (1.0 - threat))
        elif action == "WAIT":
            node.trust = self._clamp(node.trust - 0.01 * stress_intensity)
            node.fear = self._clamp(node.fear + 0.01 * stress_intensity)
        elif action == "NANO":
            node.trust = self._clamp(node.trust + 0.015 * (1.0 - vulnerability))
            node.dominance = self._clamp(node.dominance + 0.02 * finishing_window)

        return asdict(node)

    def observe_outcome(self, name: str, archetype: str, win: bool) -> dict:
        node = self.ensure(name, archetype)
        node.interactions += 1
        node.last_event_ts = time.time()
        if win:
            node.dominance = self._clamp(node.dominance + 0.08)
            node.trust = self._clamp(node.trust + 0.04)
            node.fear = self._clamp(node.fear - 0.05)
            node.rivalry = self._clamp(node.rivalry + 0.03)
        else:
            node.dominance = self._clamp(node.dominance - 0.06)
            node.fear = self._clamp(node.fear + 0.07)
            node.adaptability = self._clamp(node.adaptability + 0.03)
            node.rivalry = self._clamp(node.rivalry + 0.04)
        return asdict(node)

    def snapshot(self, name: str, archetype: str = "unknown") -> dict:
        return asdict(self.ensure(name, archetype))

    def export_state(self) -> dict:
        return {
            "sensitivity": self.sensitivity,
            "nodes": {name: asdict(node) for name, node in self._nodes.items()},
        }

    def import_state(self, payload: dict) -> bool:
        try:
            nodes = payload.get("nodes", {})
            sensitivity = float(payload.get("sensitivity", 1.0))
        except (AttributeError, TypeError, ValueError):
            return False
        self.sensitivity = max(0.1, sensitivity)
        imported = {}
        for name, node_data in nodes.items():
            try:
                imported[name] = RelationshipNode(**node_data)
            except TypeError:
                continue
        self._nodes = imported
        return True