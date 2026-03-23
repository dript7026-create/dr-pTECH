from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from typing import Callable, Generic, TypeVar


ResultT = TypeVar("ResultT")


@dataclass(slots=True)
class DropLoopMetrics:
    decay_factor: float
    datastream_integrity: float
    concurrency_load: float
    electrical_stress: float
    cycle_frequency_hz: float
    disturbance_tolerance: float = 0.35


@dataclass(slots=True)
class DropLoopDecision:
    offset_seconds: float
    repair_required: bool
    risk_score: float
    stability_score: float
    rationale: str


@dataclass(slots=True)
class DropLoopPolicy:
    max_attempts: int = 3
    base_offset_seconds: float = 0.12
    max_offset_seconds: float = 1.5
    min_cycle_frequency_hz: float = 0.25
    repair_cooldown_scale: float = 0.65


@dataclass(slots=True)
class DropLoopAttemptRecord:
    attempt: int
    offset_seconds: float
    repair_applied: bool
    risk_score: float
    stability_score: float
    rationale: str
    succeeded: bool


@dataclass(slots=True)
class DropLoopRunReport:
    succeeded: bool
    attempts: list[DropLoopAttemptRecord]
    final_result_summary: str

    def to_dict(self) -> dict:
        return {
            "succeeded": self.succeeded,
            "attempts": [asdict(attempt) for attempt in self.attempts],
            "final_result_summary": self.final_result_summary,
        }


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


class DropLoopController(Generic[ResultT]):
    def __init__(self, policy: DropLoopPolicy | None = None) -> None:
        self.policy = policy or DropLoopPolicy()

    def assess(self, metrics: DropLoopMetrics) -> DropLoopDecision:
        frequency = max(metrics.cycle_frequency_hz, self.policy.min_cycle_frequency_hz)
        risk_score = clamp(
            metrics.decay_factor * 0.30
            + (1.0 - metrics.datastream_integrity) * 0.30
            + metrics.concurrency_load * 0.20
            + metrics.electrical_stress * 0.20,
            0.0,
            1.0,
        )
        stability_score = clamp(1.0 - risk_score, 0.0, 1.0)
        repair_required = risk_score > metrics.disturbance_tolerance or metrics.datastream_integrity < 0.92
        offset_seconds = self.policy.base_offset_seconds + (risk_score / frequency) * self.policy.repair_cooldown_scale
        offset_seconds = clamp(offset_seconds, self.policy.base_offset_seconds, self.policy.max_offset_seconds)
        rationale = (
            f"risk={risk_score:.3f}, stability={stability_score:.3f}, "
            f"frequency={frequency:.3f}Hz, repair_required={repair_required}"
        )
        return DropLoopDecision(
            offset_seconds=offset_seconds,
            repair_required=repair_required,
            risk_score=risk_score,
            stability_score=stability_score,
            rationale=rationale,
        )

    def run(
        self,
        operation: Callable[[int], ResultT],
        metrics_provider: Callable[[int, ResultT | None, Exception | None], DropLoopMetrics],
        success_evaluator: Callable[[ResultT], bool],
        repair_action: Callable[[int, DropLoopDecision, ResultT | None, Exception | None], None] | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        result_summarizer: Callable[[ResultT | None, Exception | None], str] | None = None,
    ) -> tuple[ResultT | None, DropLoopRunReport]:
        attempts: list[DropLoopAttemptRecord] = []
        last_result: ResultT | None = None
        last_error: Exception | None = None

        for attempt in range(1, self.policy.max_attempts + 1):
            try:
                last_result = operation(attempt)
                last_error = None
            except Exception as exc:  # pragma: no cover - defensive runtime path
                last_error = exc
                last_result = None

            metrics = metrics_provider(attempt, last_result, last_error)
            decision = self.assess(metrics)
            succeeded = last_error is None and last_result is not None and success_evaluator(last_result)
            attempts.append(
                DropLoopAttemptRecord(
                    attempt=attempt,
                    offset_seconds=decision.offset_seconds,
                    repair_applied=decision.repair_required and not succeeded,
                    risk_score=decision.risk_score,
                    stability_score=decision.stability_score,
                    rationale=decision.rationale,
                    succeeded=succeeded,
                )
            )
            if succeeded:
                summary = result_summarizer(last_result, None) if result_summarizer else "completed"
                return last_result, DropLoopRunReport(True, attempts, summary)
            if attempt == self.policy.max_attempts:
                break
            if decision.repair_required and repair_action is not None:
                repair_action(attempt, decision, last_result, last_error)
            sleep_fn(decision.offset_seconds)

        if result_summarizer:
            summary = result_summarizer(last_result, last_error)
        elif last_error is not None:
            summary = f"failed: {last_error}"
        else:
            summary = "failed"
        return last_result, DropLoopRunReport(False, attempts, summary)
