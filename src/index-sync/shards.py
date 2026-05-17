"""Shard generation for the index-sync tool."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from models import TaskRecord

from index_writer import ensure_clean_dir, to_repo_path, write_jsonl


def _shard_range(issue_number: int, shard_size: int) -> tuple[int, int]:
    """Return (start, end) shard range for an issue number."""
    start = (issue_number // shard_size) * shard_size
    if issue_number % shard_size == 0:
        start -= shard_size
    start += 1
    return start, start + shard_size - 1


def _task_to_dict(task: TaskRecord) -> dict[str, object]:
    return {
        "jira": task.jira,
        "title": task.title,
        "status": task.status,
        "primary_component": task.primary_component,
        "related_components": task.related_components,
        "updated_at": task.updated_at,
        "paths": task.paths,
        "related_tasks": task.related_tasks,
        "tags": task.tags,
    }


def _build_shard_sync_counts(
    tasks: list[TaskRecord], shard_size: int
) -> dict[tuple[int, int], dict[str, int]]:
    shard_counts: dict[tuple[int, int], dict[str, int]] = {}
    if not tasks:
        return shard_counts

    for task in tasks:
        start, end = _shard_range(task.issue_number, shard_size)
        counts = shard_counts.setdefault(
            (start, end),
            {
                "saved_tasks": 0,
                "unsynced_tasks": 0,
                "total_tasks": shard_size,
            },
        )
        counts["saved_tasks"] += 1

    for counts in shard_counts.values():
        counts["unsynced_tasks"] = counts["total_tasks"] - counts["saved_tasks"]

    return shard_counts


def _build_shard_manifest(
    grouped: dict[tuple[int, int], list[TaskRecord]],
    shard_counts: dict[tuple[int, int], dict[str, int]],
    shards_dir: Path,
) -> list[dict[str, object]]:
    manifest: list[dict[str, object]] = []
    for (start, end), counts in sorted(shard_counts.items()):
        shard_tasks = grouped.get((start, end), [])
        shard_id = f"{start}-{end}"
        file_path = shards_dir / f"{shard_id}.jsonl"
        write_jsonl(
            file_path,
            [
                _task_to_dict(task)
                for task in sorted(shard_tasks, key=lambda x: x.issue_number)
            ],
        )
        jira_numbers = [task.issue_number for task in shard_tasks]
        manifest.append(
            {
                "id": shard_id,
                "path": to_repo_path(file_path),
                "jira_min": min(jira_numbers) if jira_numbers else start,
                "jira_max": max(jira_numbers) if jira_numbers else end,
                "saved_tasks": counts["saved_tasks"],
                "unsynced_tasks": counts["unsynced_tasks"],
                "total_tasks": counts["total_tasks"],
            }
        )
    return manifest


def generate_shard_indexes(
    index_dir: Path,
    tasks: list[TaskRecord],
    shard_size: int,
) -> list[dict[str, object]]:
    """Generate shard files and return the shard manifest."""
    shards_dir = index_dir / "shards"
    ensure_clean_dir(shards_dir)

    grouped: dict[tuple[int, int], list[TaskRecord]] = defaultdict(list)
    shard_counts = _build_shard_sync_counts(tasks, shard_size)
    for task in tasks:
        start, end = _shard_range(task.issue_number, shard_size)
        grouped[(start, end)].append(task)

    return _build_shard_manifest(grouped, shard_counts, shards_dir)
