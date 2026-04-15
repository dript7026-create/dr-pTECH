# Experiential Genesis Progress

## 2026-03-13

- Created the initial EG home under `subdriptech/ExperientialGenesis`.
- Defined EG as a safe, opt-in hypermanager for approved workspace modules instead of a machine-wide arbitrary process controller.
- Added a deterministic coherency-driven orchestration core with authorization gating, adapter registration, and consensus render synthesis.
- Added sample adapters representing strategic and runtime game modules so EG can centralize simulation decisions without broad OS control.
- Added focused tests and a demo entry point.
- Added JSONL tick-history export so EG runs can be replayed and inspected deterministically.
- Added a small CLI control surface with built-in `default`, `storm`, and `calm` presets plus optional snapshot printing.

## Next Targets

- connect EG outputs to additional approved workspace modules
- expose a small control surface for scenario presets and runtime inspection
- add richer replay viewers and persistent state rehydration from saved history

## 2026-03-25

- Added a dedicated KaijuGaiden runtime adapter plus HOPE runtime contract export so EG can guide the boss-runtime bridge through approved, deterministic parameters instead of ad hoc JSON alone.
- Extended the EG runner and tests to cover KaijuGaiden adapter registration and contract emission.