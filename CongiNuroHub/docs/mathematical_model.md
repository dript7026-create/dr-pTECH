# CongiNuroHub Mathematical Model

CongiNuroHub uses explicit bounded equations so educators can inspect what the simulation is doing.

## Equation registry

1. Environment affordance

$$
E = clamp(0.45 \cdot stability + 0.35 \cdot nutrient + 0.20 \cdot complexity)
$$

2. Learning gain

$$
L = clamp(0.30 \cdot curiosity + 0.25 \cdot challenge + 0.25 \cdot affordance + 0.20 \cdot (1 - stress))
$$

3. Reflective balance

$$
R = clamp(0.35 \cdot awareness + 0.30 \cdot empathy + 0.20 \cdot reflection + 0.15 \cdot (1 - stress))
$$

4. Social coherence

$$
S = clamp(0.40 \cdot belonging + 0.35 \cdot trust + 0.25 \cdot equity)
$$

5. Hub consensus

$$
H = clamp(0.35 \cdot \overline{knowledge} + 0.25 \cdot \overline{reflection} + 0.25 \cdot \overline{coherence} + 0.15 \cdot (1 - friction))
$$

## Modeling stance

- The system is deterministic and inspectable.
- The system does not claim literal consciousness.
- The goal is educational experimentation with interacting variables, tradeoffs, and emergent cohort behavior.