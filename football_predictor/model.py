from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, log_loss
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .data_loader import FEATURE_COLUMNS
from .evolution import run_evolution
from .sports import entropy_normalizer, normalize_sport, outcome_label, probability_matrix_from_classes, resolve_frame_sport


@dataclass
class DirkOddsBundle:
    estimator: object
    feature_columns: List[str]
    model_name: str
    metrics: Dict[str, float]
    training_rows: int
    sport: str = "football"


def _assemble_features(df: pd.DataFrame, feature_columns: Optional[List[str]] = None) -> np.ndarray:
    columns = feature_columns or FEATURE_COLUMNS
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required feature columns: {', '.join(missing)}")
    return df.loc[:, columns].astype(float).to_numpy()


def _candidate_models(random_state: int = 42) -> Dict[str, Pipeline]:
    return {
        "logistic_regression": Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                (
                    "model",
                    LogisticRegression(
                        max_iter=2000,
                        random_state=random_state,
                        class_weight="balanced",
                    ),
                ),
            ]
        ),
        "random_forest": Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "model",
                    RandomForestClassifier(
                        n_estimators=220,
                        max_depth=10,
                        min_samples_leaf=2,
                        max_features=0.8,
                        class_weight="balanced_subsample",
                        random_state=random_state,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
        "gradient_boosting": Pipeline(
            steps=[
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "model",
                    HistGradientBoostingClassifier(
                        max_depth=6,
                        max_iter=220,
                        learning_rate=0.05,
                        random_state=random_state,
                    ),
                ),
            ]
        ),
    }


def _should_stratify(y: np.ndarray) -> bool:
    _, counts = np.unique(y, return_counts=True)
    return len(counts) > 1 and int(counts.min()) >= 2


def _evaluate_estimator(name: str, estimator: Pipeline, X_train, X_test, y_train, y_test, labels: List[int]) -> Dict[str, float]:
    estimator.fit(X_train, y_train)
    probabilities = estimator.predict_proba(X_test)
    predictions = estimator.predict(X_test)
    return {
        "model_name": name,
        "log_loss": float(log_loss(y_test, probabilities, labels=labels)),
        "accuracy": float(accuracy_score(y_test, predictions)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, predictions)),
    }


def _fit_final_bundle(
    estimator: Pipeline,
    model_name: str,
    metrics: Dict[str, float],
    df: pd.DataFrame,
    sport: str,
    save_path: Optional[str] = None,
) -> Tuple[DirkOddsBundle, Dict[str, float]]:
    X = _assemble_features(df)
    y = df["outcome"].to_numpy()
    final_estimator = clone(estimator)
    final_estimator.fit(X, y)
    bundle = DirkOddsBundle(
        estimator=final_estimator,
        feature_columns=list(FEATURE_COLUMNS),
        model_name=model_name,
        metrics=metrics,
        training_rows=int(len(df)),
        sport=normalize_sport(sport),
    )
    if save_path:
        joblib.dump(bundle, save_path)
    return bundle, metrics


def train_model(
    df: pd.DataFrame,
    model_name: str = "auto",
    save_path: Optional[str] = None,
    random_state: int = 42,
    sport: Optional[str] = None,
) -> Tuple[DirkOddsBundle, Dict[str, float]]:
    """Train DirkOdds on pre-match features and return a serializable bundle."""
    if "outcome" not in df.columns:
        raise ValueError("Training frame must contain an 'outcome' column.")

    X = _assemble_features(df)
    y = df["outcome"].to_numpy()
    resolved_sport = normalize_sport(sport or resolve_frame_sport(df.get("sport", []), default="football"))
    labels = sorted(int(value) for value in np.unique(y))
    stratify = y if _should_stratify(y) else None
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=random_state,
        stratify=stratify,
    )

    candidates = _candidate_models(random_state=random_state)
    selected_names = [model_name] if model_name in candidates else list(candidates.keys())

    best_name = None
    best_metrics = None
    best_estimator = None
    for candidate_name in selected_names:
        estimator = clone(candidates[candidate_name])
        metrics = _evaluate_estimator(candidate_name, estimator, X_train, X_test, y_train, y_test, labels=labels)
        if best_metrics is None or metrics["log_loss"] < best_metrics["log_loss"]:
            best_name = candidate_name
            best_metrics = metrics
            best_estimator = candidates[candidate_name]

    assert best_name is not None and best_metrics is not None and best_estimator is not None
    return _fit_final_bundle(best_estimator, best_name, best_metrics, df, resolved_sport, save_path=save_path)


def predict_proba(bundle_or_estimator: Union[DirkOddsBundle, object], df: pd.DataFrame) -> np.ndarray:
    feature_columns = bundle_or_estimator.feature_columns if isinstance(bundle_or_estimator, DirkOddsBundle) else FEATURE_COLUMNS
    estimator = bundle_or_estimator.estimator if isinstance(bundle_or_estimator, DirkOddsBundle) else bundle_or_estimator
    X = _assemble_features(df, feature_columns=feature_columns)
    probabilities = estimator.predict_proba(X)
    return probability_matrix_from_classes(probabilities, estimator.classes_)


def predict_matches(bundle_or_estimator: Union[DirkOddsBundle, object], df: pd.DataFrame, sport: Optional[str] = None) -> pd.DataFrame:
    resolved_sport = normalize_sport(
        sport
        or getattr(bundle_or_estimator, "sport", None)
        or resolve_frame_sport(df.get("sport", []), default="football")
    )
    probabilities = predict_proba(bundle_or_estimator, df)
    output = df.copy().reset_index(drop=True)
    output["sport"] = resolved_sport
    output["prob_away_win"] = probabilities[:, 0]
    output["prob_draw"] = probabilities[:, 1]
    output["prob_home_win"] = probabilities[:, 2]

    confidence = probabilities.max(axis=1)
    entropy = -np.sum(probabilities * np.log(np.clip(probabilities, 1e-9, 1.0)), axis=1) / entropy_normalizer(resolved_sport)
    predicted = probabilities.argmax(axis=1)

    output["prediction_code"] = predicted
    output["prediction"] = [outcome_label(int(index), resolved_sport) for index in predicted]
    output["confidence"] = confidence
    output["uncertainty"] = 1.0 - confidence
    output["entropy"] = entropy
    return output


def export_model(bundle: DirkOddsBundle, path: str) -> None:
    joblib.dump(bundle, path)


def evolutionary_search_and_train(
    df: pd.DataFrame,
    ngen: int = 12,
    pop_size: int = 20,
    save_path: Optional[str] = None,
    random_state: int = 42,
    sport: Optional[str] = None,
) -> Tuple[DirkOddsBundle, Dict[str, object]]:
    """Run GA-based RF search, then fit the final DirkOdds bundle."""
    if "outcome" not in df.columns:
        raise ValueError("Training frame must contain an 'outcome' column.")

    X = _assemble_features(df)
    y = df["outcome"].to_numpy()
    resolved_sport = normalize_sport(sport or resolve_frame_sport(df.get("sport", []), default="football"))
    labels = sorted(int(value) for value in np.unique(y))
    best_params, fitness = run_evolution(X, y, ngen=ngen, pop_size=pop_size, random_state=random_state)
    tuned_estimator = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=best_params.get("n_estimators", 220),
                    max_depth=best_params.get("max_depth", 10),
                    max_features=best_params.get("max_features", 0.8),
                    min_samples_leaf=best_params.get("min_samples_leaf", 2),
                    class_weight="balanced_subsample",
                    random_state=random_state,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    stratify = y if _should_stratify(y) else None
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=random_state,
        stratify=stratify,
    )
    metrics = _evaluate_estimator("evolved_random_forest", clone(tuned_estimator), X_train, X_test, y_train, y_test, labels=labels)
    bundle, _ = _fit_final_bundle(tuned_estimator, "evolved_random_forest", metrics, df, resolved_sport, save_path=save_path)
    info = {
        "best_params": best_params,
        "fitness": float(fitness),
        "metrics": metrics,
    }
    return bundle, info


def load_model(path: str) -> DirkOddsBundle:
    return joblib.load(path)
