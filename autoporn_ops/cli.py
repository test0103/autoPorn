from __future__ import annotations

import argparse

from .config import load_config
from .pipeline import OperationsPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Content operations automation")
    parser.add_argument("--config", default="config/config.example.yaml")
    parser.add_argument("--execute", action="store_true", help="Perform API mutations; otherwise only writes the Excel plan")
    parser.add_argument("--learn", action="store_true", help="Train from review workbook before planning")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_config(args.config)
    if args.execute:
        config.api.dry_run = False
    pipeline = OperationsPipeline(config)
    if args.learn:
        count = pipeline.learn_from_review()
        print(f"learned_rows={count}")
    decisions = pipeline.plan()
    pipeline.execute(decisions)
    print(f"decisions={len(decisions)} dry_run={config.api.dry_run}")


if __name__ == "__main__":
    main()
