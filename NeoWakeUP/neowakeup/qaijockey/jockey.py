"""QAIJockey runner core migrated into NeoWakeUP."""

import time
from collections import deque
from dataclasses import dataclass
from typing import Deque, Optional

import numpy as np

from ..relationships import EgoSphereSocialModel
from .profiles import ActionSpec, GameProfile, GameState


class SkillManager:
    BUDGET_MS = 16.0
    WARMUP_FRAMES = 10

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
    def __init__(self, budget_ms: float = 16.0):
        self.budget_ms = budget_ms
        self._stress_hist: Deque[float] = deque(maxlen=90)

    def update(self, avg_frame_ms: float, combat_pressure: float) -> None:
        perf_load = np.clip((avg_frame_ms - self.budget_ms) / max(self.budget_ms, 1.0), 0.0, 2.0)
        stress = np.clip(0.65 * perf_load + 0.35 * combat_pressure, 0.0, 1.0)
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
    def __init__(self):
        self._states: Deque[GameState] = deque(maxlen=12)

    def update(self, gs: GameState) -> None:
        self._states.append(gs)

    def _velocity(self, attr: str) -> float:
        if len(self._states) < 2:
            return 0.0
        recent = list(self._states)[-4:]
        diffs = [getattr(b, attr) - getattr(a, attr) for a, b in zip(recent[:-1], recent[1:])]
        return float(np.mean(diffs)) if diffs else 0.0

    def forecast(self, gs: GameState, compensator: PerformanceCompensator) -> PredictiveSnapshot:
        horizon = compensator.anticipation_frames
        player_vx = self._velocity("player_x")
        boss_vx = self._velocity("opponent_x")
        predicted_player_x = float(np.clip(gs.player_x + player_vx * horizon, 0, 159))
        predicted_boss_x = float(np.clip(gs.opponent_x + boss_vx * horizon, 0, 159))
        predicted_distance = abs(predicted_player_x - predicted_boss_x)
        boss_momentum = max(0.0, abs(boss_vx) / 4.0)
        collapse_risk = np.clip((32.0 - predicted_distance) / 32.0, 0.0, 1.0)
        threat_score = float(np.clip(0.50 * gs.danger + 0.30 * collapse_risk + 0.20 * boss_momentum, 0.0, 1.0))
        predicted_boss_attack = gs.predicted_attack_hint or threat_score > (0.38 - 0.08 * compensator.acute_stress)
        return PredictiveSnapshot(horizon, predicted_player_x, predicted_boss_x, predicted_distance, predicted_boss_attack, threat_score)


class GeneticPolicyMixer:
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


def _softmax(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - x.max())
    return e / e.sum()


class QAIJockey:
    def __init__(
        self,
        emulator,
        profile: GameProfile,
        skill: float = 0.75,
        stress_delay_ms: float = 0.0,
        stress_jitter_ms: float = 0.0,
        input_logger=None,
        tune_window: int = 12,
    ):
        self.emu = emulator
        self.profile = profile
        self.actions: list[ActionSpec] = list(profile.action_specs)
        self.skill_mgr = SkillManager(base_skill=skill)
        self.compensator = PerformanceCompensator(budget_ms=self.skill_mgr.BUDGET_MS)
        self.predictor = PredictiveEngine()
        self._rng = np.random.default_rng()
        self.genetics = GeneticPolicyMixer(self._rng)
        self.reward_tuner = OutcomeRewardTuner(window=tune_window)
        self.relationships = EgoSphereSocialModel()
        self.opponent_id = getattr(profile, "opponent_id", "opponent")
        self.opponent_archetype = getattr(profile, "opponent_archetype", "unknown")
        self.stress_delay_ms = max(0.0, float(stress_delay_ms))
        self.stress_jitter_ms = max(0.0, float(stress_jitter_ms))
        self.input_logger = input_logger
        self._held: set[str] = set()
        self._pending_release: Optional[tuple[str, int]] = None
        self._delay_remain = 0
        self._frame_n = 0
        self._phase_prev = "unknown"
        self._prev_state: Optional[GameState] = None
        self._last_forecast = PredictiveSnapshot()
        self.wins = 0
        self.losses = 0
        self.inputs_logged = 0

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

    def _relationship_snapshot(self) -> dict:
        return self.relationships.snapshot(self.opponent_id, self.opponent_archetype)

    def _find_action(self, token: str) -> Optional[ActionSpec]:
        normalized = token.strip().lower()
        for spec in self.actions:
            if spec.label.lower() == normalized:
                return spec
            if spec.button and spec.button.lower() == normalized:
                return spec
        return None

    def _log_decision(self, gs: GameState, forecast: PredictiveSnapshot, spec: ActionSpec) -> None:
        if self.input_logger is None:
            return
        social = self._relationship_snapshot()
        self.input_logger.log_input({
            "frame": self._frame_n,
            "profile": self.profile.name,
            "phase": gs.phase,
            "action": spec.label,
            "button": spec.button,
            "hold_frames": spec.hold_frames,
            "player_progress": round(gs.player_progress, 4),
            "opponent_progress": round(gs.opponent_progress, 4),
            "resource": round(gs.resource, 4),
            "player_x": round(gs.player_x, 3),
            "opponent_x": round(gs.opponent_x, 3),
            "danger": round(gs.danger, 4),
            "opportunity": round(gs.opportunity, 4),
            "predicted_distance": round(forecast.predicted_distance, 3),
            "predicted_boss_attack": forecast.predicted_boss_attack,
            "threat": round(forecast.threat_score, 4),
            "stress": round(self.compensator.acute_stress, 4),
            "effective_skill": round(self.skill_mgr.effective_skill, 4),
            "genome_predictive": round(self.genetics.active["predictive_weight"], 4),
            "genome_reactive": round(self.genetics.active["reactive_weight"], 4),
            "social_rivalry": round(social["rivalry"], 4),
            "social_fear": round(social["fear"], 4),
            "social_dominance": round(social["dominance"], 4),
            "meta": gs.meta,
        })
        self.inputs_logged += 1

    def _combat_pressure(self, gs: GameState) -> float:
        hp_risk = np.clip(1.0 - gs.player_progress, 0.0, 1.0)
        proximity = np.clip((36.0 - abs(gs.player_x - gs.opponent_x)) / 36.0, 0.0, 1.0)
        opponent_pressure = 1.0 if gs.predicted_attack_hint else 0.0
        return float(np.clip(0.40 * hp_risk + 0.25 * proximity + 0.35 * max(gs.danger, opponent_pressure), 0.0, 1.0))

    def _compute_logits(self, gs: GameState, forecast: PredictiveSnapshot) -> np.ndarray:
        genome = self.genetics.active
        social = self._relationship_snapshot()
        logits = np.zeros(len(self.actions), dtype=np.float32)
        dist = abs(gs.player_x - gs.opponent_x)
        predicted_dist = forecast.predicted_distance
        threat = forecast.threat_score
        safety_bias = self.compensator.safety_bias * genome["stress_weight"] * (1.0 + 0.25 * social["fear"])
        aggression = self.compensator.aggression_damping * genome["courage"] * (1.0 + 0.20 * social["dominance"])
        predictive_weight = genome["predictive_weight"] * (1.0 + 0.10 * social["adaptability"])
        reactive_weight = genome["reactive_weight"] * (1.0 + 0.15 * social["rivalry"])
        player_low = gs.player_progress < 0.35
        target_dir_x = 0
        if gs.opponent_visible:
            if forecast.predicted_boss_attack or gs.danger > 0.55:
                target_dir_x = -1 if forecast.predicted_player_x < forecast.predicted_boss_x else 1
            elif predicted_dist > 46:
                target_dir_x = 1 if forecast.predicted_player_x < forecast.predicted_boss_x else -1

        for idx, spec in enumerate(self.actions):
            if spec.role == "primary":
                attack_range_bonus = max(0.0, 1.0 - dist / 60.0)
                predictive_window = max(0.0, 1.0 - predicted_dist / 64.0)
                attack_threat_penalty = 1.0 + safety_bias * (0.55 if forecast.predicted_boss_attack else 0.0)
                logits[idx] = (
                    reactive_weight * 2.0 * attack_range_bonus
                    + predictive_weight * 1.7 * predictive_window
                    + gs.opportunity * 1.2
                ) * aggression / attack_threat_penalty
                if gs.player_progress > 0.4 and not forecast.predicted_boss_attack:
                    logits[idx] += 0.35 + 0.15 * social["dominance"]
            elif spec.role in ("secondary", "evade"):
                logits[idx] = 0.1 + reactive_weight * (2.2 * threat + 1.5 * gs.danger)
                if player_low:
                    logits[idx] += 0.9 * safety_bias
                if gs.player_hit_flash:
                    logits[idx] += 1.6 * safety_bias
            elif spec.role == "move":
                if spec.axis == "x":
                    if target_dir_x == 0:
                        logits[idx] = 0.2 * genome["patience"] + 0.2 * (1.0 - gs.scene_motion)
                    elif spec.direction == target_dir_x:
                        logits[idx] = 0.6 + reactive_weight * 1.2 + predictive_weight * 0.9 * aggression
                    else:
                        logits[idx] = 0.12 + 0.3 * genome["patience"]
                else:
                    logits[idx] = 0.25 + 0.25 * genome["patience"] + 0.25 * (1.0 - gs.scene_motion)
                    logits[idx] += 0.2 if int(self._frame_n / 30) % 2 == (0 if spec.direction < 0 else 1) else 0.0
            elif spec.role == "resource":
                logits[idx] = 0.15 + gs.resource * 2.2 + gs.opportunity * 0.8
                if player_low:
                    logits[idx] += 0.4
            elif spec.role == "menu_confirm":
                logits[idx] = 0.1 + (0.8 if gs.phase not in ("combat", "active") else -0.8)
            elif spec.role == "menu_back":
                logits[idx] = -0.15 + (0.5 if gs.phase not in ("combat", "active") else -0.8)
            elif spec.role == "wait":
                logits[idx] = 0.25 + 0.35 * genome["patience"] + 0.5 * threat + 0.1 * social["fear"]
            else:
                logits[idx] = 0.1
        return logits

    def _effective_reaction_delay(self) -> int:
        return max(0, self.skill_mgr.reaction_delay_frames - max(0, self._last_forecast.horizon_frames - 1))

    def _select_action(self, gs: GameState, forecast: PredictiveSnapshot) -> ActionSpec:
        logits = self._compute_logits(gs, forecast)
        instinct_noise = self.genetics.active["instinct_noise"]
        base_noise = (1.0 - self.skill_mgr.effective_skill) * 3.0
        stress_focus = 1.0 - 0.25 * self.compensator.acute_stress * self.genetics.active["predictive_weight"]
        noise_scale = max(0.15, base_noise * stress_focus + instinct_noise)
        noisy = logits + self._rng.normal(0.0, noise_scale, len(self.actions)).astype(np.float32)
        probs = _softmax(noisy)
        index = int(self._rng.choice(len(self.actions), p=probs))
        return self.actions[index]

    def _apply_action(self, gs: GameState, forecast: PredictiveSnapshot, spec: ActionSpec) -> None:
        self.relationships.observe_action(
            self.opponent_id,
            self.opponent_archetype,
            spec.label,
            forecast.threat_score,
            gs.player_progress,
            gs.opponent_progress,
        )
        self._log_decision(gs, forecast, spec)
        if spec.button:
            self._tap(spec.button, hold_frames=spec.hold_frames)
        else:
            self._release_all()
        self._delay_remain = self._effective_reaction_delay()

    def _handle_active(self, gs: GameState, forecast: PredictiveSnapshot) -> None:
        if self._delay_remain > 0:
            self._delay_remain -= 1
            return
        spec = self._select_action(gs, forecast)
        self._apply_action(gs, forecast, spec)

    def _check_outcomes(self, gs: GameState) -> None:
        outcome = self.profile.evaluate_outcome(self._phase_prev, gs)
        if outcome == "win":
            self.wins += 1
            social = self.relationships.observe_outcome(self.opponent_id, self.opponent_archetype, True)
            self.reward_tuner.record(True)
            self.genetics.reward(self.reward_tuner.shape_outcome_reward(True))
            self.genetics.reward_outcome(win=True)
            if self.input_logger is not None:
                self.input_logger.log_outcome({
                    "frame": self._frame_n,
                    "profile": self.profile.name,
                    "result": "win",
                    "wins": self.wins,
                    "losses": self.losses,
                    "win_rate": round(self.reward_tuner.win_rate, 4),
                    "social_dominance": round(social["dominance"], 4),
                })
        elif outcome == "loss":
            self.losses += 1
            social = self.relationships.observe_outcome(self.opponent_id, self.opponent_archetype, False)
            self.reward_tuner.record(False)
            self.genetics.reward(self.reward_tuner.shape_outcome_reward(False))
            self.genetics.reward_outcome(win=False)
            if self.input_logger is not None:
                self.input_logger.log_outcome({
                    "frame": self._frame_n,
                    "profile": self.profile.name,
                    "result": "loss",
                    "wins": self.wins,
                    "losses": self.losses,
                    "win_rate": round(self.reward_tuner.win_rate, 4),
                    "social_fear": round(social["fear"], 4),
                })
        self._phase_prev = gs.phase

    def _reward_live_adaptation(self, gs: GameState, forecast: PredictiveSnapshot) -> None:
        if self._prev_state is None or gs.phase not in ("combat", "active"):
            self._prev_state = gs
            return
        reward = 0.0
        if gs.player_progress > self._prev_state.player_progress:
            reward += 0.25
        if gs.player_progress < self._prev_state.player_progress:
            reward -= 0.7
        if gs.opponent_progress < self._prev_state.opponent_progress:
            reward += 0.9
        reward += 0.20 * (gs.opportunity - self._prev_state.opportunity)
        reward -= 0.15 * max(0.0, gs.danger - self._prev_state.danger)
        if forecast.predicted_boss_attack and not gs.player_hit_flash:
            reward += 0.10
        reward -= 0.10 * self.compensator.acute_stress
        self.genetics.reward(self.reward_tuner.shape_live_reward(reward))
        self._prev_state = gs

    def export_learning_state(self) -> dict:
        return {
            "profile": self.profile.name,
            "genetics": self.genetics.export_state(),
            "relationships": self.relationships.export_state(),
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
        ok = self.genetics.import_state(genetics)
        relationships = payload.get("relationships") if isinstance(payload, dict) else None
        if isinstance(relationships, dict):
            self.relationships.import_state(relationships)
        return ok

    def tick(self, shades: np.ndarray) -> GameState:
        t0 = time.perf_counter()
        self._inject_stress_delay()
        self._frame_n += 1
        gs = self.profile.analyze_frame(shades)
        self.predictor.update(gs)
        combat_pressure = self._combat_pressure(gs) if gs.phase in ("combat", "active") else 0.0
        self.compensator.update(self.skill_mgr.avg_frame_ms, combat_pressure)
        forecast = self.predictor.forecast(gs, self.compensator)
        self._last_forecast = forecast
        self._check_outcomes(gs)
        self._reward_live_adaptation(gs, forecast)
        if self._pending_release is not None:
            btn, release_at = self._pending_release
            if self._frame_n >= release_at:
                self._release(btn)
                self._pending_release = None

        forced = self.profile.forced_action(gs, self._frame_n)
        if forced:
            spec = self._find_action(forced)
            if spec is not None:
                self._apply_action(gs, forecast, spec)
            elif forced.strip().lower() != "wait":
                self._tap(forced.strip().lower(), hold_frames=3)
        elif gs.phase in ("combat", "active"):
            self._handle_active(gs, forecast)
        else:
            self._release_all()

        self.skill_mgr.record((time.perf_counter() - t0) * 1000.0)
        return gs

    @property
    def stats(self) -> dict:
        genome = self.genetics.active
        social = self._relationship_snapshot()
        return {
            "profile": self.profile.name,
            "frame": self._frame_n,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate": round(self.reward_tuner.win_rate, 4),
            "effective_skill": round(self.skill_mgr.effective_skill, 4),
            "base_skill": self.skill_mgr.base_skill,
            "avg_frame_ms": round(self.skill_mgr.avg_frame_ms, 3),
            "reaction_lag": self.skill_mgr.reaction_delay_frames,
            "comp_lag": self._effective_reaction_delay(),
            "stress": round(self.compensator.stress, 4),
            "acute_stress": round(self.compensator.acute_stress, 4),
            "anticipation": self._last_forecast.horizon_frames,
            "threat": round(self._last_forecast.threat_score, 4),
            "genome_predictive": round(genome["predictive_weight"], 4),
            "genome_reactive": round(genome["reactive_weight"], 4),
            "genome_courage": round(genome["courage"], 4),
            "genome_generation": self.genetics.generations,
            "inputs_logged": self.inputs_logged,
            "social_rivalry": round(social["rivalry"], 4),
            "social_fear": round(social["fear"], 4),
            "social_dominance": round(social["dominance"], 4),
        }
