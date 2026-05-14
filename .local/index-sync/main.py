#!/usr/bin/env python3
"""Generate dev/index artifacts from structured task.json content."""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = Path(__file__).resolve().with_name("config.json")
KEYWORD_ENTRY_PATTERN = re.compile(r"^\s*-\s+canonical:\s*(.+?)\s*$")
FIELD_PATTERN = re.compile(r"^\s{2,}(group|aliases|related):\s*(.+?)\s*$")
GROUPS = {
    "product-area",
    "domain-entity",
    "workflow",
    "auth-access",
    "technical",
    "ui-ux",
    "integration",
    "environment",
    "issue-shape",
}


@dataclass
class AppConfig:
    tasks_dir: Path
    index_dir: Path
    keywords_file: Path
    shard_size: int
    task_key_pattern: re.Pattern[str]


@dataclass(frozen=True)
class KeywordEntry:
    canonical: str
    group: str
    aliases: list[str]
    related: list[str]


@dataclass(frozen=True)
class KeywordTaxonomy:
    entries: list[KeywordEntry]
    by_canonical: dict[str, KeywordEntry]
    alias_to_canonical: dict[str, str]
    by_group: dict[str, list[str]]


@dataclass
class TaskRecord:
    jira: str
    issue_number: int
    title: str
    status: str
    primary_component: str
    related_components: list[str]
    keywords: list[str]
    keyword_groups: dict[str, list[str]]
    updated_at: str
    paths: dict[str, str]
    related_tasks: list[str]


class TaskParseError(RuntimeError):
    pass


class KeywordParseError(RuntimeError):
    pass


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
        keywords_file=resolve_path("keywords_file"),
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
    return parser.parse_args()


def normalize_keyword(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"[\s_./\\]+", "-", text)
    text = re.sub(r"[^a-z0-9-]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def parse_inline_list(value: str) -> list[str]:
    text = value.strip()
    if not text.startswith("[") or not text.endswith("]"):
        raise KeywordParseError(f"Expected inline list like [a, b], got: {value}")
    inner = text[1:-1].strip()
    if not inner:
        return []
    items = [normalize_keyword(item) for item in inner.split(",")]
    return [item for item in items if item]


def load_keyword_taxonomy(path: Path) -> KeywordTaxonomy:
    if not path.exists():
        raise FileNotFoundError(f"Keyword taxonomy file not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".json":
        return load_keyword_taxonomy_json(path)
    if suffix == ".md":
        return load_keyword_taxonomy_md(path)
    raise KeywordParseError(f"Unsupported keyword taxonomy format: {path}")


def load_keyword_taxonomy_md(path: Path) -> KeywordTaxonomy:
    entries: list[KeywordEntry] = []
    current: dict[str, Any] | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        entry_match = KEYWORD_ENTRY_PATTERN.match(raw_line)
        if entry_match:
            if current is not None:
                entries.append(build_keyword_entry(current))
            current = {
                "canonical": normalize_keyword(entry_match.group(1)),
                "group": None,
                "aliases": [],
                "related": [],
            }
            continue

        field_match = FIELD_PATTERN.match(raw_line)
        if field_match and current is not None:
            field_name = field_match.group(1)
            field_value = field_match.group(2)
            if field_name == "group":
                current["group"] = normalize_keyword(field_value)
            else:
                current[field_name] = parse_inline_list(field_value)

    if current is not None:
        entries.append(build_keyword_entry(current))

    return build_keyword_taxonomy(entries, path)


def load_keyword_taxonomy_json(path: Path) -> KeywordTaxonomy:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise KeywordParseError(f"Invalid JSON in keyword taxonomy file {path}: {exc}") from exc

    raw_entries = data.get("entries")
    if not isinstance(raw_entries, list) or not raw_entries:
        raise KeywordParseError(f"No keyword entries found in {path}")

    entries = [build_keyword_entry(raw_entry) for raw_entry in raw_entries]
    return build_keyword_taxonomy(entries, path)


def build_keyword_taxonomy(
    entries: list[KeywordEntry],
    source_path: Path,
) -> KeywordTaxonomy:
    if not entries:
        raise KeywordParseError(f"No keyword entries found in {source_path}")

    by_canonical: dict[str, KeywordEntry] = {}
    alias_to_canonical: dict[str, str] = {}
    by_group: dict[str, list[str]] = defaultdict(list)

    for entry in entries:
        if entry.canonical in by_canonical:
            raise KeywordParseError(f"Duplicate canonical keyword: {entry.canonical}")
        by_canonical[entry.canonical] = entry
        by_group[entry.group].append(entry.canonical)

    for entry in entries:
        for alias in entry.aliases:
            if alias in by_canonical and alias != entry.canonical:
                raise KeywordParseError(
                    f"Alias '{alias}' conflicts with canonical keyword '{alias}'"
                )
            existing = alias_to_canonical.get(alias)
            if existing is not None and existing != entry.canonical:
                raise KeywordParseError(
                    f"Alias '{alias}' mapped to both '{existing}' and '{entry.canonical}'"
                )
            alias_to_canonical[alias] = entry.canonical

        for related in entry.related:
            if related not in by_canonical:
                raise KeywordParseError(
                    f"Keyword '{entry.canonical}' references unknown related keyword '{related}'"
                )

    return KeywordTaxonomy(
        entries=entries,
        by_canonical=by_canonical,
        alias_to_canonical=alias_to_canonical,
        by_group={group: sorted(values) for group, values in by_group.items()},
    )


def build_keyword_entry(raw: dict[str, Any]) -> KeywordEntry:
    canonical = normalize_keyword(str(raw.get("canonical") or ""))
    group = normalize_keyword(str(raw.get("group") or ""))
    aliases = [normalize_keyword(str(item)) for item in raw.get("aliases") or []]
    related = [normalize_keyword(str(item)) for item in raw.get("related") or []]

    if not canonical:
        raise KeywordParseError("Keyword entry missing canonical value")
    if group not in GROUPS:
        raise KeywordParseError(f"Keyword '{canonical}' has invalid group '{group}'")

    aliases = [item for item in aliases if item and item != canonical]
    related = [item for item in related if item and item != canonical]

    return KeywordEntry(
        canonical=canonical,
        group=group,
        aliases=sorted(set(aliases)),
        related=sorted(set(related)),
    )


def normalize_component(value: str) -> str:
    return normalize_keyword(value)


def slugify(value: str) -> str:
    text = value.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def iter_task_directories(
    tasks_dir: Path, task_key_pattern: re.Pattern[str]
) -> Iterable[Path]:
    if not tasks_dir.exists():
        raise FileNotFoundError(f"Tasks directory not found: {tasks_dir}")
    for child in sorted(tasks_dir.iterdir()):
        if child.is_dir() and task_key_pattern.match(child.name):
            yield child


def contains_phrase(search_blob: str, value: str) -> bool:
    token_pattern = re.escape(value).replace(r"\-", r"[-\s]")
    pattern = re.compile(rf"(?<![a-z0-9]){token_pattern}(?![a-z0-9])", re.IGNORECASE)
    return pattern.search(search_blob) is not None


def build_keywords(search_blob: str, taxonomy: KeywordTaxonomy) -> list[str]:
    matched: list[str] = []
    for entry in taxonomy.entries:
        if contains_phrase(search_blob, entry.canonical) or any(
            contains_phrase(search_blob, alias) for alias in entry.aliases
        ):
            matched.append(entry.canonical)
    return matched


def parse_task_record(
    task_dir: Path,
    taxonomy: KeywordTaxonomy,
    config: AppConfig,
) -> TaskRecord:
    task_json_path = task_dir / "task.json"
    if not task_json_path.exists():
        raise TaskParseError(f"Missing task.json in {task_dir}")

    task_data = json.loads(task_json_path.read_text(encoding="utf-8"))
    if not isinstance(task_data, dict):
        raise TaskParseError(f"Invalid task.json object in {task_json_path}")

    jira = str(task_data.get("task_key") or task_dir.name)
    if not config.task_key_pattern.match(jira):
        raise TaskParseError(f"Invalid task key: {jira}")

    title = str(task_data.get("task_summary") or jira)
    status = str(task_data.get("status") or "Unknown")
    normalized_components: list[str] = []
    seen_components: set[str] = set()
    for item in cast(list[Any], task_data.get("components") or []):
        normalized_component = normalize_component(str(item))
        if not normalized_component or normalized_component in seen_components:
            continue
        seen_components.add(normalized_component)
        normalized_components.append(normalized_component)

    primary_component = normalized_components[0] if normalized_components else "unknown"
    related_components = normalized_components[1:]

    search_parts = [
        title,
        " ".join(cast(list[Any], task_data.get("components") or [])),
        str(task_data.get("description_text") or task_data.get("description") or ""),
        " ".join(
            str(label) for label in cast(list[Any], task_data.get("labels") or [])
        ),
        " ".join(
            str(related.get("summary") or "")
            for related in cast(list[Any], task_data.get("related_tasks") or [])
            if isinstance(related, dict)
        ),
        " ".join(
            str(related.get("key") or "")
            for related in cast(list[Any], task_data.get("related_tasks") or [])
            if isinstance(related, dict)
        ),
        " ".join(
            str(comment.get("body_text") or comment.get("body") or "")
            for comment in cast(list[Any], task_data.get("comments") or [])
            if isinstance(comment, dict)
        ),
    ]
    search_blob = "\n".join(search_parts).lower()
    keywords = build_keywords(search_blob, taxonomy)
    if primary_component != "unknown" and primary_component in taxonomy.by_canonical:
        if primary_component not in keywords:
            keywords = [primary_component, *keywords]

    keyword_groups: dict[str, list[str]] = defaultdict(list)
    for keyword in keywords:
        entry = taxonomy.by_canonical.get(keyword)
        if entry is None:
            continue
        keyword_groups[entry.group].append(keyword)

    updated_source = str(task_data.get("updated") or "")
    updated_at = (
        datetime.fromisoformat(f"{updated_source}T00:00:00+00:00").isoformat()
        if updated_source
        else datetime.fromtimestamp(
            task_json_path.stat().st_mtime, tz=timezone.utc
        ).isoformat()
    )
    issue_number = int(jira.rsplit("-", 1)[1])

    paths_data = task_data.get("paths") or {}
    raw_path = str(paths_data.get("raw") or "") if isinstance(paths_data, dict) else ""
    related_tasks = [
        str(item.get("key"))
        for item in cast(list[Any], task_data.get("related_tasks") or [])
        if isinstance(item, dict) and str(item.get("key") or "").strip()
    ]

    return TaskRecord(
        jira=jira,
        issue_number=issue_number,
        title=title,
        status=status,
        primary_component=primary_component,
        related_components=related_components,
        keywords=keywords,
        keyword_groups={
            group: sorted(set(values)) for group, values in keyword_groups.items()
        },
        updated_at=updated_at,
        paths={
            "task_json": to_repo_path(task_json_path),
            "raw": raw_path,
        },
        related_tasks=related_tasks,
    )


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


def build_shard_sync_counts(
    tasks: list[TaskRecord], shard_size: int
) -> dict[tuple[int, int], dict[str, int]]:
    shard_counts: dict[tuple[int, int], dict[str, int]] = {}
    if not tasks:
        return shard_counts

    for task in tasks:
        start = (task.issue_number // shard_size) * shard_size
        if task.issue_number % shard_size == 0:
            start -= shard_size
        start += 1
        end = start + shard_size - 1
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


def generate_shards(
    index_dir: Path,
    tasks: list[TaskRecord],
    shard_size: int,
) -> list[dict[str, object]]:
    shards_dir = index_dir / "shards"
    ensure_clean_dir(shards_dir)

    grouped: dict[tuple[int, int], list[TaskRecord]] = defaultdict(list)
    shard_counts = build_shard_sync_counts(tasks, shard_size)
    for task in tasks:
        start = (task.issue_number // shard_size) * shard_size
        if task.issue_number % shard_size == 0:
            start -= shard_size
        start += 1
        end = start + shard_size - 1
        grouped[(start, end)].append(task)

    manifest_shards: list[dict[str, object]] = []
    for (start, end), counts in sorted(shard_counts.items()):
        shard_tasks = grouped.get((start, end), [])
        shard_id = f"{start}-{end}"
        file_path = shards_dir / f"{shard_id}.jsonl"
        write_jsonl(
            file_path,
            [
                task_to_dict(task)
                for task in sorted(shard_tasks, key=lambda x: x.issue_number)
            ],
        )
        jira_numbers = [task.issue_number for task in shard_tasks]
        jira_min = min(jira_numbers) if jira_numbers else start
        jira_max = max(jira_numbers) if jira_numbers else end
        manifest_shards.append(
            {
                "id": shard_id,
                "path": to_repo_path(file_path),
                "jira_min": jira_min,
                "jira_max": jira_max,
                "saved_tasks": counts["saved_tasks"],
                "unsynced_tasks": counts["unsynced_tasks"],
                "total_tasks": counts["total_tasks"],
            }
        )
    return manifest_shards


def generate_lookup_indexes(
    index_dir: Path,
    tasks: list[TaskRecord],
    folder_name: str,
    key_name: str,
    values: Iterable[str],
    selector: Callable[[TaskRecord, str], bool],
) -> None:
    output_dir = index_dir / folder_name
    ensure_clean_dir(output_dir)
    for value in values:
        task_keys = sorted({task.jira for task in tasks if selector(task, value)})
        write_json(
            output_dir / f"{slugify(value)}.json", {key_name: value, "tasks": task_keys}
        )


def task_to_dict(task: TaskRecord) -> dict[str, object]:
    return {
        "jira": task.jira,
        "title": task.title,
        "status": task.status,
        "primary_component": task.primary_component,
        "related_components": task.related_components,
        "keywords": task.keywords,
        "keyword_groups": task.keyword_groups,
        "updated_at": task.updated_at,
        "paths": task.paths,
        "related_tasks": task.related_tasks,
    }


def main() -> int:
    args = parse_args()
    config_path = cast(Path, args.config)
    config = load_config(config_path)

    taxonomy = load_keyword_taxonomy(config.keywords_file)
    tasks = [
        parse_task_record(task_dir, taxonomy, config)
        for task_dir in iter_task_directories(config.tasks_dir, config.task_key_pattern)
        if (task_dir / "task.json").exists()
    ]
    tasks.sort(key=lambda item: item.issue_number)

    _ = config.index_dir.mkdir(parents=True, exist_ok=True)
    shard_manifest = generate_shards(
        config.index_dir,
        tasks,
        config.shard_size,
    )
    components = sorted(
        {
            component
            for task in tasks
            for component in [task.primary_component, *task.related_components]
            if component and component != "unknown"
        }
    )
    generate_lookup_indexes(
        config.index_dir,
        tasks,
        "by-component",
        "component",
        components,
        lambda task, value: (
            task.primary_component == value or value in task.related_components
        ),
    )
    generate_lookup_indexes(
        config.index_dir,
        tasks,
        "by-keyword",
        "keyword",
        taxonomy.by_canonical.keys(),
        lambda task, value: value in task.keywords,
    )
    generate_lookup_indexes(
        config.index_dir,
        tasks,
        "by-group",
        "group",
        taxonomy.by_group.keys(),
        lambda task, value: value in task.keyword_groups,
    )

    write_json(
        config.index_dir / "index.json",
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "shards": shard_manifest,
            "keyword_groups": taxonomy.by_group,
        },
    )

    print(f"Indexed {len(tasks)} tasks into {config.index_dir}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
