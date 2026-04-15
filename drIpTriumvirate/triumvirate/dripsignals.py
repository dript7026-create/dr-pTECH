"""dripsignals — the middle layer.

Translates FeelState into SignalSet with explainable resonance mapping.
The bridge between experience and output.
"""

from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path

from .driplive import FeelState

_STUDIO_ROOT = Path(__file__).resolve().parents[2] / "drIpSignalStudio"
if str(_STUDIO_ROOT) not in sys.path:
    sys.path.insert(0, str(_STUDIO_ROOT))

from dripsignalstudio.model import SignalSet  # noqa: E402


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(v)))


# Resonance matrix: how each feeling dimension maps to each signal dimension.
# Columns: trend_momentum, audience_match, proof_strength, novelty_gap,
#          inv_fatigue, conversion_intent, retention_pull
_RESONANCE: dict[str, list[float]] = {
    "urgency":     [0.35, 0.10, 0.08, 0.12,  0.05, 0.28, 0.02],
    "trust":       [0.05, 0.22, 0.32, 0.04,  0.18, 0.12, 0.07],
    "wonder":      [0.18, 0.08, 0.04, 0.38,  0.08, 0.06, 0.18],
    "tenderness":  [0.02, 0.28, 0.08, 0.06,  0.16, 0.08, 0.32],
    "grit":        [0.12, 0.06, 0.30, 0.08,  0.04, 0.32, 0.08],
    "clarity":     [0.08, 0.15, 0.12, 0.06,  0.35, 0.10, 0.14],
    "volatility":  [0.30, 0.02, 0.02, 0.28, -0.20, 0.06, 0.08],
}

_FEEL_KEYS = ["urgency", "trust", "wonder", "tenderness", "grit", "clarity", "volatility"]
_SIGNAL_NAMES = [
    "trend_momentum", "audience_match", "proof_strength",
    "novelty_gap", "fatigue_risk", "conversion_intent", "retention_pull",
]


def feel_to_signals(feel: FeelState) -> SignalSet:
    """Translate a FeelState into a SignalSet via resonance mapping."""
    feel_values = [
        feel.urgency, feel.trust, feel.wonder,
        feel.tenderness, feel.grit, feel.clarity, feel.volatility,
    ]

    signals = [0.0] * 7
    for i, fk in enumerate(_FEEL_KEYS):
        weights = _RESONANCE[fk]
        for j in range(7):
            signals[j] += feel_values[i] * weights[j]

    # Column 4 represents inverse-fatigue (clarity boosts it, volatility reduces it).
    raw_inv_fatigue = signals[4]

    return SignalSet(
        trend_momentum=_clamp(signals[0]),
        audience_match=_clamp(signals[1]),
        proof_strength=_clamp(signals[2]),
        novelty_gap=_clamp(signals[3]),
        fatigue_risk=_clamp(1.0 - raw_inv_fatigue),
        conversion_intent=_clamp(signals[5]),
        retention_pull=_clamp(signals[6]),
    )


def resonance_score(feel: FeelState, signals: SignalSet) -> float:
    """How well do the current feel and signals align? 0–1."""
    translated = feel_to_signals(feel)
    t = asdict(translated)
    s = asdict(signals)
    diffs = [(t[k] - s[k]) ** 2 for k in t]
    return round(1.0 - (sum(diffs) / len(diffs)) ** 0.5, 3)


def translation_trace(feel: FeelState) -> dict:
    """Explainable mapping showing which feelings drove which signals."""
    feel_values = {
        "urgency": feel.urgency, "trust": feel.trust, "wonder": feel.wonder,
        "tenderness": feel.tenderness, "grit": feel.grit,
        "clarity": feel.clarity, "volatility": feel.volatility,
    }

    trace: dict[str, list[dict]] = {}
    for j, sig_name in enumerate(_SIGNAL_NAMES):
        drivers = []
        for fk, fv in feel_values.items():
            contribution = fv * _RESONANCE[fk][j]
            if abs(contribution) > 0.02:
                drivers.append({
                    "feel": fk,
                    "value": round(fv, 3),
                    "weight": _RESONANCE[fk][j],
                    "contribution": round(contribution, 3),
                })
        drivers.sort(key=lambda d: d["contribution"], reverse=True)
        trace[sig_name] = drivers

    return trace
