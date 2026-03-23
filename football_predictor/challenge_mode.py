from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ChallengeCueProfile:
    challenge_mode_enabled: bool
    visible_label: str
    pressure_label: str
    timing_window_label: str
    rhythm_label: str
    attention_focus_label: str
    reflex_window_label: str
    spectator_prompt: str
    focus_target: str
    cue_color: str
    cue_vector: Dict[str, float]
    exact_percentages_hidden: bool

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def _bounded(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return float(np.clip(value, lower, upper))


def build_challenge_cue_profile(row: pd.Series, simulation_result: Dict[str, object] | None = None) -> Dict[str, object]:
    confidence = _bounded(float(row.get("confidence", 0.5)))
    uncertainty = _bounded(float(row.get("uncertainty", 1.0 - confidence)))
    entropy = _bounded(float(row.get("entropy", 0.5)))
    channel_confidence = confidence
    volatility = entropy
    error_pressure = 0.0
    perception_gap = 0.0
    focus_load = 0.0
    spectator_prompt = "Track the whole flow and wait for the pressure swing."
    focus_target = "central_balance"
    if simulation_result:
        regulated = simulation_result.get("regulated_session", {}) or {}
        visible_channels = [channel for channel in regulated.get("simulation_channels", []) or [] if channel.get("visible_to_user", False)]
        if visible_channels:
            channel_confidence = _bounded(float(visible_channels[0].get("confidence_band", confidence)))
        effects = simulation_result.get("entity_effects", {}) or {}
        error_pressure = _bounded(0.5 * float(effects.get("home_error_pressure", 0.0)) + 0.5 * float(effects.get("away_error_pressure", 0.0)))
        perception_gap = _bounded(abs(float(effects.get("perception_gap", 0.0))) * 1.6)
        cues = simulation_result.get("spectator_cues", {}) or {}
        focus_load = _bounded(float(cues.get("focus_load", 0.0)))
        spectator_prompt = str(cues.get("spectator_prompt", spectator_prompt))
        focus_target = str(cues.get("focus_target", focus_target))

    cue_strength = _bounded(0.55 * channel_confidence + 0.25 * confidence + 0.2 * (1.0 - uncertainty))
    tension = _bounded(0.44 * entropy + 0.26 * uncertainty + 0.18 * error_pressure + 0.12 * focus_load)
    rhythm = _bounded(0.48 * cue_strength + 0.22 * (1.0 - tension) + 0.16 * (1.0 - perception_gap) + 0.14 * (1.0 - error_pressure))
    reflex_load = _bounded(0.42 * tension + 0.26 * focus_load + 0.18 * error_pressure + 0.14 * perception_gap)

    if cue_strength < 0.43:
        visible_label = "Foggy Read"
        cue_color = "ash"
    elif cue_strength < 0.56:
        visible_label = "Soft Lean"
        cue_color = "steel"
    elif cue_strength < 0.7:
        visible_label = "Readable Lean"
        cue_color = "signal"
    elif cue_strength < 0.82:
        visible_label = "Strong Tell"
        cue_color = "amber"
    else:
        visible_label = "Heavy Tell"
        cue_color = "crimson"

    if tension < 0.33:
        pressure_label = "Calm Pressure"
        timing_window_label = "Wide Window"
    elif tension < 0.58:
        pressure_label = "Balanced Pressure"
        timing_window_label = "Standard Window"
    else:
        pressure_label = "Sharp Pressure"
        timing_window_label = "Tight Window"

    if focus_load < 0.34:
        attention_focus_label = "Whole-Field Read"
    elif focus_load < 0.62:
        attention_focus_label = "Two-Sided Pressure"
    else:
        attention_focus_label = "Hotspot Lock"

    if reflex_load < 0.34:
        reflex_window_label = "Measured Reflex"
    elif reflex_load < 0.62:
        reflex_window_label = "Active Reflex"
    else:
        reflex_window_label = "Acute Reflex"

    rhythm_label = "Smooth Rhythm" if rhythm >= 0.58 else "Broken Rhythm"
    return ChallengeCueProfile(
        challenge_mode_enabled=True,
        visible_label=visible_label,
        pressure_label=pressure_label,
        timing_window_label=timing_window_label,
        rhythm_label=rhythm_label,
        attention_focus_label=attention_focus_label,
        reflex_window_label=reflex_window_label,
        spectator_prompt=spectator_prompt,
        focus_target=focus_target,
        cue_color=cue_color,
        cue_vector={
            "cue_strength": round(cue_strength, 4),
            "tension": round(tension, 4),
            "rhythm": round(rhythm, 4),
            "focus_load": round(focus_load, 4),
            "error_pressure": round(error_pressure, 4),
            "perception_gap": round(perception_gap, 4),
            "reflex_load": round(reflex_load, 4),
        },
        exact_percentages_hidden=True,
    ).to_dict()