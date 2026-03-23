from __future__ import annotations

from ctypes import CDLL, POINTER, Structure, byref, c_char_p, c_double, c_int, c_size_t
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess


@dataclass(slots=True)
class EncounterReading:
    pressure: float
    focus_enemy: str | None
    recommended_style: str
    source: str = "heuristic"


class _Tier(Structure):
    _fields_ = [("weight", c_double)]


class _Priors(Structure):
    _fields_ = [
        ("pattern_trust", c_double),
        ("bias_action", c_double * 3),
    ]


class _Experience(Structure):
    _fields_ = [("action", c_int), ("reward", c_double), ("context", c_int)]


class _Memory(Structure):
    _fields_ = [("items", POINTER(_Experience)), ("count", c_size_t), ("capacity", c_size_t)]


class _Agent(Structure):
    _fields_ = [
        ("name", c_char_p),
        ("id", _Tier),
        ("ego", _Tier),
        ("superego", _Tier),
        ("priors", _Priors),
        ("memory", _Memory),
    ]


class HeuristicEgoSphereBridge:
    """Pure Python fallback when the native EgoSphere bridge is unavailable."""

    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}

    def read_encounter(self, player_state, enemies) -> EncounterReading:
        living = [enemy for enemy in enemies if enemy.hp > 0]
        if not living:
            return EncounterReading(pressure=0.0, focus_enemy=None, recommended_style="advance", source="heuristic")

        focus = min(living, key=lambda enemy: abs(enemy.x - player_state.x))
        average_aggression = sum(enemy.aggression for enemy in living) / max(1, len(living))
        proximity = max(0.0, 1.0 - (abs(focus.x - player_state.x) / 30.0))
        tension_weight = min(1.0, player_state.bond_tension / 100.0)
        pressure = round((average_aggression * 0.45) + (proximity * 0.35) + (tension_weight * 0.20), 3)

        if player_state.bond_tension >= 70:
            style = "stabilize"
        elif focus.posture <= 20:
            style = "commit"
        elif proximity >= 0.7:
            style = "dodge_counter"
        else:
            style = "probe"
        return EncounterReading(pressure=pressure, focus_enemy=focus.name, recommended_style=style, source="heuristic")


class NativeEgoSphereBridge:
    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}
        self.workspace_root = Path(__file__).resolve().parents[2]
        self.egosphere_root = self.workspace_root / "egosphere"
        self.library_path = self._resolve_library_path()
        self.dll = self._load_or_build_library(self.library_path)
        self._configure_api()
        self.agent = _Agent()
        agent_name = str(self.config.get("agent_name", "illusioncanvas_agent"))
        self.dll.egosphere_init_agent(byref(self.agent), agent_name.encode("utf-8"))

    def _resolve_library_path(self) -> Path:
        configured = self.config.get("library_path")
        if configured:
            return Path(configured)
        return self.egosphere_root / "egosphere.dll"

    def _load_or_build_library(self, library_path: Path) -> CDLL:
        if not library_path.exists() and self.config.get("auto_build", True):
            self._build_library(library_path)
        return CDLL(str(library_path))

    def _build_library(self, library_path: Path) -> None:
        compiler = shutil.which("gcc") or shutil.which("clang")
        if compiler is None:
            raise RuntimeError("No C compiler available to build egosphere.dll")
        source_path = self.egosphere_root / "egosphere.c"
        command = [
            compiler,
            "-std=c11",
            "-O2",
            "-shared",
            "-Wl,--export-all-symbols",
            "-o",
            str(library_path),
            str(source_path),
            "-lm",
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout or "Failed to build egosphere.dll")

    def _configure_api(self) -> None:
        self.dll.egosphere_init_agent.argtypes = [POINTER(_Agent), c_char_p]
        self.dll.egosphere_init_agent.restype = None
        self.dll.egosphere_free_agent.argtypes = [POINTER(_Agent)]
        self.dll.egosphere_free_agent.restype = None
        self.dll.egosphere_decide_action.argtypes = [POINTER(_Agent), c_int]
        self.dll.egosphere_decide_action.restype = c_int
        self.dll.egosphere_update.argtypes = [POINTER(_Agent), c_int, c_double, c_int]
        self.dll.egosphere_update.restype = None

    def _pressure(self, player_state, enemies) -> tuple[float, object | None]:
        living = [enemy for enemy in enemies if enemy.hp > 0]
        if not living:
            return 0.0, None
        focus = min(living, key=lambda enemy: abs(enemy.x - player_state.x))
        proximity = max(0.0, 1.0 - (abs(focus.x - player_state.x) / 30.0))
        aggression = sum(enemy.aggression for enemy in living) / max(1, len(living))
        weakened = sum((1.0 - (enemy.hp / max(1, enemy.max_hp))) for enemy in living) / len(living)
        tension = min(1.0, player_state.bond_tension / 100.0)
        pressure = round((aggression * 0.4) + (proximity * 0.35) + (tension * 0.15) + ((1.0 - weakened) * 0.1), 3)
        return pressure, focus

    def _compute_reward(self, player_state, enemies) -> float:
        living = [enemy for enemy in enemies if enemy.hp > 0]
        if not living:
            return 0.35 if player_state.bond_tension < 45 else 0.1
        player_health_ratio = player_state.hp / max(1, player_state.max_hp)
        enemy_posture_ratio = sum((1.0 - (enemy.posture / 100.0)) for enemy in living) / len(living)
        enemy_health_ratio = sum((1.0 - (enemy.hp / max(1, enemy.max_hp))) for enemy in living) / len(living)
        tension_penalty = player_state.bond_tension / 100.0
        reward = (player_health_ratio * 0.45) + (enemy_posture_ratio * 0.30) + (enemy_health_ratio * 0.20) - (tension_penalty * 0.35)
        return max(-1.0, min(1.0, reward))

    def read_encounter(self, player_state, enemies) -> EncounterReading:
        pressure, focus = self._pressure(player_state, enemies)
        context = 1 if focus is not None else 0
        action = int(self.dll.egosphere_decide_action(byref(self.agent), context))
        reward = self._compute_reward(player_state, enemies)
        self.dll.egosphere_update(byref(self.agent), action, reward, context)
        if action == 0:
            style = "probe"
        elif action == 1:
            style = "stabilize" if player_state.bond_tension >= 58 else "dodge_counter"
        else:
            style = "commit" if focus is not None and focus.posture <= 28 else "pressure_step"
        return EncounterReading(
            pressure=pressure,
            focus_enemy=None if focus is None else focus.name,
            recommended_style=style,
            source="native-egosphere",
        )

    def close(self) -> None:
        if getattr(self, "dll", None) is not None:
            self.dll.egosphere_free_agent(byref(self.agent))
            self.dll = None

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass


class EgoSphereBridge:
    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}
        self.mode = str(self.config.get("mode", "native-preferred"))
        self.bridge = self._create_bridge()

    def _create_bridge(self):
        if self.mode in {"native", "native-preferred", "bridge-ready"}:
            try:
                return NativeEgoSphereBridge(self.config)
            except Exception:
                if self.mode == "native":
                    raise
        return HeuristicEgoSphereBridge(self.config)

    def read_encounter(self, player_state, enemies) -> EncounterReading:
        return self.bridge.read_encounter(player_state, enemies)