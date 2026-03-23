from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Dict, List

import numpy as np
import pandas as pd

from .entity_state import TeamEntityState


@dataclass(frozen=True)
class SimulationChannel:
    channel_id: str
    label: str
    visible_to_user: bool
    confidence_band: float
    state: str
    description: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PresencePrompt:
    prompt_id: str
    minute: float
    prompt_type: str
    response_window_ms: int
    expected_action: str
    impact_label: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def _bounded(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return float(np.clip(value, lower, upper))


def _build_consent_gate(row: pd.Series) -> Dict[str, object]:
    approved_ratio = _bounded(float(row.get("lineup_approval_ratio", 0.0)))
    home_ratio = _bounded(float(row.get("home_lineup_approval_ratio", approved_ratio)))
    away_ratio = _bounded(float(row.get("away_lineup_approval_ratio", approved_ratio)))
    required_ratio = 1.0
    return {
        "lineup_approval_ratio": approved_ratio,
        "home_lineup_approval_ratio": home_ratio,
        "away_lineup_approval_ratio": away_ratio,
        "required_ratio": required_ratio,
        "all_current_lineup_approved": bool(np.isclose(approved_ratio, required_ratio)),
        "live_activation_allowed": bool(np.isclose(approved_ratio, required_ratio)),
        "play_level_reapproval_required": True,
        "notes": [
            "Scaffold only. Per-play approval must be resolved by an external licensed consent service.",
            "The session must not move into live individualized mode until the full current lineup approval ratio reaches 1.0.",
        ],
    }


def _decoded_registry(raw_value: object) -> List[Dict[str, object]]:
    if raw_value is None:
        return []
    if isinstance(raw_value, list):
        return raw_value
    text = str(raw_value).strip()
    if not text:
        return []
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return []
    return payload if isinstance(payload, list) else []


def _build_team_consent_registry(row: pd.Series, side: str, team_state: TeamEntityState) -> Dict[str, object]:
    ratio = _bounded(float(row.get(f"{side}_lineup_approval_ratio", row.get("lineup_approval_ratio", 0.0))))
    registry = _decoded_registry(row.get(f"{side}_consent_registry_json", ""))
    if not registry:
        approved_slots = int(round(ratio * len(team_state.roster)))
        registry = [
            {
                "entity_id": player.entity_id,
                "team": team_state.team,
                "approved": index < approved_slots,
                "approval_scope": "lineup",
                "approval_source": "ratio_only",
            }
            for index, player in enumerate(team_state.roster)
        ]
    approved_count = sum(1 for item in registry if item.get("approved", False))
    return {
        "team": team_state.team,
        "approved_count": approved_count,
        "required_count": len(team_state.roster),
        "approval_ratio": round(approved_count / float(max(1, len(team_state.roster))), 4),
        "registry": registry,
    }


def _build_previous_game_datastreams(row: pd.Series, entity_effects: Dict[str, float]) -> List[Dict[str, object]]:
    return [
        {
            "stream_id": "previous_game_form",
            "source_type": "historical_match_summary",
            "enabled": True,
            "input_strength": round(_bounded(float(row.get("home_goals_for_form", 1.2)) / 3.0), 4),
            "target": "team_preparedness",
        },
        {
            "stream_id": "previous_game_rest_delta",
            "source_type": "historical_recovery_window",
            "enabled": True,
            "input_strength": round(_bounded(float(row.get("rest_days_diff", 0.0)) / 10.0 + 0.5), 4),
            "target": "pregame_readiness",
        },
        {
            "stream_id": "previous_game_discipline_echo",
            "source_type": "historical_behavior_trace",
            "enabled": True,
            "input_strength": round(_bounded(0.5 + entity_effects.get("discipline_swing", 0.0)), 4),
            "target": "temper_pressure",
        },
    ]


def _build_simulation_channels(row: pd.Series, consent_gate: Dict[str, object]) -> List[Dict[str, object]]:
    model_confidence = _bounded(float(row.get("confidence", 0.5)))
    visible_confidence = round(_bounded(0.45 + 0.4 * model_confidence), 4)
    interactive_confidence = round(_bounded(0.4 + 0.32 * model_confidence), 4)
    protected_confidence = round(_bounded(0.48 + 0.42 * model_confidence), 4)
    channels = [
        SimulationChannel(
            channel_id="protected_analytic",
            label="Protected Analytic Channel",
            visible_to_user=False,
            confidence_band=protected_confidence,
            state="gated" if not consent_gate["live_activation_allowed"] else "ready",
            description="Reserved analytic stream for licensed deployment paths. Hidden from the user interface and disabled until consent gates are satisfied.",
        ),
        SimulationChannel(
            channel_id="visible_interactive",
            label="Visible Interactive Channel",
            visible_to_user=True,
            confidence_band=visible_confidence,
            state="active",
            description="User-visible simulation stream with explicit labels and transparent state transitions.",
        ),
        SimulationChannel(
            channel_id="timing_adjusted",
            label="Timing-Adjusted Channel",
            visible_to_user=True,
            confidence_band=interactive_confidence,
            state="standby",
            description="Activated only when a human-presence prompt is answered late or missed, and its effect must be shown explicitly in the UI.",
        ),
    ]
    return [channel.to_dict() for channel in channels]


def _build_presence_prompts(trajectories: List[Dict[str, object]], incidents: List[Dict[str, object]]) -> List[Dict[str, object]]:
    prompts: List[PresencePrompt] = []
    source_minutes = [float(event.get("minute", 0.0)) for event in trajectories[:2]]
    if not source_minutes:
        source_minutes = [18.0, 63.0]
    for index, minute in enumerate(source_minutes, start=1):
        prompts.append(
            PresencePrompt(
                prompt_id=f"qte_{index}",
                minute=round(minute, 2),
                prompt_type="timed_confirmation",
                response_window_ms=900,
                expected_action="confirm_prompt",
                impact_label="timing_adjustment",
            )
        )
    if incidents:
        prompts.append(
            PresencePrompt(
                prompt_id="incident_ack",
                minute=round(float(incidents[0].get("minute", 45.0)), 2),
                prompt_type="incident_acknowledgement",
                response_window_ms=1200,
                expected_action="acknowledge_state_shift",
                impact_label="state_resync",
            )
        )
    return [prompt.to_dict() for prompt in prompts]


def build_regulated_session_hooks(
    row: pd.Series,
    entity_effects: Dict[str, float],
    trajectories: List[Dict[str, object]],
    incidents: List[Dict[str, object]],
    entity_states: Dict[str, TeamEntityState],
) -> Dict[str, object]:
    consent_gate = _build_consent_gate(row)
    home_registry = _build_team_consent_registry(row, "home", entity_states["home"])
    away_registry = _build_team_consent_registry(row, "away", entity_states["away"])
    datastreams = _build_previous_game_datastreams(row, entity_effects)
    channels = _build_simulation_channels(row, consent_gate)
    prompts = _build_presence_prompts(trajectories, incidents)
    timing_dilation = round(
        _bounded(
            0.5
            + 0.35 * float(row.get("uncertainty", 0.5))
            + 0.25 * abs(entity_effects.get("discipline_swing", 0.0))
        ),
        4,
    )
    return {
        "mode": "regulated_interactive_scaffold",
        "consent_gate": consent_gate,
        "player_consent_registry": {
            "home": home_registry,
            "away": away_registry,
        },
        "previous_game_datastreams": datastreams,
        "simulation_channels": channels,
        "human_presence_prompts": prompts,
        "operator_session_status": {
            "consent_ready": bool(consent_gate["live_activation_allowed"]),
            "home_registry_complete": bool(home_registry["approved_count"] == home_registry["required_count"]),
            "away_registry_complete": bool(away_registry["approved_count"] == away_registry["required_count"]),
            "top_visible_channel": next((channel["label"] for channel in channels if channel["visible_to_user"]), "none"),
        },
        "timing_dilation_factor": timing_dilation,
        "user_must_remain_present": True,
        "transparent_channel_switching_required": True,
        "notes": [
            "This scaffold does not implement wagering logic, deceptive hidden labels, or guaranteed-accuracy claims.",
            "Any production use must display channel changes transparently and honor lineup/player consent gates before activation.",
        ],
    }