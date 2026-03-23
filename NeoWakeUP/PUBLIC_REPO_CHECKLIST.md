# NeoWakeUP Public Repository Checklist

Prepared items:

- Dedicated runtime directory with top-level entry points.
- Local API server entry point for external tooling.
- Control hub UI entry point.
- Recraft manifests for primary and finalization GUI passes.
- Persistent state isolated under `NeoWakeUP/state/`.

Before pushing publicly:

1. Generate the Recraft assets after loading `RECRAFT_API_KEY`, then verify there are no accidental proprietary prompts or private paths embedded in logs.
2. Review `NeoWakeUP/state/` and either exclude it or replace it with sanitized sample state files.
3. Decide whether `KaijuGaiden` compatibility wrappers should remain in the public repo or move to a separate integration example.
4. Add screenshots from the control hub once the generated GUI pass assets are integrated.
5. Check license compatibility for any external runtime dependencies you intend to advertise.