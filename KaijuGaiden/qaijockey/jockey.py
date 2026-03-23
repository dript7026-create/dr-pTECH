"""
qaijockey/jockey.py — QAIJockey: the AI 'rider' that plays Kaiju Gaiden!? GB.

Philosophy:
  The AI 'rides' the game like a jockey on a horse — not by brute-force
  look-ahead, but by reading the current state of motion and responding
  with calibrated probability.  Every frame the game advances (makes its
  move), then QAIJockey reads the framebuffer, weighs the evidence from
  the temporal diff buffer, and selects a button input (makes the
  player's move).  This repeats until a win or loss state is reached.

Skill model:
  Base skill (0.0–1.0) sets the signal-to-noise ratio of action selection.
  At skill=1.0 the highest-probability action is taken every time.
  At skill=0.0 actions are effectively random.
  The SkillManager dynamically scales effective skill downward when the
  host machine's frame-processing time exceeds the ~16 ms vsync budget,
  preventing the AI from making decisions faster than the game can render.

Action space (maps directly to Game Boy buttons):
  A_ATTACK  → "a"       primary attack / combo
  A_DODGE   → "b"       dodge roll
  A_LEFT    → "left"    move left
  A_RIGHT   → "right"   move right
  A_NANO    → "select"  consume NanoCell (power boost)
  A_NONE    → None      hold still
"""

import time
import numpy as np
from dataclasses import dataclass
from collections import deque
from typing import Optional, Deque

from qaijockey.vision import GameState, TemporalContext, analyze

# ── Action index constants ────────────────────────────────────────────────────
A_ATTACK = 0
A_DODGE  = 1
A_LEFT   = 2
A_RIGHT  = 3
A_NANO   = 4
A_NONE   = 5
N_ACTIONS = 6

ACTION_BUTTONS = ["a", "b", "left", "right", "select", None]
ACTION_LABELS  = ["ATTACK", "DODGE", "LEFT", "RIGHT", "NANO", "WAIT"]

# How many frames each button press is held before auto-release
ACTION_HOLD_FRAMES = {
    A_ATTACK: 3,
    A_DODGE:  6,
    A_LEFT:   4,
    A_RIGHT:  4,
    A_NANO:   2,
    A_NONE:   0,
}

# Cinematic auto-skip: hold B for this many consecutive frames
CINEMATIC_B_HOLD = 95   # kaijugaiden.c SKIP_HOLD_FRAMES = 90 + margin

# ── Skill manager ─────────────────────────────────────────────────────────────

class SkillManager:
    """
    Dynamically adjusts effective skill based on measured frame-processing
    wall-clock time versus the 16 ms vblank budget.

    If the analysis loop is taking longer than the budget (slow machine),
    effective_skill is reduced so the AI makes less optimal decisions —
    simulating a human player who can't react in time.

    effective_skill = base_skill × min(1, budget_ms / avg_frame_ms)
    """

    BUDGET_MS = 16.0        # one 60fps frame
    WARMUP_FRAMES = 10      # frames before performance scaling kicks in

    def __init__(self, base_skill: float = 0.75):
        self.base_skill = float(np.clip(base_skill, 0.0, 1.0))
        self._frame_times: Deque[float] = deque(maxlen=60)

    def record(self, elapsed_ms: float) -> None:
        self._frame_times.append(elapsed_ms)

    @property
    def effective_skill(self) -> float:
        if len(self._frame_times) < self.WARMUP_FRAMES:
            return self.base_skill
        avg = float(np.mean(self._frame_times))
        perf = min(1.0, self.BUDGET_MS / max(avg, 0.5))
        return float(self.base_skill * perf)

    @property
    def reaction_delay_frames(self) -> int:
        """
        Lower skill = more 'reaction lag' frames before acting.
        Simulates a human who can't react instantly.
        """
        sk = self.effective_skill
        if sk >= 0.90:
            return 0
        if sk >= 0.70:
            return 1
        if sk >= 0.50:
            return 3
        if sk >= 0.30:
            return 5
        return 8

    @property
    def avg_frame_ms(self) -> float:
        if not self._frame_times:
            return 0.0
        return float(np.mean(self._frame_times))


@dataclass
class PredictiveSnapshot:
    horizon_frames: int = 1
    predicted_player_x: float = 40.0
    predicted_boss_x: float = 120.0
    predicted_distance: float = 80.0
    predicted_boss_attack: bool = False
    threat_score: float = 0.0


class PerformanceCompensator:
    """
    Converts machine stress plus combat pressure into anticipation adjustments.

    Under load, a human player starts reading motion earlier and committing to
    safer actions. This model mirrors that by raising the forecast horizon and
    amplifying threat sensitivity when frame budget is being missed.
    """

    def __init__(self, budget_ms: float = 16.0):
        self.budget_ms = budget_ms
        self._stress_hist: Deque[float] = deque(maxlen=90)
        self._perf_hist: Deque[float] = deque(maxlen=90)
        self._combat_hist: Deque[float] = deque(maxlen=90)

    def update(self, avg_frame_ms: float, combat_pressure: float) -> None:
        perf_load = np.clip((avg_frame_ms - self.budget_ms) / max(self.budget_ms, 1.0), 0.0, 2.0)
        stress = np.clip(0.65 * perf_load + 0.35 * combat_pressure, 0.0, 1.0)
        self._perf_hist.append(float(perf_load))
        self._combat_hist.append(float(combat_pressure))
        self._stress_hist.append(float(stress))

    @property
    def stress(self) -> float:
        if not self._stress_hist:
            return 0.0
        return float(np.mean(self._stress_hist))

    @property
    def acute_stress(self) -> float:
        if not self._stress_hist:
            return 0.0
        return float(self._stress_hist[-1])

    @property
    def anticipation_frames(self) -> int:
        stress = self.acute_stress
        if stress >= 0.85:
            return 4
        if stress >= 0.60:
            return 3
        if stress >= 0.35:
            return 2
        return 1

    @property
    def safety_bias(self) -> float:
        return 1.0 + self.acute_stress * 1.75

    @property
    def aggression_damping(self) -> float:
        return 1.0 - self.acute_stress * 0.45


class PredictiveEngine:
    """
    Builds a short-horizon forecast from recent state deltas.

    This is intentionally lightweight: it predicts where the fighters will be
    a few frames ahead, then raises boss threat if motion trends imply an
    incoming lunge. The horizon grows automatically under performance stress.
    """

    def __init__(self):
        self._states: Deque[GameState] = deque(maxlen=12)

    def update(self, gs: GameState) -> None:
        self._states.append(gs)

    def _velocity(self, attr: str) -> float:
        if len(self._states) < 2:
            return 0.0
        recent = list(self._states)[-4:]
        if len(recent) < 2:
            return 0.0
        diffs = [getattr(b, attr) - getattr(a, attr) for a, b in zip(recent[:-1], recent[1:])]
        return float(np.mean(diffs))

    def forecast(self, gs: GameState, temporal: TemporalContext,
                 compensator: PerformanceCompensator) -> PredictiveSnapshot:
        horizon = compensator.anticipation_frames
        player_vx = self._velocity("player_x")
        boss_vx = self._velocity("boss_x")
        predicted_player_x = float(np.clip(gs.player_x + player_vx * horizon, 0, 159))
        predicted_boss_x = float(np.clip(gs.boss_x + boss_vx * horizon, 0, 159))
        predicted_distance = abs(predicted_player_x - predicted_boss_x)

        boss_momentum = max(0.0, abs(boss_vx) / 4.0)
        boss_motion = min(1.0, temporal.boss_diff_mean * 2.8)
        collapse_risk = np.clip((32.0 - predicted_distance) / 32.0, 0.0, 1.0)
        threat_score = float(np.clip(
            0.45 * boss_motion +
            0.35 * collapse_risk +
            0.20 * boss_momentum,
            0.0,
            1.0,
        ))
        predicted_boss_attack = temporal.boss_attacking or threat_score > (0.38 - 0.08 * compensator.acute_stress)

        return PredictiveSnapshot(
            horizon_frames=horizon,
            predicted_player_x=predicted_player_x,
            predicted_boss_x=predicted_boss_x,
            predicted_distance=predicted_distance,
            predicted_boss_attack=predicted_boss_attack,
            threat_score=threat_score,
        )


class GeneticPolicyMixer:
    """
    Maintains a tiny evolving set of policy genomes.

    Each genome controls how strongly the AI trusts predictive versus reactive
    thinking, how cautious it becomes under stress, and how noisy its decision
    making feels. Rewards are shaped from survival, damage race, and outcomes.
    """

    def __init__(self, rng: np.random.Generator):
        self._rng = rng
        self._population = [self._new_genome() for _ in range(5)]
        self._scores = [0.0 for _ in self._population]
        self._active_index = 0
        self.generations = 0

    def _new_genome(self) -> dict:
        return {
            "predictive_weight": float(self._rng.uniform(0.30, 0.80)),
            "reactive_weight": float(self._rng.uniform(0.70, 1.35)),
            "stress_weight": float(self._rng.uniform(0.55, 1.45)),
            "courage": float(self._rng.uniform(0.80, 1.20)),
            "patience": float(self._rng.uniform(0.75, 1.25)),
            "instinct_noise": float(self._rng.uniform(0.05, 0.55)),
        }

    @property
    def active(self) -> dict:
        return self._population[self._active_index]

    def choose_active(self) -> None:
        self._active_index = int(np.argmax(self._scores))

    def reward(self, delta: float) -> None:
        idx = self._active_index
        self._scores[idx] = 0.92 * self._scores[idx] + 0.08 * float(delta)
        if self._rng.random() < 0.03:
            self._evolve()
        self.choose_active()

    def reward_outcome(self, win: bool) -> None:
        self.reward(2.5 if win else -1.8)
        self._evolve(force=True)

    def _evolve(self, force: bool = False) -> None:
        if not force and len(self._population) < 2:
            return
        elite = int(np.argmax(self._scores))
        base = dict(self._population[elite])
        candidate = {}
        for key, value in base.items():
            sigma = 0.06 if key != "instinct_noise" else 0.04
            candidate[key] = float(np.clip(value + self._rng.normal(0.0, sigma), 0.0, 1.6))
        replace = int(np.argmin(self._scores))
        self._population[replace] = candidate
        self._scores[replace] = self._scores[elite] * 0.75
        self.generations += 1

    def export_state(self) -> dict:
        return {
            "population": self._population,
            "scores": self._scores,
            "active_index": self._active_index,
            "generations": self.generations,
        }

    def import_state(self, payload: dict) -> bool:
        try:
            population = payload["population"]
            scores = payload["scores"]
            active_index = int(payload.get("active_index", 0))
        except (KeyError, TypeError, ValueError):
            return False
        if not population or len(population) != len(scores):
            return False
        self._population = [dict(item) for item in population]
        self._scores = [float(item) for item in scores]
        self._active_index = max(0, min(active_index, len(self._population) - 1))
        self.generations = int(payload.get("generations", 0))
        self.choose_active()
        return True


class OutcomeRewardTuner:
    """
    Tunes reward intensity against actual long-run outcomes.
    """

    def __init__(self, window: int = 12):
        self._outcomes: Deque[float] = deque(maxlen=max(4, window))

    def record(self, win: bool) -> None:
        self._outcomes.append(1.0 if win else 0.0)

    @property
    def win_rate(self) -> float:
        if not self._outcomes:
            return 0.5
        return float(np.mean(self._outcomes))

    @property
    def confidence(self) -> float:
        return min(1.0, len(self._outcomes) / max(self._outcomes.maxlen, 1))

    def shape_outcome_reward(self, win: bool) -> float:
        base = 2.8 if win else -2.0
        pressure = 1.0 - self.win_rate
        if win:
            return base + 1.1 * pressure * self.confidence
        return base - 0.9 * pressure * self.confidence

    def shape_live_reward(self, reward: float) -> float:
        pressure = 1.0 - self.win_rate
        scale = 1.0 + 0.35 * pressure * self.confidence
        return float(reward * scale)


# ── Softmax ───────────────────────────────────────────────────────────────────

def _softmax(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - x.max())
    return e / e.sum()


# ── QAIJockey ─────────────────────────────────────────────────────────────────

class QAIJockey:
    """
    The AI rider.

    Usage:
        jockey = QAIJockey(emulator_interface, skill=0.75)
        while True:
            pyboy.tick()                       # game makes its move
            shades = pil_to_shades(pyboy.screen.image)
            state = jockey.tick(shades)        # AI reads & responds
            recorder.write_pil(pyboy.screen.image)
    """

    def __init__(self, emulator, skill: float = 0.75,
                 stress_delay_ms: float = 0.0,
                 stress_jitter_ms: float = 0.0,
                 input_logger=None,
                 tune_window: int = 12):
        """
        emulator: object with .press(btn) and .release(btn) methods.
        skill:    0.0 = random play  |  1.0 = optimal play
        """
        self.emu = emulator
        self.temporal = TemporalContext()
        self.skill_mgr = SkillManager(base_skill=skill)
        self.compensator = PerformanceCompensator(budget_ms=self.skill_mgr.BUDGET_MS)
        self.predictor = PredictiveEngine()
        self._rng = np.random.default_rng()
        self.genetics = GeneticPolicyMixer(self._rng)
        self.reward_tuner = OutcomeRewardTuner(window=tune_window)
        self.stress_delay_ms = max(0.0, float(stress_delay_ms))
        self.stress_jitter_ms = max(0.0, float(stress_jitter_ms))
        self.input_logger = input_logger

        self._held: set = set()                     # currently held buttons
        self._pending_release: Optional[tuple] = None  # (btn, release_at_frame)
        self._delay_remain: int = 0                 # reaction-lag countdown
        self._frame_n: int = 0                      # total frames processed

        self._phase_prev: str = "unknown"
        self._cinematic_b_frames: int = 0           # consecutive B-hold frames
        self._prev_state: Optional[GameState] = None
        self._last_forecast = PredictiveSnapshot()

        # Outcome tracking
        self.wins:   int = 0
        self.losses: int = 0
        self.inputs_logged: int = 0

    # ── Internal button helpers ──────────────────────────────────────────────

    def _press(self, btn: str) -> None:
        if btn and btn not in self._held:
            self.emu.press(btn)
            self._held.add(btn)

    def _release(self, btn: str) -> None:
        if btn and btn in self._held:
            self.emu.release(btn)
            self._held.discard(btn)

    def _release_all(self) -> None:
        for btn in list(self._held):
            self.emu.release(btn)
        self._held.clear()

    def _tap(self, btn: str, hold_frames: int = 3) -> None:
        """Press btn now; schedule auto-release after hold_frames frames."""
        if btn:
            self._release_all()
            self._press(btn)
            self._pending_release = (btn, self._frame_n + hold_frames)

    def _inject_stress_delay(self) -> None:
        if self.stress_delay_ms <= 0.0 and self.stress_jitter_ms <= 0.0:
            return
        delay_ms = self.stress_delay_ms
        if self.stress_jitter_ms > 0.0:
            delay_ms += abs(float(self._rng.normal(0.0, self.stress_jitter_ms)))
        if delay_ms > 0.0:
            time.sleep(delay_ms / 1000.0)

    def _log_decision(self, gs: GameState, forecast: PredictiveSnapshot,
                      action: int, hold: int) -> None:
        if self.input_logger is None:
            return
        self.input_logger.log_input({
            "frame": self._frame_n,
            "phase": gs.phase,
            "action": ACTION_LABELS[action],
            "button": ACTION_BUTTONS[action],
            "hold_frames": hold,
            "player_hp": gs.player_hp,
            "boss_hp_frac": round(gs.boss_hp_frac, 4),
            "player_x": gs.player_x,
            "boss_x": gs.boss_x,
            "nanocells": gs.nanocells,
            "predicted_distance": round(forecast.predicted_distance, 3),
            "predicted_boss_attack": forecast.predicted_boss_attack,
            "threat": round(forecast.threat_score, 4),
            "stress": round(self.compensator.acute_stress, 4),
            "effective_skill": round(self.skill_mgr.effective_skill, 4),
            "genome_predictive": round(self.genetics.active["predictive_weight"], 4),
            "genome_reactive": round(self.genetics.active["reactive_weight"], 4),
        })
        self.inputs_logged += 1

    # ── Action probability engine ────────────────────────────────────────────

    def _combat_pressure(self, gs: GameState) -> float:
        hp_risk = np.clip((3.0 - gs.player_hp) / 3.0, 0.0, 1.0)
        proximity = np.clip((36.0 - abs(gs.player_x - gs.boss_x)) / 36.0, 0.0, 1.0)
        boss_pressure = 1.0 if self.temporal.boss_attacking else 0.0
        return float(np.clip(0.45 * hp_risk + 0.30 * proximity + 0.25 * boss_pressure, 0.0, 1.0))

    def _compute_logits(self, gs: GameState, forecast: PredictiveSnapshot) -> np.ndarray:
        """
        Compute raw action logits from game state + temporal context.

        Heuristic signal sources:
          • Spatial distance  (player ↔ boss)
          • Boss attack flag  (temporal motion diff)
          • Player HP         (desperation factor)
          • Boss HP fraction  (finishing-blow factor)
          • NanoCell count    (strategic resource)
        """
        tc   = self.temporal
        genome = self.genetics.active
        logits = np.zeros(N_ACTIONS, dtype=np.float32)

        dist = abs(gs.player_x - gs.boss_x)
        predicted_dist = forecast.predicted_distance
        threat = forecast.threat_score
        safety_bias = self.compensator.safety_bias * genome["stress_weight"]
        aggression = self.compensator.aggression_damping * genome["courage"]
        predictive_weight = genome["predictive_weight"]
        reactive_weight = genome["reactive_weight"]

        # ── ATTACK ──────────────────────────────────────────────────────────
        # Prefer attacking when close and boss isn't visibly lunging
        attack_range_bonus = max(0.0, 1.0 - dist / 60.0)  # peaks at dist=0
        predictive_window = max(0.0, 1.0 - predicted_dist / 64.0)
        attack_threat_penalty = 1.0 + safety_bias * (0.55 if forecast.predicted_boss_attack else 0.0)
        logits[A_ATTACK] = (
            reactive_weight * 2.0 * attack_range_bonus +
            predictive_weight * 1.7 * predictive_window
        ) * aggression / attack_threat_penalty

        # Combo bonus: keep attacking if already in a good rhythm
        if gs.player_hp > 2 and not forecast.predicted_boss_attack:
            logits[A_ATTACK] += 0.5

        # ── DODGE ────────────────────────────────────────────────────────────
        # Prioritise dodge when boss motion detected or player HP is critical
        logits[A_DODGE] = 0.1 + reactive_weight * (3.2 if tc.boss_attacking else 0.0)
        logits[A_DODGE] += predictive_weight * safety_bias * threat * 2.8
        if gs.player_hp <= 2:
            logits[A_DODGE] += 1.0 * safety_bias

        # Hit-flash: player just got hit → dodge immediately
        if tc.player_hit_flash:
            logits[A_DODGE] += 2.0 * safety_bias

        # ── MOVEMENT ─────────────────────────────────────────────────────────
        # Close the gap if too far; back off slightly if boss is attacking
        if predicted_dist > 50:
            # Approach
            if forecast.predicted_player_x < forecast.predicted_boss_x:
                logits[A_RIGHT] = reactive_weight * 1.2 + predictive_weight * 1.1 * aggression
            else:
                logits[A_LEFT]  = reactive_weight * 1.2 + predictive_weight * 1.1 * aggression
        elif predicted_dist < 18 and forecast.predicted_boss_attack:
            # Back off a step to dodge
            if forecast.predicted_player_x < forecast.predicted_boss_x:
                logits[A_LEFT]  = 1.0 + 1.6 * safety_bias
            else:
                logits[A_RIGHT] = 1.0 + 1.6 * safety_bias
        else:
            logits[A_LEFT]  = 0.25 * genome["patience"]
            logits[A_RIGHT] = 0.25 * genome["patience"]

        # ── NANO BOOST ───────────────────────────────────────────────────────
        # Use NanoCell when it matters most: boss nearly dead or player low HP
        if gs.nanocells > 0:
            finishing_blow = gs.boss_visible and gs.boss_hp_frac < 0.35
            desperation    = gs.player_hp <= 2
            predicted_finish = gs.boss_visible and predicted_dist < 28 and threat < 0.35
            if finishing_blow or desperation or predicted_finish:
                logits[A_NANO] = 2.3 + 0.7 * genome["courage"]
            else:
                logits[A_NANO] = 0.25 * genome["patience"]
        else:
            logits[A_NANO] = -2.0      # can't use — strongly suppress

        # ── WAIT ─────────────────────────────────────────────────────────────
        logits[A_NONE] = 0.2 + 0.35 * genome["patience"] + 0.5 * threat

        return logits

    def _effective_reaction_delay(self) -> int:
        base_delay = self.skill_mgr.reaction_delay_frames
        anticipation_credit = max(0, self._last_forecast.horizon_frames - 1)
        return max(0, base_delay - anticipation_credit)

    def _select_action(self, gs: GameState, forecast: PredictiveSnapshot) -> int:
        """
        Convert logits → probability distribution → sampled action,
        with skill-scaled Gaussian noise added to logits before softmax.

        At skill=1.0: noise=0 → pure argmax (deterministic optimal play)
        At skill=0.0: noise>>  → uniform random (hopeless player)
        """
        logits = self._compute_logits(gs, forecast)

        instinct_noise = self.genetics.active["instinct_noise"]
        base_noise = (1.0 - self.skill_mgr.effective_skill) * 3.0
        stress_focus = 1.0 - 0.25 * self.compensator.acute_stress * self.genetics.active["predictive_weight"]
        noise_scale = max(0.15, base_noise * stress_focus + instinct_noise)
        noisy = logits + self._rng.normal(0.0, noise_scale, N_ACTIONS).astype(np.float32)

        probs = _softmax(noisy)
        return int(self._rng.choice(N_ACTIONS, p=probs))

    # ── Phase handlers ───────────────────────────────────────────────────────

    def _handle_splash(self) -> None:
        if self._frame_n % 45 == 0:
            self._tap("a", hold_frames=3)

    def _handle_cinematic(self) -> None:
        # Hold B continuously until the cinematic skip threshold is met
        self._cinematic_b_frames += 1
        if "b" not in self._held:
            self._press("b")
        # Release once skip should have fired (extra margin)
        if self._cinematic_b_frames > CINEMATIC_B_HOLD + 10:
            self._release("b")
            self._cinematic_b_frames = 0

    def _handle_title(self) -> None:
        self._cinematic_b_frames = 0
        self._release_all()
        if self._frame_n % 60 == 0:
            self._tap("start", hold_frames=3)

    def _handle_combat(self, gs: GameState, forecast: PredictiveSnapshot) -> None:
        # Apply reaction-delay lag (lower skill = more frames before acting)
        if self._delay_remain > 0:
            self._delay_remain -= 1
            return

        action = self._select_action(gs, forecast)
        btn    = ACTION_BUTTONS[action]
        hold   = ACTION_HOLD_FRAMES[action]
        self._log_decision(gs, forecast, action, hold)

        if btn:
            self._tap(btn, hold_frames=hold)
        else:
            self._release_all()

        self._delay_remain = self._effective_reaction_delay()

    def _handle_gameover(self) -> None:
        self._release_all()
        if self._frame_n % 90 == 0:
            self._tap("start", hold_frames=3)

    def _handle_transition(self) -> None:
        if self._frame_n % 30 == 0:
            self._tap("a", hold_frames=2)

    # ── Win/loss tracking ────────────────────────────────────────────────────

    def _check_outcomes(self, gs: GameState) -> None:
        prev = self._phase_prev
        curr = gs.phase

        # Combat → title/splash: boss defeated (win)
        if prev == "combat" and curr in ("title", "transition", "splash"):
            if gs.player_hp > 0 or gs.boss_hp_frac == 0.0:
                self.wins += 1
                self.reward_tuner.record(True)
                self.genetics.reward(self.reward_tuner.shape_outcome_reward(True))
                self.genetics.reward_outcome(win=True)
                if self.input_logger is not None:
                    self.input_logger.log_outcome({
                        "frame": self._frame_n,
                        "result": "win",
                        "wins": self.wins,
                        "losses": self.losses,
                        "win_rate": round(self.reward_tuner.win_rate, 4),
                    })

        # Combat → gameover: player died (loss)
        if prev == "combat" and curr == "gameover":
            self.losses += 1
            self.reward_tuner.record(False)
            self.genetics.reward(self.reward_tuner.shape_outcome_reward(False))
            self.genetics.reward_outcome(win=False)
            if self.input_logger is not None:
                self.input_logger.log_outcome({
                    "frame": self._frame_n,
                    "result": "loss",
                    "wins": self.wins,
                    "losses": self.losses,
                    "win_rate": round(self.reward_tuner.win_rate, 4),
                })

        # Gameover → title: respawned after loss (already counted)
        self._phase_prev = curr

    def _reward_live_adaptation(self, gs: GameState, forecast: PredictiveSnapshot) -> None:
        if self._prev_state is None or gs.phase != "combat":
            self._prev_state = gs
            return

        reward = 0.0
        if gs.player_hp > self._prev_state.player_hp:
            reward += 0.2
        if gs.player_hp < self._prev_state.player_hp:
            reward -= 0.7
        if gs.boss_hp_frac < self._prev_state.boss_hp_frac:
            reward += 0.9
        if forecast.predicted_boss_attack and not self.temporal.player_hit_flash:
            reward += 0.15
        reward -= 0.10 * self.compensator.acute_stress
        self.genetics.reward(self.reward_tuner.shape_live_reward(reward))
        self._prev_state = gs

    def export_learning_state(self) -> dict:
        return {
            "genetics": self.genetics.export_state(),
            "skill": self.skill_mgr.base_skill,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate": self.reward_tuner.win_rate,
        }

    def import_learning_state(self, payload: dict) -> bool:
        try:
            genetics = payload["genetics"]
        except (KeyError, TypeError):
            return False
        return self.genetics.import_state(genetics)

    # ── Public tick ─────────────────────────────────────────────────────────

    def tick(self, shades: np.ndarray) -> GameState:
        """
        Called once per emulator frame, AFTER pyboy.tick() has advanced
        the game by one frame.

        1. Update temporal context  (game made its move)
        2. Analyse framebuffer      (what does the screen show now?)
        3. Select & inject input    (player makes its move)
        4. Handle pending releases
        5. Record performance metrics

        Returns the current GameState for external logging / recording.
        """
        t0 = time.perf_counter()
        self._inject_stress_delay()

        self._frame_n += 1

        # Game has already advanced — observe the result
        self.temporal.update(shades)
        gs = analyze(shades)
        self.predictor.update(gs)

        combat_pressure = self._combat_pressure(gs) if gs.phase == "combat" else 0.0
        self.compensator.update(self.skill_mgr.avg_frame_ms, combat_pressure)
        forecast = self.predictor.forecast(gs, self.temporal, self.compensator)
        self._last_forecast = forecast

        # Track wins/losses
        self._check_outcomes(gs)
        self._reward_live_adaptation(gs, forecast)

        # Handle any pending button auto-release
        if self._pending_release is not None:
            btn, release_at = self._pending_release
            if self._frame_n >= release_at:
                self._release(btn)
                self._pending_release = None

        # Dispatch to phase handler
        if gs.phase == "splash":
            self._handle_splash()
        elif gs.phase == "cinematic":
            self._handle_cinematic()
        elif gs.phase == "title":
            self._handle_title()
        elif gs.phase == "combat":
            self._handle_combat(gs, forecast)
        elif gs.phase == "gameover":
            self._handle_gameover()
        else:
            self._handle_transition()

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        self.skill_mgr.record(elapsed_ms)

        return gs

    # ── Stats ─────────────────────────────────────────────────────────────────

    @property
    def stats(self) -> dict:
        genome = self.genetics.active
        return {
            "frame":           self._frame_n,
            "wins":            self.wins,
            "losses":          self.losses,
            "win_rate":        round(self.reward_tuner.win_rate, 4),
            "effective_skill": round(self.skill_mgr.effective_skill, 4),
            "base_skill":      self.skill_mgr.base_skill,
            "avg_frame_ms":    round(self.skill_mgr.avg_frame_ms, 3),
            "reaction_lag":    self.skill_mgr.reaction_delay_frames,
            "comp_lag":        self._effective_reaction_delay(),
            "stress":          round(self.compensator.stress, 4),
            "acute_stress":    round(self.compensator.acute_stress, 4),
            "anticipation":    self._last_forecast.horizon_frames,
            "threat":          round(self._last_forecast.threat_score, 4),
            "genome_predictive": round(genome["predictive_weight"], 4),
            "genome_reactive":   round(genome["reactive_weight"], 4),
            "genome_courage":    round(genome["courage"], 4),
            "genome_generation": self.genetics.generations,
            "inputs_logged":    self.inputs_logged,
        }
