from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class RootKnotVisit:
    rootknot_id: str
    progress: float


@dataclass
class GameState:
    run_seed: int
    active_rootknot_id: str
    previous_rootknot_id: str | None
    distance_to_nearest_rootknot: float
    distance_from_previous_rootknot: float
    blade_ids: list[str] = field(default_factory=list)
    defeated_enemy_ids: list[str] = field(default_factory=list)
    rootknot_visits: list[RootKnotVisit] = field(default_factory=list)


class SaveRuntime:
    def __init__(self, save_root: Path) -> None:
        self.save_root = Path(save_root)
        self.save_root.mkdir(parents=True, exist_ok=True)
        self.autosave_path = self.save_root / "autosave.json"

    def save(self, slot_name: str, state: GameState) -> Path:
        path = self.save_root / f"{slot_name}.json"
        payload = asdict(state)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def load(self, slot_name: str) -> GameState:
        path = self.save_root / f"{slot_name}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["rootknot_visits"] = [RootKnotVisit(**visit) for visit in payload.get("rootknot_visits", [])]
        return GameState(**payload)

    def autosave(self, state: GameState) -> Path:
        payload = asdict(state)
        self.autosave_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return self.autosave_path

    def save_at_rootknot(self, state: GameState, rootknot_id: str, progress: float) -> Path:
        updated_visits = [visit for visit in state.rootknot_visits if visit.rootknot_id != rootknot_id]
        updated_visits.append(RootKnotVisit(rootknot_id=rootknot_id, progress=progress))
        updated_state = GameState(
            run_seed=state.run_seed,
            active_rootknot_id=rootknot_id,
            previous_rootknot_id=state.active_rootknot_id,
            distance_to_nearest_rootknot=0.0,
            distance_from_previous_rootknot=state.distance_from_previous_rootknot,
            blade_ids=state.blade_ids,
            defeated_enemy_ids=state.defeated_enemy_ids,
            rootknot_visits=updated_visits,
        )
        return self.autosave(updated_state)