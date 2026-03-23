"""Evolutionary hyperparameter search for DirkOdds classifiers using DEAP."""

import random
import warnings
from typing import Dict, Tuple

import numpy as np
from deap import algorithms, base, creator, tools
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, log_loss
from sklearn.model_selection import StratifiedKFold


def _ensure_deap_types() -> None:
    if hasattr(creator, "DirkOddsFitnessMax"):
        del creator.DirkOddsFitnessMax
    if hasattr(creator, "DirkOddsIndividual"):
        del creator.DirkOddsIndividual
    creator.create("DirkOddsFitnessMax", base.Fitness, weights=(1.0,))
    creator.create("DirkOddsIndividual", list, fitness=creator.DirkOddsFitnessMax)


def _clamp_individual(individual) -> None:
    individual[0] = int(min(400, max(50, round(individual[0]))))
    individual[1] = int(min(18, max(0, round(individual[1]))))
    individual[2] = float(min(1.0, max(0.25, individual[2])))
    individual[3] = int(min(8, max(1, round(individual[3]))))


def _evaluate_individual(individual, X, y, random_state):
    _clamp_individual(individual)
    n_estimators, max_depth, max_features, min_samples_leaf = individual
    max_depth = int(max_depth) if int(max_depth) > 0 else None

    unique, counts = np.unique(y, return_counts=True)
    min_class_count = int(counts.min()) if len(counts) else 0
    n_splits = min(4, min_class_count) if min_class_count >= 2 else 0
    if n_splits < 2:
        return (0.0,)

    splitter = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    accuracies = []
    losses = []

    for train_idx, test_idx in splitter.split(X, y):
        clf = RandomForestClassifier(
            n_estimators=int(n_estimators),
            max_depth=max_depth,
            max_features=float(max_features),
            min_samples_leaf=int(min_samples_leaf),
            class_weight="balanced_subsample",
            random_state=random_state,
            n_jobs=-1,
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            clf.fit(X[train_idx], y[train_idx])
        probs = clf.predict_proba(X[test_idx])
        preds = clf.predict(X[test_idx])
        accuracies.append(float(accuracy_score(y[test_idx], preds)))
        losses.append(float(log_loss(y[test_idx], probs, labels=[0, 1, 2])))

    fitness = float(np.mean(accuracies) - 0.20 * np.mean(losses))
    return (fitness,)


def run_evolution(X, y, ngen=16, pop_size=20, cxpb=0.55, mutpb=0.25, random_state=42) -> Tuple[Dict, float]:
    """Run a GA to find strong RandomForest hyperparameters."""
    random.seed(random_state)
    np.random.seed(random_state)
    _ensure_deap_types()

    toolbox = base.Toolbox()
    toolbox.register("n_estimators", random.randint, 50, 400)
    toolbox.register("max_depth", random.randint, 0, 18)
    toolbox.register("max_features", random.uniform, 0.25, 1.0)
    toolbox.register("min_samples_leaf", random.randint, 1, 8)
    toolbox.register(
        "individual",
        tools.initCycle,
        creator.DirkOddsIndividual,
        (toolbox.n_estimators, toolbox.max_depth, toolbox.max_features, toolbox.min_samples_leaf),
        n=1,
    )
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("evaluate", _evaluate_individual, X=X, y=y, random_state=random_state)
    toolbox.register("mate", tools.cxBlend, alpha=0.35)
    toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=3, indpb=0.35)
    toolbox.register("select", tools.selTournament, tournsize=3)

    pop = toolbox.population(n=pop_size)
    hof = tools.HallOfFame(1)

    for individual in pop:
        _clamp_individual(individual)

    algorithms.eaSimple(pop, toolbox, cxpb=cxpb, mutpb=mutpb, ngen=ngen, halloffame=hof, verbose=False)

    best = hof[0]
    _clamp_individual(best)
    best_params = {
        "n_estimators": int(best[0]),
        "max_depth": int(best[1]) if int(best[1]) > 0 else None,
        "max_features": float(best[2]),
        "min_samples_leaf": int(best[3]),
    }
    best_fitness = float(hof.items[0].fitness.values[0])
    return best_params, best_fitness
