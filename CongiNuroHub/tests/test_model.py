from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from conginurohub.model import Directive, bootstrap_state, dataset_payload, registry_payload, step_state


def test_bootstrap_counts_match_request():
    state = bootstrap_state(seed=5, agent_count=10, habitat_count=3)
    assert len(state.agents) == 10
    assert len(state.habitats) == 3
    assert state.tick == 0


def test_step_advances_tick_and_keeps_metrics_bounded():
    state = bootstrap_state(seed=7, agent_count=12, habitat_count=4)
    directive = Directive(curiosity_bias=0.8, equity_bias=0.75, challenge_bias=0.6, reflection_bias=0.85)
    step_state(state, steps=5, directive=directive)

    assert state.tick == 5
    assert 0.0 <= state.hub_consensus <= 1.0
    assert 0.0 <= state.mean_knowledge <= 1.0
    assert 0.0 <= state.mean_reflection <= 1.0
    assert 0.0 <= state.mean_coherence <= 1.0
    assert 0.0 <= state.friction <= 1.0


def test_registry_contains_hub_consensus_equation():
    payload = registry_payload()
    keys = {entry["key"] for entry in payload["equations"]}
    assert "hub_consensus" in keys


def test_default_bootstrap_loads_canonical_dataset():
    state = bootstrap_state()
    meta = dataset_payload()

    assert state.dataset_id == "artisapiens-seed-v1"
    assert meta["agent_count"] == len(state.agents)
    assert meta["habitat_count"] == len(state.habitats)