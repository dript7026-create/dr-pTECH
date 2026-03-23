from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet


class AuthorizationScope(str, Enum):
    OBSERVE_ONLY = "observe-only"
    RENDER = "render"
    SIMULATION = "simulation"
    ENGINE = "engine"
    DIRECTOR = "director"


class MutationDomain(str, Enum):
    STATE = "state"
    PARAMETERS = "parameters"
    MISSIONS = "missions"
    PARTICLES = "particles"
    RENDER = "render"


@dataclass(frozen=True)
class AuthorizationProfile:
    scope: AuthorizationScope
    domains: FrozenSet[MutationDomain]

    def allows(self, domain: MutationDomain) -> bool:
        return domain in self.domains


def safe_profile(scope: AuthorizationScope) -> AuthorizationProfile:
    if scope == AuthorizationScope.OBSERVE_ONLY:
        return AuthorizationProfile(scope=scope, domains=frozenset())
    if scope == AuthorizationScope.RENDER:
        return AuthorizationProfile(scope=scope, domains=frozenset({MutationDomain.PARTICLES, MutationDomain.RENDER}))
    if scope == AuthorizationScope.SIMULATION:
        return AuthorizationProfile(
            scope=scope,
            domains=frozenset({MutationDomain.STATE, MutationDomain.PARAMETERS, MutationDomain.MISSIONS}),
        )
    if scope == AuthorizationScope.ENGINE:
        return AuthorizationProfile(
            scope=scope,
            domains=frozenset({MutationDomain.STATE, MutationDomain.PARAMETERS, MutationDomain.PARTICLES, MutationDomain.RENDER}),
        )
    return AuthorizationProfile(
        scope=scope,
        domains=frozenset({
            MutationDomain.STATE,
            MutationDomain.PARAMETERS,
            MutationDomain.MISSIONS,
            MutationDomain.PARTICLES,
            MutationDomain.RENDER,
        }),
    )