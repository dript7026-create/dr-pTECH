"""Tests for the drIpTriumvirate backend."""

import sys
from pathlib import Path

# Wire up imports
_TRIUMVIRATE_ROOT = Path(__file__).resolve().parents[1]
_WORKSPACE = _TRIUMVIRATE_ROOT.parent
sys.path.insert(0, str(_TRIUMVIRATE_ROOT))
sys.path.insert(0, str(_WORKSPACE / "drIpSignalStudio"))

from triumvirate.driplive import (
    ExperientialContext,
    FeelState,
    LivePulse,
    derive_feel_state,
)
from triumvirate.dripsignals import feel_to_signals, resonance_score, translation_trace
from triumvirate.matrix_tasks import TaskBoard, TaskState


def test_derive_feel_state_returns_clamped_values():
    ctx = ExperientialContext(hour_of_day=8.0, day_energy=0.9, emotional_weather="storm")
    feel = derive_feel_state(ctx)
    for field_name in FeelState.__dataclass_fields__:
        val = getattr(feel, field_name)
        assert 0.0 <= val <= 1.0, f"{field_name}={val} out of range"


def test_live_pulse_tick_evolves_state():
    pulse = LivePulse()
    initial = pulse.feel.urgency
    # Tick many times — value should drift
    for _ in range(50):
        pulse.tick()
    assert pulse.tick_count == 50
    snapshot = pulse.snapshot()
    assert "feel" in snapshot
    assert "context" in snapshot


def test_feel_to_signals_produces_valid_signal_set():
    feel = FeelState(urgency=0.8, trust=0.7, wonder=0.9, tenderness=0.4, grit=0.6, clarity=0.8, volatility=0.3)
    signals = feel_to_signals(feel)
    assert 0.0 <= signals.trend_momentum <= 1.0
    assert 0.0 <= signals.audience_match <= 1.0
    assert 0.0 <= signals.proof_strength <= 1.0
    assert 0.0 <= signals.novelty_gap <= 1.0
    assert 0.0 <= signals.fatigue_risk <= 1.0
    assert 0.0 <= signals.conversion_intent <= 1.0
    assert 0.0 <= signals.retention_pull <= 1.0


def test_resonance_score_perfect_when_same_feel():
    feel = FeelState(urgency=0.7, trust=0.6, wonder=0.5, tenderness=0.5, grit=0.5, clarity=0.6, volatility=0.3)
    signals = feel_to_signals(feel)
    score = resonance_score(feel, signals)
    assert score == 1.0, f"Expected perfect resonance but got {score}"


def test_translation_trace_explains_drivers():
    feel = FeelState(urgency=0.9, trust=0.2, wonder=0.8, tenderness=0.1, grit=0.5, clarity=0.3, volatility=0.7)
    trace = translation_trace(feel)
    assert "trend_momentum" in trace
    assert "conversion_intent" in trace
    assert len(trace["trend_momentum"]) > 0
    assert "feel" in trace["trend_momentum"][0]


def test_task_board_add_advance_remove():
    board = TaskBoard()
    task = board.add("test-render-cut", priority=7)
    assert task.state == TaskState.INIT

    board.advance(task.id)
    assert task.state == TaskState.DRAFT

    board.advance(task.id)
    assert task.state == TaskState.FEEL

    board.advance(task.id)
    assert task.state == TaskState.SIGNAL

    assert board.remove(task.id) is True
    assert board._find(task.id) is None


def test_task_board_terminal_view():
    board = TaskBoard()
    board.add("alpha-cut", priority=8)
    board.add("beta-loop", priority=5)
    lines = board.terminal_view()
    assert len(lines) >= 5  # header + separator + 2 tasks + total
    assert "alpha-cut" in lines[3]


def test_task_board_attach_artifact():
    board = TaskBoard()
    task = board.add("render-sequence", priority=8)
    result = board.attach_artifact(task.id, "generated/previews/abc123/poster.png")
    assert result is not None
    assert len(result.artifacts) == 1
    assert "poster.png" in result.artifacts[0]
    # Second artifact appends
    board.attach_artifact(task.id, "generated/previews/abc123/preview.mp4")
    assert len(result.artifacts) == 2


def test_task_board_to_dict():
    board = TaskBoard()
    board.add("gamma")
    d = board.to_dict()
    assert d["total"] == 1
    assert "tasks" in d
    assert "states" in d
