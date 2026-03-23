"""Ephemeral central session database for GODHAX.aig.

This module implements a simple in-memory session store. It is intentionally
designed to avoid persistent profiles that live outside a gameplay session.
"""
import threading
import time
from typing import Dict, Any


class SessionStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, session_id: str, ttl: int = 3600):
        with self._lock:
            self._sessions[session_id] = {"created": time.time(), "ttl": ttl, "data": {}}

    def get_session(self, session_id: str):
        with self._lock:
            s = self._sessions.get(session_id)
            if not s:
                return None
            if time.time() - s["created"] > s["ttl"]:
                # session expired
                del self._sessions[session_id]
                return None
            return s["data"]

    def set_value(self, session_id: str, key: str, value: Any):
        with self._lock:
            s = self._sessions.setdefault(session_id, {"created": time.time(), "ttl": 3600, "data": {}})
            s["data"][key] = value

    def clear_session(self, session_id: str):
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]


# Singleton store for the process
_store = SessionStore()


def get_store():
    return _store
