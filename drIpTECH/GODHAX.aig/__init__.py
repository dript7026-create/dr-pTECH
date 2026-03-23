"""GODHAX.aig

Safe, in-house adaptive AI scaffold for game integration.
"""

from .core import AdaptiveAgent
from .evolution import evolve_agent_population
from .auth import is_authorized_admin, require_admin

__all__ = [
    "AdaptiveAgent",
    "evolve_agent_population",
    "is_authorized_admin",
    "require_admin",
]
