"""drIpLIVE — experiential runtime engine.

Generates feeling-states from environmental and contextual inputs.
The live pulse beats at the center of the triumvirate.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import asdict, dataclass, field


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, float(v)))


@dataclass
class ExperientialContext:
    """Raw environmental reads."""

    hour_of_day: float = 12.0
    day_energy: float = 0.65
    audience_pulse: float = 0.70
    content_freshness: float = 0.75
    platform_noise: float = 0.40
    emotional_weather: str = "clear"


@dataclass
class FeelState:
    """The seven feeling dimensions."""

    urgency: float = 0.5
    trust: float = 0.5
    wonder: float = 0.5
    tenderness: float = 0.5
    grit: float = 0.5
    clarity: float = 0.5
    volatility: float = 0.5

    def to_dict(self) -> dict:
        return asdict(self)


_WEATHER_MODS: dict[str, dict[str, float]] = {
    "clear": {
        "urgency": 0.0, "trust": 0.12, "wonder": 0.05,
        "tenderness": 0.08, "grit": -0.05, "clarity": 0.18, "volatility": -0.12,
    },
    "charged": {
        "urgency": 0.18, "trust": -0.05, "wonder": 0.14,
        "tenderness": -0.08, "grit": 0.12, "clarity": -0.05, "volatility": 0.16,
    },
    "static": {
        "urgency": -0.10, "trust": 0.05, "wonder": -0.12,
        "tenderness": 0.10, "grit": 0.08, "clarity": -0.08, "volatility": -0.05,
    },
    "storm": {
        "urgency": 0.22, "trust": -0.12, "wonder": 0.20,
        "tenderness": -0.15, "grit": 0.22, "clarity": -0.18, "volatility": 0.28,
    },
}

VALID_WEATHER = frozenset(_WEATHER_MODS)


def derive_feel_state(ctx: ExperientialContext) -> FeelState:
    """Derive a FeelState from environmental context."""
    hour_phase = (ctx.hour_of_day % 24) / 24.0
    morning_energy = math.exp(-((hour_phase - 0.35) ** 2) / 0.02)
    evening_pull = math.exp(-((hour_phase - 0.79) ** 2) / 0.03)

    urgency = 0.3 + morning_energy * 0.35 + ctx.day_energy * 0.25
    trust = 0.4 + ctx.content_freshness * 0.3 + (1.0 - ctx.platform_noise) * 0.2
    wonder = 0.25 + ctx.content_freshness * 0.35 + evening_pull * 0.2
    tenderness = 0.3 + evening_pull * 0.3 + ctx.audience_pulse * 0.2
    grit = 0.35 + ctx.day_energy * 0.3 + morning_energy * 0.15
    clarity = 0.3 + (1.0 - ctx.platform_noise) * 0.35 + ctx.content_freshness * 0.2
    volatility = 0.2 + ctx.platform_noise * 0.3 + abs(math.sin(hour_phase * math.pi * 3)) * 0.15

    mods = _WEATHER_MODS.get(ctx.emotional_weather, _WEATHER_MODS["clear"])
    urgency += mods["urgency"]
    trust += mods["trust"]
    wonder += mods["wonder"]
    tenderness += mods["tenderness"]
    grit += mods["grit"]
    clarity += mods["clarity"]
    volatility += mods["volatility"]

    return FeelState(
        urgency=_clamp(urgency),
        trust=_clamp(trust),
        wonder=_clamp(wonder),
        tenderness=_clamp(tenderness),
        grit=_clamp(grit),
        clarity=_clamp(clarity),
        volatility=_clamp(volatility),
    )


class LivePulse:
    """Persistent experiential runtime that ticks and evolves."""

    def __init__(self) -> None:
        self.context = ExperientialContext()
        self.feel = derive_feel_state(self.context)
        self.tick_count = 0
        self.birth = time.time()

    def tick(self, _dt: float = 1.0) -> FeelState:
        self.tick_count += 1
        self.context.day_energy = _clamp(self.context.day_energy + random.gauss(0, 0.02))
        self.context.audience_pulse = _clamp(self.context.audience_pulse + random.gauss(0, 0.015))
        self.context.platform_noise = _clamp(self.context.platform_noise + random.gauss(0, 0.02))
        self.feel = derive_feel_state(self.context)
        return self.feel

    def set_weather(self, weather: str) -> None:
        if weather in VALID_WEATHER:
            self.context.emotional_weather = weather
            self.feel = derive_feel_state(self.context)

    def set_hour(self, hour: float) -> None:
        self.context.hour_of_day = hour % 24
        self.feel = derive_feel_state(self.context)

    def snapshot(self) -> dict:
        return {
            "context": asdict(self.context),
            "feel": self.feel.to_dict(),
            "tick_count": self.tick_count,
            "uptime_seconds": round(time.time() - self.birth, 1),
        }
