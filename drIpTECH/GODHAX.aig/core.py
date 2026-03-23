"""Core AdaptiveAgent for GODHAX.aig (safe, in-memory, in-house use only).

This module provides an `AdaptiveAgent` class that maintains an ephemeral
per-session parameter vector (genome) and exposes tick-level `observe` and
`act` methods for integration with a game engine. It intentionally does NOT
include any networking, platform intrusion, or hacking capabilities.
"""
from typing import Any, Dict, Callable
import threading
import numpy as np
from .db import get_store


class AdaptiveAgent:
    """A minimal, tick-level adaptive agent.

    Usage: create one `AdaptiveAgent(session_id)` per gameplay session or per
    in-game AI instance depending on your integration strategy.
    """

    def __init__(self, session_id: str, genome_size: int = 16, params: Dict = None):
        self.session_id = session_id
        self.genome_size = genome_size
        self.lock = threading.Lock()
        self.store = get_store()

        # Load or initialize per-session genome
        session = self.store.get_session(session_id)
        if session is None:
            self.store.create_session(session_id)
            session = self.store.get_session(session_id)

        if "genome" not in session:
            session["genome"] = np.random.randn(self.genome_size).tolist()

        self.genome = np.array(session["genome"])
        self.params = params or {}

    def observe(self, observation: Dict[str, Any]):
        """Receive structured game observation data (developer-defined).

        Observation format is intentionally generic — the integrator maps
        engine-specific data into this dict format.
        """
        # Integrators should implement feature extraction and pass numeric
        # arrays or scalar values. Here we just store last observation.
        with self.lock:
            self.last_observation = observation

    def act(self) -> Dict[str, Any]:
        """Return an action dict decided from current genome and last observation.

        This is a simple placeholder policy: dot(genome, features) then softmax.
        Integrators can replace `policy_fn` or subclass `AdaptiveAgent`.
        """
        with self.lock:
            obs = getattr(self, "last_observation", {})
            features = np.zeros(self.genome_size)
            # Simple feature mapping: if numeric features provided, fill them
            numeric = obs.get("features")
            if numeric is not None:
                arr = np.asarray(numeric).ravel()[: self.genome_size]
                features[: len(arr)] = arr

            logits = np.dot(self.genome, features)
            # Map to simple action probabilities
            prob = 1.0 / (1.0 + np.exp(-logits))
            action = {"probability": float(prob), "raw": float(logits)}
            return action

    def apply_genome(self, new_genome):
        with self.lock:
            self.genome = np.asarray(new_genome)
            self.store.set_value(self.session_id, "genome", self.genome.tolist())

    def snapshot(self) -> Dict[str, Any]:
        with self.lock:
            return {"session_id": self.session_id, "genome": self.genome.tolist(), "params": self.params}
