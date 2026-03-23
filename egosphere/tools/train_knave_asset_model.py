import json
import math
import re
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT / "pipeline" / "projects" / "knave_prototype"
CURRICULUM_PATH = PROJECT_ROOT / "pixel_art_history_curriculum.json"
CORPUS_PATH = PROJECT_ROOT / "knave_ml_training_corpus.jsonl"
TRAINED_MODEL_PATH = PROJECT_ROOT / "knave_trained_ml_model.json"
REPORT_PATH = PROJECT_ROOT / "knave_trained_ml_report.json"
MODEL_PATH = PROJECT_ROOT / "knave_asset_generator_model.json"

TOKEN_RE = re.compile(r"[a-z0-9_]{2,}")
FEATURE_DIM = 256
EPOCHS = 180
LEARNING_RATE = 0.08


def load_corpus() -> list[dict]:
    rows = []
    with CORPUS_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def tokenize(text: str, tags: list[str]) -> list[str]:
    lowered = text.lower()
    tokens = TOKEN_RE.findall(lowered)
    tokens.extend(tag.lower().replace("-", "_") for tag in tags)
    return tokens


def hashed_features(tokens: list[str], dim: int = FEATURE_DIM) -> list[float]:
    features = [0.0] * dim
    for token in tokens:
        bucket = zlib.crc32(token.encode("utf-8")) % dim
        features[bucket] += 1.0
    norm = math.sqrt(sum(value * value for value in features)) or 1.0
    return [value / norm for value in features]


def train_linear_regressor(samples: list[list[float]], targets: list[float]) -> tuple[list[float], float]:
    weights = [0.0] * FEATURE_DIM
    bias = 0.0
    for _ in range(EPOCHS):
        for features, target in zip(samples, targets):
            prediction = sum(weight * value for weight, value in zip(weights, features)) + bias
            error = prediction - target
            for index, value in enumerate(features):
                weights[index] -= LEARNING_RATE * error * value
            bias -= LEARNING_RATE * error
    return weights, bias


def predict(weights: list[float], bias: float, features: list[float]) -> float:
    return sum(weight * value for weight, value in zip(weights, features)) + bias


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def mean_squared_error(weights: list[float], bias: float, samples: list[list[float]], targets: list[float]) -> float:
    if not samples:
        return 0.0
    total = 0.0
    for features, target in zip(samples, targets):
        error = predict(weights, bias, features) - target
        total += error * error
    return total / len(samples)


def train_model(corpus: list[dict]) -> tuple[dict, dict]:
    feature_rows = [hashed_features(tokenize(row["text"], row["component_tags"])) for row in corpus]
    axis_names = sorted(corpus[0]["targets"].keys())
    godai_names = sorted(corpus[0]["godai_bias"].keys())

    axis_models = {}
    axis_errors = {}
    for axis_name in axis_names:
        targets = [float(row["targets"][axis_name]) for row in corpus]
        weights, bias = train_linear_regressor(feature_rows, targets)
        axis_models[axis_name] = {"weights": weights, "bias": bias}
        axis_errors[axis_name] = round(mean_squared_error(weights, bias, feature_rows, targets), 6)

    godai_models = {}
    godai_errors = {}
    for name in godai_names:
        targets = [float(row["godai_bias"][name]) for row in corpus]
        weights, bias = train_linear_regressor(feature_rows, targets)
        godai_models[name] = {"weights": weights, "bias": bias}
        godai_errors[name] = round(mean_squared_error(weights, bias, feature_rows, targets), 6)

    trained = {
        "model_name": "KnavePixelArtHistoryBootstrapModel",
        "model_version": "2026-03-18.knave.pixelhistory.v1",
        "feature_dim": FEATURE_DIM,
        "epochs": EPOCHS,
        "learning_rate": LEARNING_RATE,
        "training_sources": {
            "curriculum": str(CURRICULUM_PATH),
            "corpus": str(CORPUS_PATH),
        },
        "axis_models": axis_models,
        "godai_models": godai_models,
        "inference_contract": {
            "tokenization": "lowercase regex tokens + component tags",
            "vectorization": "hashed bag-of-words normalized to unit length",
            "postprocess": {
                "axes": "clamp to [0.0, 1.0]",
                "godai": "clamp to [0.8, 1.4]",
            },
            "outputs": {
                "axes": axis_names,
                "godai": godai_names,
            },
        },
        "limitations": [
            "This is a lightweight steering model over textual and component metadata, not a generative image model.",
            "It bootstraps taste and direction from a curated pixel-art history curriculum plus knave component targets.",
        ],
    }
    report = {
        "training_examples": len(corpus),
        "axis_mse": axis_errors,
        "godai_mse": godai_errors,
        "history_examples": len([row for row in corpus if row["source_type"] == "pixel_art_history"]),
        "component_examples": len([row for row in corpus if row["source_type"] == "knave_component"]),
    }
    return trained, report


def build_integration_preview(trained_model: dict) -> dict:
    knave_model = json.loads(MODEL_PATH.read_text(encoding="utf-8"))
    preview = []
    for component in knave_model["designer_components"][:5]:
        features = hashed_features(tokenize(component["compiled_prompt"], component["component_tags"]))
        axis_prediction = {}
        for axis_name, model in trained_model["axis_models"].items():
            axis_prediction[axis_name] = round(clamp(predict(model["weights"], model["bias"], features), 0.0, 1.0), 3)
        godai_prediction = {}
        for name, model in trained_model["godai_models"].items():
            godai_prediction[name] = round(clamp(predict(model["weights"], model["bias"], features), 0.8, 1.4), 3)
        preview.append(
            {
                "asset_id": component["asset_id"],
                "predicted_axes": axis_prediction,
                "predicted_godai": godai_prediction,
            }
        )
    return {"preview_predictions": preview}


def main() -> int:
    corpus = load_corpus()
    trained_model, report = train_model(corpus)
    report.update(build_integration_preview(trained_model))
    TRAINED_MODEL_PATH.write_text(json.dumps(trained_model, indent=2) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"model": str(TRAINED_MODEL_PATH), "report": str(REPORT_PATH), "examples": report["training_examples"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())