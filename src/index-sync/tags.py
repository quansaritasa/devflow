"""Tag index generation for the index-sync tool."""

from __future__ import annotations

from pathlib import Path

from index_writer import generate_lookup_indexes


def generate_tag_indexes(index_dir: Path, tasks: list) -> None:
    """Generate by-tag lookup indexes under `index_dir`."""
    tags = sorted({tag for task in tasks for tag in task.tags if tag})
    generate_lookup_indexes(
        index_dir,
        tasks,
        "by-tag",
        "tag",
        tags,
        lambda task, value: value in task.tags,
    )
