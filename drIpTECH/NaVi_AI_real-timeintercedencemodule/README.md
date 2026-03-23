NaVi — Real-time Interceding AI Controller
=========================================

Purpose
-------

NaVi is a genetically-evolving, memory-storing agent that intercedes live AI API calls to guide and bias outputs toward user preferences, context, and evolving policies.

Goals

- Act as a low-latency proxy between a client and upstream AI model APIs.
- Log requests/responses and store condensed memories in a local store.
- Provide programmable hooks to mutate prompts/responses in real-time.
- Run a genetic evolution loop over candidate policy mutations to optimize for user-specified metrics.

Quickstart (prototype)
----------------------

1. Install dependencies: `pip install -r requirements.txt`
2. Start NaVi proxy (example):

   ```powershell
   # set upstream API and key
   $env:UPSTREAM_API_URL = 'https://external.api.recraft.ai/v1/images/generations'
   $env:UPSTREAM_API_KEY = '<your-key>'
   python navi_proxy.py --listen 127.0.0.1:8080
   ```

3. Point client to `http://127.0.0.1:8080` instead of upstream. NaVi will forward, log, and allow hooks.

Files

- `navi_proxy.py` — async proxy, intercept hooks, SQLite logging.
- `genetic.py` — genetic algorithm stubs for evolving small policy scripts/parameters.
- `requirements.txt` — project-scoped async proxy Python dependencies.

Workspace manifest

- [tools/dependency_manifests/navi_proxy.json](tools/dependency_manifests/navi_proxy.json) tracks this stack separately from the shared workspace venv.

Next steps

- Define concrete metrics (preference fidelity, latency, safety) and user feedback loop.
- Implement policy encoding and mutation operators used by the genetic engine.
- Add a small web UI for visualization and manual selection.
