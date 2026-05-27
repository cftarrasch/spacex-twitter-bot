from __future__ import annotations

import argparse
from pathlib import Path

from .config import Settings
from .model import save_model_bundle, train_model_bundle
from .spacex_api import SpaceXClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train SpaceX prediction models.")
    parser.add_argument(
        "--model-path",
        type=Path,
        default=None,
        help="Output path for the trained joblib model bundle.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings.from_env()
    model_path = args.model_path or settings.model_path
    client = SpaceXClient(base_url=settings.spacex_api_base_url)
    launches = client.past_launches()
    bundle = train_model_bundle(launches)
    save_model_bundle(bundle, model_path)

    print(f"Saved model bundle to {model_path}")
    for name, model_info in bundle["models"].items():
        print(f"{name}: {model_info['metrics']}")


if __name__ == "__main__":
    main()

