"""Deterministic education-oriented cognition simulation for CongiNuroHub."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from random import Random
from statistics import fmean


DATA_ROOT = Path(__file__).resolve().parent / "data"
DEFAULT_DATASET_FILE = DATA_ROOT / "artisapiens_seed_v1.json"


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


@dataclass(frozen=True)
class EquationSpec:
    key: str
    expression: str
    description: str


EQUATION_SPECS = {
    "environment_affordance": EquationSpec(
        key="environment_affordance",
        expression="E = clamp(0.45*stability + 0.35*nutrient + 0.20*complexity)",
        description="Habitat support for safe and interesting learning.",
    ),
    "learning_gain": EquationSpec(
        key="learning_gain",
        expression="L = clamp(0.30*curiosity + 0.25*challenge + 0.25*affordance + 0.20*(1-stress))",
        description="Knowledge gain produced by curiosity, challenge, and environmental support.",
    ),
    "reflective_balance": EquationSpec(
        key="reflective_balance",
        expression="R = clamp(0.35*awareness + 0.30*empathy + 0.20*reflection + 0.15*(1-stress))",
        description="Metacognitive stability that resists panic and impulsive drift.",
    ),
    "social_coherence": EquationSpec(
        key="social_coherence",
        expression="S = clamp(0.40*belonging + 0.35*trust + 0.25*equity)",
        description="Group cohesion under educational equity pressure.",
    ),
    "hub_consensus": EquationSpec(
        key="hub_consensus",
        expression="H = clamp(0.35*mean(knowledge) + 0.25*mean(reflection) + 0.25*mean(coherence) + 0.15*(1*friction))",
        description="Whole-hub consensus signal used by the live dashboard.",
    ),
}


@dataclass
class Directive:
    curiosity_bias: float = 0.72
    equity_bias: float = 0.78
    challenge_bias: float = 0.66
    reflection_bias: float = 0.81


@dataclass
class ArtiSapiensSeed:
    agent_id: str
    habitat_id: str
    lifecycle_stage: str
    specialization: str
    curiosity: float
    empathy: float
    awareness: float
    resilience: float
    knowledge: float
    trust: float
    belonging: float
    stress: float


@dataclass
class HabitatState:
    habitat_id: str
    title: str
    theme: str
    stability: float
    nutrient: float
    complexity: float
    chemistry: float
    biology: float
    physics: float


@dataclass
class SimulationState:
    tick: int
    seed: int
    dataset_id: str = "procedural-v1"
    dataset_title: str = "Procedural ArtiSapiens cohort"
    directive: Directive = field(default_factory=Directive)
    agents: list[ArtiSapiensSeed] = field(default_factory=list)
    habitats: list[HabitatState] = field(default_factory=list)
    hub_consensus: float = 0.0
    mean_knowledge: float = 0.0
    mean_reflection: float = 0.0
    mean_coherence: float = 0.0
    friction: float = 0.0

    def to_dict(self) -> dict:
        return asdict(self)


def environment_affordance(stability: float, nutrient: float, complexity: float) -> float:
    return _clamp(0.45 * stability + 0.35 * nutrient + 0.20 * complexity)


def learning_gain(curiosity: float, challenge: float, affordance: float, stress: float) -> float:
    return _clamp(0.30 * curiosity + 0.25 * challenge + 0.25 * affordance + 0.20 * (1.0 - stress))


def reflective_balance(awareness: float, empathy: float, reflection: float, stress: float) -> float:
    return _clamp(0.35 * awareness + 0.30 * empathy + 0.20 * reflection + 0.15 * (1.0 - stress))


def social_coherence(belonging: float, trust: float, equity: float) -> float:
    return _clamp(0.40 * belonging + 0.35 * trust + 0.25 * equity)


def hub_consensus(mean_knowledge: float, mean_reflection: float, mean_coherence: float, friction: float) -> float:
    return _clamp(0.35 * mean_knowledge + 0.25 * mean_reflection + 0.25 * mean_coherence + 0.15 * (1.0 - friction))


def _load_dataset(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _state_from_dataset(path: Path) -> SimulationState:
    payload = _load_dataset(path)
    state = SimulationState(
        tick=int(payload.get("tick", 0)),
        seed=int(payload.get("seed", 11)),
        dataset_id=str(payload.get("dataset_id", path.stem)),
        dataset_title=str(payload.get("title", "ArtiSapiens cohort")),
        directive=Directive(**payload.get("directive", {})),
        habitats=[HabitatState(**habitat) for habitat in payload.get("habitats", [])],
        agents=[ArtiSapiensSeed(**agent) for agent in payload.get("agents", [])],
    )
    _recompute_metrics(state)
    return state


def bootstrap_state(seed: int = 11, agent_count: int = 18, habitat_count: int = 4) -> SimulationState:
    if seed == 11 and agent_count == 18 and habitat_count == 4 and DEFAULT_DATASET_FILE.exists():
        return _state_from_dataset(DEFAULT_DATASET_FILE)

    rng = Random(seed)
    habitats = []
    for index in range(habitat_count):
        habitats.append(
            HabitatState(
                habitat_id=f"hub-{index + 1}",
                title=f"Habitat {index + 1}",
                theme="procedural-learning-ecology",
                stability=rng.uniform(0.52, 0.88),
                nutrient=rng.uniform(0.45, 0.92),
                complexity=rng.uniform(0.35, 0.90),
                chemistry=rng.uniform(0.40, 0.85),
                biology=rng.uniform(0.38, 0.88),
                physics=rng.uniform(0.44, 0.86),
            )
        )

    agents = []
    for index in range(agent_count):
        habitat = habitats[index % habitat_count]
        agents.append(
            ArtiSapiensSeed(
                agent_id=f"artisapiens-{index + 1:02d}",
                habitat_id=habitat.habitat_id,
                lifecycle_stage="apprentice",
                specialization="general-systems-inquiry",
                curiosity=rng.uniform(0.42, 0.95),
                empathy=rng.uniform(0.36, 0.92),
                awareness=rng.uniform(0.32, 0.90),
                resilience=rng.uniform(0.40, 0.92),
                knowledge=rng.uniform(0.18, 0.52),
                trust=rng.uniform(0.35, 0.72),
                belonging=rng.uniform(0.30, 0.76),
                stress=rng.uniform(0.16, 0.48),
            )
        )

    state = SimulationState(tick=0, seed=seed, agents=agents, habitats=habitats)
    _recompute_metrics(state)
    return state


def _recompute_metrics(state: SimulationState) -> None:
    reflection_values = []
    coherence_values = []
    for agent in state.agents:
        reflection_values.append(
            reflective_balance(
                agent.awareness,
                agent.empathy,
                state.directive.reflection_bias,
                agent.stress,
            )
        )
        coherence_values.append(social_coherence(agent.belonging, agent.trust, state.directive.equity_bias))

    state.mean_knowledge = fmean(agent.knowledge for agent in state.agents) if state.agents else 0.0
    state.mean_reflection = fmean(reflection_values) if reflection_values else 0.0
    state.mean_coherence = fmean(coherence_values) if coherence_values else 0.0
    state.friction = fmean(agent.stress for agent in state.agents) if state.agents else 0.0
    state.hub_consensus = hub_consensus(state.mean_knowledge, state.mean_reflection, state.mean_coherence, state.friction)


def step_state(state: SimulationState, steps: int = 1, directive: Directive | None = None) -> SimulationState:
    if directive is not None:
        state.directive = directive

    for _ in range(max(1, int(steps))):
        state.tick += 1
        habitat_lookup = {habitat.habitat_id: habitat for habitat in state.habitats}
        for habitat in state.habitats:
            habitat.stability = _clamp(habitat.stability + 0.01 * state.directive.equity_bias - 0.006 * state.friction)
            habitat.nutrient = _clamp(habitat.nutrient + 0.008 * state.directive.reflection_bias - 0.004 * state.friction)
            habitat.complexity = _clamp(habitat.complexity + 0.008 * state.directive.curiosity_bias + 0.004 * habitat.physics - 0.003 * habitat.stability)

        for agent in state.agents:
            habitat = habitat_lookup[agent.habitat_id]
            affordance = environment_affordance(habitat.stability, habitat.nutrient, habitat.complexity)
            gain = learning_gain(agent.curiosity, state.directive.challenge_bias, affordance, agent.stress)
            reflection = reflective_balance(agent.awareness, agent.empathy, state.directive.reflection_bias, agent.stress)
            coherence = social_coherence(agent.belonging, agent.trust, state.directive.equity_bias)

            agent.knowledge = _clamp(agent.knowledge + 0.05 * gain + 0.01 * reflection)
            agent.awareness = _clamp(agent.awareness + 0.03 * state.directive.reflection_bias + 0.02 * gain - 0.015 * agent.stress)
            agent.trust = _clamp(agent.trust + 0.03 * coherence + 0.02 * state.directive.equity_bias - 0.01 * state.directive.challenge_bias)
            agent.belonging = _clamp(agent.belonging + 0.03 * state.directive.equity_bias + 0.02 * reflection - 0.01 * agent.stress)
            agent.stress = _clamp(agent.stress + 0.03 * state.directive.challenge_bias - 0.03 * reflection - 0.02 * agent.resilience)

        _recompute_metrics(state)

    return state


def registry_payload() -> dict:
    return {
        "equations": [asdict(spec) for spec in EQUATION_SPECS.values()],
        "note": "These equations are explicit educational simulation primitives, not claims of literal consciousness.",
    }


def dataset_payload(path: Path = DEFAULT_DATASET_FILE) -> dict:
    if not path.exists():
        return {
            "dataset_id": "procedural-v1",
            "title": "Procedural ArtiSapiens cohort",
            "note": "No canonical dataset file is available.",
            "habitat_count": 0,
            "agent_count": 0,
        }

    payload = _load_dataset(path)
    return {
        "dataset_id": payload.get("dataset_id", path.stem),
        "title": payload.get("title", "ArtiSapiens cohort"),
        "note": payload.get("note", ""),
        "habitat_count": len(payload.get("habitats", [])),
        "agent_count": len(payload.get("agents", [])),
    }