import argparse
import json

from validate_pipeline_core import run_validation_suite


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate drIpTECH pipeline outputs")
    parser.add_argument(
        "--suite",
        choices=["sample", "pertinence", "all"],
        default="sample",
        help="Validation suite to run",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the desktop validator instead of printing JSON to stdout",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="When used with --gui, start the selected suite immediately after launch",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.gui:
        from validate_pipeline_gui import launch_app

        return launch_app(initial_suite=args.suite, auto_run=args.run)

    summary = run_validation_suite(args.suite)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())