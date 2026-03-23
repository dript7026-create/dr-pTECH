"""
Immutable equation registry for the NeoWakeUP planetary simulation.

These equations are explicit and inspectable. They are not claims of
mathematical perfection or literal consciousness; they are deterministic
computation primitives for a recursive social simulation.
"""

from __future__ import annotations

from dataclasses import dataclass


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


@dataclass(frozen=True)
class EquationSpec:
    key: str
    expression: str
    description: str


EQUATION_SPECS = {
    "individual_activation": EquationSpec(
        key="individual_activation",
        expression="A_i = clamp(0.42*a + 0.28*c + 0.18*p + 0.12*(1-s))",
        description="Entity readiness to act from agency, curiosity, plasticity, and low stress.",
    ),
    "relational_resonance": EquationSpec(
        key="relational_resonance",
        expression="R_ij = clamp(0.5*trust + 0.25*empathy + 0.25*(1-conflict))",
        description="Pairwise social resonance between two interacting entities.",
    ),
    "regional_coherence": EquationSpec(
        key="regional_coherence",
        expression="C_r = clamp(0.4*mean(resonance) + 0.3*knowledge + 0.3*resource_balance)",
        description="Regional ability to share knowledge while maintaining stability.",
    ),
    "planetary_coherence": EquationSpec(
        key="planetary_coherence",
        expression="C_p = clamp(0.55*mean(C_r) + 0.25*exchange + 0.2*(1*volatility))",
        description="Global coherence of the simulated planetary mindset.",
    ),
    "directive_solution": EquationSpec(
        key="directive_solution",
        expression="S = clamp(0.35*C_p + 0.2*novelty + 0.2*equity + 0.15*resilience + 0.1*speed)",
        description="Directive-specific solution potential under user-supplied priorities.",
    ),
}


def individual_activation(agency: float, curiosity: float, plasticity: float, stress: float) -> float:
    return _clamp(0.42 * agency + 0.28 * curiosity + 0.18 * plasticity + 0.12 * (1.0 - stress))


def relational_resonance(trust: float, empathy: float, conflict: float) -> float:
    return _clamp(0.50 * trust + 0.25 * empathy + 0.25 * (1.0 - conflict))


def regional_coherence(avg_resonance: float, knowledge: float, resource_balance: float) -> float:
    return _clamp(0.40 * avg_resonance + 0.30 * knowledge + 0.30 * resource_balance)


def planetary_coherence(avg_region: float, exchange: float, volatility: float) -> float:
    return _clamp(0.55 * avg_region + 0.25 * exchange + 0.20 * (1.0 - volatility))


def directive_solution(global_coherence: float, novelty: float, equity: float, resilience: float, speed: float) -> float:
    return _clamp(0.35 * global_coherence + 0.20 * novelty + 0.20 * equity + 0.15 * resilience + 0.10 * speed)