"""Task record parsing from task.json files."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

from index_writer import to_repo_path
from models import AppConfig, TaskParseError, TaskRecord


def _normalize_name(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"[\s_./\\]+", "-", text)
    text = re.sub(r"[^a-z0-9-]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def _parse_components(task_data: dict[str, Any]) -> tuple[str, list[str]]:
    """Return (primary_component, related_components) from task data."""
    normalized: list[str] = []
    seen: set[str] = set()
    for item in cast(list[Any], task_data.get("components") or []):
        name = _normalize_name(str(item))
        if not name or name in seen:
            continue
        seen.add(name)
        normalized.append(name)
    primary = normalized[0] if normalized else "unknown"
    return primary, normalized[1:]


def _parse_tags(task_data: dict[str, Any]) -> list[str]:
    """Return deduplicated, stripped tags from task data."""
    tags: list[str] = []
    for item in cast(list[Any], task_data.get("tags") or []):
        tag = str(item).strip()
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def _parse_related_tasks(task_data: dict[str, Any]) -> list[str]:
    """Return related task keys from task data."""
    return [
        str(item.get("key"))
        for item in cast(list[Any], task_data.get("related_tasks") or [])
        if isinstance(item, dict) and str(item.get("key") or "").strip()
    ]


def _load_task_json(task_dir: Path) -> tuple[Path, dict[str, Any]]:
    """Load and validate task.json, returning (path, data)."""
    task_json_path = task_dir / "task.json"
    if not task_json_path.exists():
        raise TaskParseError(f"Missing task.json in {task_dir}")
    task_data = json.loads(task_json_path.read_text(encoding="utf-8"))
    if not isinstance(task_data, dict):
        raise TaskParseError(f"Invalid task.json object in {task_json_path}")
    return task_json_path, task_data


def _parse_updated_at(task_data: dict[str, Any], task_json_path: Path) -> str:
    """Return ISO-formatted updated_at from task data or file mtime."""
    updated_source = str(task_data.get("updated") or "")
    if updated_source:
        return datetime.fromisoformat(f"{updated_source}T00:00:00+00:00").isoformat()
    return datetime.fromtimestamp(
        task_json_path.stat().st_mtime, tz=timezone.utc
    ).isoformat()


def parse_task_record(
    task_dir: Path,
    config: AppConfig,
) -> TaskRecord:
    task_json_path, task_data = _load_task_json(task_dir)

    jira = str(task_data.get("task_key") or task_dir.name)
    if not config.task_key_pattern.match(jira):
        raise TaskParseError(f"Invalid task key: {jira}")

    title = str(task_data.get("task_summary") or jira)
    status = str(task_data.get("status") or "Unknown")
    primary_component, related_components = _parse_components(task_data)

    issue_number = int(jira.rsplit("-", 1)[1])
    paths_data = task_data.get("paths") or {}
    raw_path = str(paths_data.get("raw") or "") if isinstance(paths_data, dict) else ""

    return TaskRecord(
        jira=jira,
        issue_number=issue_number,
        title=title,
        status=status,
        primary_component=primary_component,
        related_components=related_components,
        updated_at=_parse_updated_at(task_data, task_json_path),
        tags=_parse_tags(task_data),
        paths={
            "task_json": to_repo_path(task_json_path),
            "raw": raw_path,
        },
        related_tasks=_parse_related_tasks(task_data),
    )
