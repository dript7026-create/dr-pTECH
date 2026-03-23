import argparse
import json

from .data_loader import load_csv, prepare_training_frame
from .model import evolutionary_search_and_train, train_model


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a DirkOdds bundle for football, baseball, or basketball.")
    parser.add_argument("--input", required=True, help="Path to historical match CSV")
    parser.add_argument("--output", required=True, help="Path to save the trained joblib bundle")
    parser.add_argument("--sport", default="football", help="Sport name: football, baseball, or basketball")
    parser.add_argument("--evolve", action="store_true", help="Use genetic hyperparameter search before final training")
    parser.add_argument("--ngen", type=int, default=10, help="Number of GA generations")
    parser.add_argument("--pop-size", type=int, default=18, help="GA population size")
    args = parser.parse_args()

    raw_df = load_csv(args.input, sport=args.sport)
    train_df = prepare_training_frame(raw_df, sport=args.sport)

    if args.evolve:
        bundle, info = evolutionary_search_and_train(
            train_df,
            ngen=args.ngen,
            pop_size=args.pop_size,
            save_path=args.output,
            sport=args.sport,
        )
        summary = {
            "sport": bundle.sport,
            "model_name": bundle.model_name,
            "training_rows": bundle.training_rows,
            "metrics": bundle.metrics,
            "best_params": info.get("best_params"),
            "fitness": info.get("fitness"),
            "output": args.output,
        }
    else:
        bundle, metrics = train_model(train_df, save_path=args.output, sport=args.sport)
        summary = {
            "sport": bundle.sport,
            "model_name": bundle.model_name,
            "training_rows": bundle.training_rows,
            "metrics": metrics,
            "output": args.output,
        }

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
