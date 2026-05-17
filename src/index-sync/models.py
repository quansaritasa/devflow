"""Shared data models for the index-sync tool."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AppConfig:
    tasks_dir: Path
    index_dir: Path
    shard_size: int
    task_key_pattern: re.Pattern[str]


@dataclass
class TaskRecord:
    jira: str
    issue_number: int
    title: str
    status: str
    primary_component: str
    related_components: list[str]
    updated_at: str
    paths: dict[str, str]
    related_tasks: list[str]
    tags: list[str]


class TaskParseError(RuntimeError):
    pass
