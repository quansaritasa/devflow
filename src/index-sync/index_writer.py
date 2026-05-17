"""Shared index I/O utilities for the index-sync tool."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def slugify(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def to_repo_path(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def ensure_clean_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for child in path.iterdir():
        if child.is_file():
            child.unlink()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def write_jsonl(path: Path, rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def generate_lookup_indexes(
    index_dir: Path,
    tasks: list,
    folder_name: str,
    key_name: str,
    values: Iterable[str],
    selector: Callable,
) -> None:
    output_dir = index_dir / folder_name
    ensure_clean_dir(output_dir)
    for value in values:
        task_keys = sorted({task.jira for task in tasks if selector(task, value)})
        write_json(
            output_dir / f"{slugify(value)}.json",
            {key_name: value, "tasks": task_keys},
        )
