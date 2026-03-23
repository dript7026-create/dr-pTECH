"""Engine integration hooks for GODHAX.aig.

Provide simple, engine-agnostic functions that developers should call from
their engine's tick/update events. Integrators must wire these functions into
their own game loop (this package does not modify any third-party engines).
"""
import os
from typing import Dict, Any
from .core import AdaptiveAgent
from .db import get_store


# Default opt-in flag: developers must explicitly enable GODHAX for a project.
def is_enabled() -> bool:
    return os.getenv("GODHAX_ENABLED", "false").lower() in ("1", "true", "yes")


def create_agent_for_session(session_id: str, **kwargs) -> AdaptiveAgent:
    if not is_enabled():
        raise RuntimeError("GODHAX is not enabled for this project. Set GODHAX_ENABLED=1 to opt in.")
    agent = AdaptiveAgent(session_id, **kwargs)
    return agent


def tick_update(session_id: str, observation: Dict[str, Any]) -> Dict[str, Any]:
    """Call from engine each tick with a serializable `observation` dict.

    Returns the agent action dict which integrators should map to engine
    commands. This function keeps everything in-process and session-scoped.
    """
    store = get_store()
    session = store.get_session(session_id)
    if session is None:
        store.create_session(session_id)
        session = store.get_session(session_id)

    # Lazily create agent instance and keep in session
    if "_agent_obj" not in session:
        session["_agent_obj"] = AdaptiveAgent(session_id)

    agent = session["_agent_obj"]
    agent.observe(observation)
    return agent.act()


def clear_session(session_id: str):
    get_store().clear_session(session_id)
