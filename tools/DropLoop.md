# DropLoop

`tools/DropLoop.py` is a standalone recovery and reintroduction controller for cyclic processes.

Primary use:

- assess decay, integrity, concurrency, electrical-stress, and frequency metrics,
- compute a proportionate reintroduction offset,
- trigger a repair step before retry when risk exceeds tolerance,
- record a machine-readable attempt history for later inspection.

Core types:

- `DropLoopMetrics`: runtime state for one attempt.
- `DropLoopPolicy`: retry count and offset shaping rules.
- `DropLoopDecision`: calculated risk and offset for a single cycle.
- `DropLoopController`: generic executor around any callable process.

Minimal integration pattern:

```python
from tools.DropLoop import DropLoopController, DropLoopMetrics

controller = DropLoopController()
result, report = controller.run(
    operation=lambda attempt: run_process(),
    metrics_provider=lambda attempt, result, error: DropLoopMetrics(
        decay_factor=0.12,
        datastream_integrity=0.97,
        concurrency_load=0.18,
        electrical_stress=0.09,
        cycle_frequency_hz=2.0,
    ),
    success_evaluator=lambda result: result.ok,
)
```

Adaptation guidance:

- For IO-heavy software, drive `concurrency_load` from queue depth or worker saturation.
- For media/data pipelines, drive `datastream_integrity` from validation and warning counts.
- For hardware-facing or timing-sensitive systems, drive `electrical_stress` from temperature, voltage, jitter, or comparable safety metrics.
- For long-running orchestration, persist `report.to_dict()` and use it as the next cycle's prior-state signal.
