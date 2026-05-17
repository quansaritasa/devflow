#!/usr/bin/env python3
"""Generate dev/index artifacts from structured task.json content."""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

from components import generate_component_indexes
from index_writer import REPO_ROOT, write_json
from models import AppConfig, TaskParseError
from shards import generate_shard_indexes
from tags import generate_tag_indexes
from task_parser import parse_task_record

CONFIG_PATH = Path(__file__).resolve().with_name("config.json")


def load_config(config_path: Path) -> AppConfig:
    raw = json.loads(config_path.read_text(encoding="utf-8"))

    def resolve_path(key: str) -> Path:
        value = raw.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Config value '{key}' must be a non-empty string")
        return (REPO_ROOT / value).resolve()

    shard_size = raw.get("shard_size")
    if not isinstance(shard_size, int) or shard_size <= 0:
        raise ValueError("Config value 'shard_size' must be a positive integer")

    task_key_pattern = raw.get("task_key_pattern")
    if not isinstance(task_key_pattern, str) or not task_key_pattern.strip():
        raise ValueError("Config value 'task_key_pattern' must be a non-empty string")

    return AppConfig(
        tasks_dir=resolve_path("tasks_dir"),
        index_dir=resolve_path("index_dir"),
        shard_size=shard_size,
        task_key_pattern=re.compile(task_key_pattern),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate shard and lookup indexes from structured task sources."
    )
    _ = parser.add_argument(
        "--config",
        type=Path,
        default=CONFIG_PATH,
        help=f"Path to config file (default: {CONFIG_PATH})",
    )
    _ = parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Print progress details during indexing",
    )
    return parser.parse_args()


def iter_task_directories(
    tasks_dir: Path, task_key_pattern: re.Pattern[str]
) -> Iterable[Path]:
    if not tasks_dir.exists():
        raise FileNotFoundError(f"Tasks directory not found: {tasks_dir}")
    for child in sorted(tasks_dir.iterdir()):
        if child.is_dir() and task_key_pattern.match(child.name):
            yield child


def main() -> int:
    try:
        return _run()
    except (TaskParseError, FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=__import__("sys").stderr)
        return 1


def _run() -> int:
    args = parse_args()
    verbose: bool = args.verbose
    config_path = cast(Path, args.config)
    config = load_config(config_path)

    if verbose:
        print(f"Scanning task directories in {config.tasks_dir}")
    tasks = [
        parse_task_record(task_dir, config)
        for task_dir in iter_task_directories(config.tasks_dir, config.task_key_pattern)
        if (task_dir / "task.json").exists()
    ]
    tasks.sort(key=lambda item: item.issue_number)

    if verbose:
        print(f"Found {len(tasks)} tasks, generating indexes")

    _ = config.index_dir.mkdir(parents=True, exist_ok=True)
    shard_manifest = generate_shard_indexes(
        config.index_dir,
        tasks,
        config.shard_size,
    )
    generate_component_indexes(config.index_dir, tasks)
    generate_tag_indexes(config.index_dir, tasks)

    write_json(
        config.index_dir / "index.json",
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "shards": shard_manifest,
        },
    )

    print(f"Indexed {len(tasks)} tasks into {config.index_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
