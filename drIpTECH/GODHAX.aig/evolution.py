"""Simple, sandboxed evolutionary utilities for GODHAX.aig.

These functions are intended to run in-process or on dedicated test servers
that you control. They do not interact with external game services.
"""
import random
import numpy as np
from typing import Callable, List, Tuple, Dict


def _mutate(genome: np.ndarray, sigma: float = 0.1) -> np.ndarray:
    g = genome.copy()
    noise = np.random.normal(scale=sigma, size=g.shape)
    return g + noise


def _crossover(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    # simple one-point crossover
    point = random.randint(1, len(a) - 1)
    child = np.concatenate([a[:point], b[point:]])
    return child


def evolve_agent_population(
    init_genome: np.ndarray,
    evaluate_fn: Callable[[np.ndarray], float],
    ngen: int = 10,
    pop_size: int = 20,
    retain_frac: float = 0.4,
    mutate_sigma: float = 0.05,
) -> Tuple[np.ndarray, Dict]:
    """Run a lightweight GA to optimize genomes using evaluate_fn.

    `evaluate_fn` must be a pure function provided by the integrator that
    simulates or scores a genome in sandboxed conditions. It should not
    communicate with external services.
    Returns best_genome and an info dict with best_score.
    """
    genome_size = len(init_genome)
    population = [init_genome + np.random.randn(genome_size) * 0.1 for _ in range(pop_size)]

    best = None
    best_score = float("-inf")

    for gen in range(ngen):
        scored = [(evaluate_fn(g), g) for g in population]
        scored.sort(key=lambda x: x[0], reverse=True)
        if scored[0][0] > best_score:
            best_score = scored[0][0]
            best = scored[0][1]

        retain_length = max(2, int(pop_size * retain_frac))
        parents = [g for _, g in scored[:retain_length]]

        # fill rest with children
        children = []
        while len(parents) + len(children) < pop_size:
            a, b = random.sample(parents, 2)
            child = _crossover(a, b)
            if random.random() < 0.3:
                child = _mutate(child, sigma=mutate_sigma)
            children.append(child)

        population = parents + children

    return best, {"best_score": float(best_score)}
