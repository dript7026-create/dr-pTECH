"""Preset model profiles for NeoWakeUP planetary simulations."""

from __future__ import annotations


MODEL_PRESETS = {
    "civic": {
        "description": "Biases toward equity and institutional stability.",
        "directive": {"novelty": 0.45, "equity": 0.90, "resilience": 0.85, "speed": 0.55},
    },
    "scientific": {
        "description": "Biases toward discovery, experimentation, and knowledge transfer.",
        "directive": {"novelty": 0.95, "equity": 0.55, "resilience": 0.70, "speed": 0.60},
    },
    "ecological": {
        "description": "Biases toward long-horizon balance and distributed adaptation.",
        "directive": {"novelty": 0.60, "equity": 0.80, "resilience": 0.95, "speed": 0.40},
    },
    "strategic": {
        "description": "Biases toward speed, selective concentration, and competitive response.",
        "directive": {"novelty": 0.70, "equity": 0.45, "resilience": 0.75, "speed": 0.95},
    },
    "diplomatic": {
        "description": "Biases toward interpersonal harmony and conflict attenuation.",
        "directive": {"novelty": 0.50, "equity": 0.95, "resilience": 0.80, "speed": 0.50},
    },
    "mythic": {
        "description": "Biases toward cultural synthesis, symbolism, and narrative continuity.",
        "directive": {"novelty": 0.88, "equity": 0.68, "resilience": 0.72, "speed": 0.48},
    },
}