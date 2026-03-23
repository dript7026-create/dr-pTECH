"""
genetic.py

Minimal genetic algorithm controller stub for NaVi.
This module defines a `GeneticController` that will manage candidate policy
representations and perform selection/mutation. It's intentionally small as a
scaffold — add concrete genotype encoding, fitness evaluation, and persistence.
"""

import random

class Candidate:
    def __init__(self, params=None):
        self.params = params or { 'mutate_chance': 0.1, 'style_bias': 0.0 }
        self.fitness = 0.0

    def mutate(self):
        # simple numeric mutation example
        if random.random() < self.params.get('mutate_chance', 0.1):
            self.params['style_bias'] += random.uniform(-0.1, 0.1)

class GeneticController:
    def __init__(self, population_size=8):
        self.population = [Candidate() for _ in range(population_size)]

    def evaluate_and_select(self, eval_fn):
        """Evaluate candidates using eval_fn(candidate) -> fitness; keep top half."""
        for c in self.population:
            c.fitness = eval_fn(c)
        self.population.sort(key=lambda x: x.fitness, reverse=True)
        survivors = self.population[:max(1, len(self.population)//2)]
        self.population = survivors + [Candidate(params=dict(random.choice(survivors).params)) for _ in range(len(survivors))]

    def iterate(self):
        for c in self.population:
            c.mutate()

    def best(self):
        return max(self.population, key=lambda c: c.fitness)
