"""Simple authorization helpers for GODHAX.aig.

This is a minimal, file-based authorization stub intended for in-house use.
Administrators for your studio or project should be listed in `ADMIN_USERS`.
"""
import os
from functools import wraps
from typing import Callable

# Configure admin users here or via the GODHAX_ADMIN_USERS environment var
ADMIN_USERS = os.getenv("GODHAX_ADMIN_USERS", "").split(",") if os.getenv("GODHAX_ADMIN_USERS") else [os.getenv("USER") or os.getenv("USERNAME")]


def is_authorized_admin(username: str) -> bool:
    """Return True if username is an authorized admin."""
    return bool(username) and username in ADMIN_USERS


def require_admin(func: Callable) -> Callable:
    """Decorator that requires an admin username to be passed as `user` kwarg.

    Usage:
        @require_admin
        def export(..., user=None):
            ...
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        user = kwargs.get("user") or os.getenv("GODHAX_CURRENT_USER")
        if not user or not is_authorized_admin(user):
            raise PermissionError("user is not authorized to perform this action")
        return func(*args, **kwargs)

    return wrapper
