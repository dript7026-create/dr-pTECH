# Experiential Genesis

Experiential Genesis (EG) is a safe, opt-in hypermanager for the `drIpTECH` workspace.

It does **not** attempt to arbitrarily alter any running application on the machine. Instead, it centralizes approved in-process adapters behind an authorization hierarchy and drives them through a deterministic coherency tick.

## Scope

EG is designed to unify simulation and game-play modules that explicitly register with it, including:

- engine-side systems
- simulation-side systems
- AI-side policy and state synthesis
- deterministic consensus render planning

## Core Model

Each tick performs five stages:

1. collect adapter state
2. compute frequency perception coherency fields
3. produce bounded change plans for authorized adapters
4. synthesize a consensus particle field and render frame
5. apply only approved mutations to registered adapters

## Safety Model

- only registered adapters can be changed
- each adapter declares its authorization scope and mutable domains
- EG never injects into or tampers with arbitrary OS processes
- all consensus output is deterministic from tick input and seed

## Layout

- `experiential_genesis/authorization.py`: authorization hierarchy and mutation policy
- `experiential_genesis/coherency.py`: frequency perception coherency math
- `experiential_genesis/adapters.py`: adapter protocol and sample adapters
- `experiential_genesis/consensus.py`: particle-field and frame synthesis
- `experiential_genesis/hypermanager.py`: central EG orchestrator
- `tests/test_experiential_genesis.py`: focused behavioral tests

## Run Demo

```powershell
python subdriptech/ExperientialGenesis/run_experiential_genesis.py
python subdriptech/ExperientialGenesis/run_experiential_genesis.py --preset storm --ticks 5 --show-snapshots
python subdriptech/ExperientialGenesis/run_experiential_genesis.py --history-out subdriptech/ExperientialGenesis/state/eg_history.jsonl
python subdriptech/ExperientialGenesis/run_experiential_genesis.py --include-kaijugaiden --scene-id thunder_reef_duel --ticks 4
python subdriptech/ExperientialGenesis/run_experiential_genesis.py --include-kaijugaiden --preset storm --contract-out KaijuGaiden/runtime/hope_runtime_contract.json --scene-id thunder_reef_duel --scene-type boss-rush
```

## Control Surface

- `--ticks`: number of deterministic EG ticks to run
- `--preset`: `default`, `storm`, or `calm`
- `--show-snapshots`: print adapter metrics after each tick
- `--history-out`: write consensus history as JSONL for replay or inspection
- `--include-kaijugaiden`: register the KaijuGaiden runtime adapter
- `--contract-out`: export a KaijuGaiden HOPE runtime contract JSON that `kaijugaiden.c` can load through its existing bridge path
- `--scene-id`: set the exported KaijuGaiden runtime scene id
- `--scene-type`: set the exported KaijuGaiden runtime scene type

## KaijuGaiden Bridge

When the KaijuGaiden adapter is enabled, EG can emit a deterministic runtime contract into `KaijuGaiden/runtime/hope_runtime_contract.json`.
That contract now includes a timeline projection layer with project-progress, predictive-vision, derivative-final-state, and refinement-depth seeds that KaijuGaiden can turn into live playback and combat adaptation.

That contract is designed to be consumed directly by `KaijuGaiden/kaijugaiden.c`, where it can influence:

- boss movement pressure and spacing
- silhouette hit activation density
- debris, after-image, and healing FX behavior
- environment-driven regeneration through moisture and air-chemistry relations
- toxicant and insolvent-impurity contamination across encounter ecology
- atmospheric corrosives, irritants, respiratory burden, hemoneural stress, plasmic instability, and matter-tension stasis
- audio and render reactivity

## Next Expansion

- add more workspace adapters for approved modules
- bridge consensus output into authored mission and UI layers
- add stronger replay inspection and preset authoring beyond the built-in demo set
