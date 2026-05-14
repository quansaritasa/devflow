from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


SECTION_GROUP_MAP = {
    "1. Product Areas": "product-area",
    "2. Domain Entities": "domain-entity",
    "3. Workflow": "workflow",
    "4. Auth and Access": "auth-access",
    "5. Technical Areas": "technical",
    "6. UI and UX": "ui-ux",
    "7. Integrations": "integration",
    "8. Environment and Release": "environment",
    "9. Issue Shapes": "issue-shape",
}


@dataclass
class KeywordEntry:
    canonical: str
    group: str
    aliases: List[str]
    related: List[str]


def parse_inline_list(value: str) -> List[str]:
    value = value.strip()
    if value == "[]":
        return []
    if not (value.startswith("[") and value.endswith("]")):
        raise ValueError(f"Expected inline list, got: {value}")
    inner = value[1:-1].strip()
    if not inner:
        return []
    return [item.strip() for item in inner.split(",") if item.strip()]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def resolve_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolve_repo_path(repo_root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return repo_root / path


def load_config(config_path: Path) -> dict:
    return load_json(config_path)


def load_rules(rules_path: Path) -> dict:
    return load_json(rules_path)


def parse_keywords_md(path: Path) -> List[KeywordEntry]:
    lines = path.read_text(encoding="utf-8").splitlines()
    entries: List[KeywordEntry] = []
    current_group = None
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        if line.startswith("## "):
            section_name = line[3:].strip()
            current_group = SECTION_GROUP_MAP.get(section_name)
            i += 1
            continue

        if line.startswith("- canonical: "):
            if current_group is None:
                raise ValueError("Found keyword entry before section header")

            canonical = line.split(": ", 1)[1].strip()

            if i + 3 >= len(lines):
                raise ValueError(f"Incomplete entry for {canonical}")

            group_line = lines[i + 1].strip()
            aliases_line = lines[i + 2].strip()
            related_line = lines[i + 3].strip()

            if not group_line.startswith("group: "):
                raise ValueError(f"Missing group for {canonical}")
            if not aliases_line.startswith("aliases: "):
                raise ValueError(f"Missing aliases for {canonical}")
            if not related_line.startswith("related: "):
                raise ValueError(f"Missing related for {canonical}")

            group = group_line.split(": ", 1)[1].strip()
            aliases = parse_inline_list(aliases_line.split(": ", 1)[1].strip())
            related = parse_inline_list(related_line.split(": ", 1)[1].strip())

            entries.append(
                KeywordEntry(
                    canonical=canonical,
                    group=group,
                    aliases=aliases,
                    related=related,
                )
            )
            i += 4
            continue

        i += 1

    return entries


def validate_entries(entries: List[KeywordEntry], allowed_groups: List[str]) -> None:
    canonicals = set()

    for entry in entries:
        if entry.group not in allowed_groups:
            raise ValueError(f"Invalid group for {entry.canonical}: {entry.group}")

        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", entry.canonical):
            raise ValueError(f"Invalid canonical format: {entry.canonical}")

        if entry.canonical in canonicals:
            raise ValueError(f"Duplicate canonical: {entry.canonical}")
        canonicals.add(entry.canonical)

    for entry in entries:
        for related in entry.related:
            if related not in canonicals:
                raise ValueError(
                    f"Unknown related keyword '{related}' in '{entry.canonical}'"
                )


def build_keywords_json(
    entries: List[KeywordEntry],
    group_order: List[str],
    group_labels: Dict[str, str],
    version: int,
) -> dict:
    group_rank = {group: index for index, group in enumerate(group_order)}
    sorted_entries = sorted(
        entries,
        key=lambda item: (group_rank[item.group], item.canonical),
    )
    return {
        "version": version,
        "group_order": group_order,
        "group_labels": group_labels,
        "entries": [
            {
                "canonical": entry.canonical,
                "group": entry.group,
                "aliases": entry.aliases,
                "related": entry.related,
            }
            for entry in sorted_entries
        ],
    }


def load_keywords_json(path: Path) -> dict:
    return load_json(path)


def export_keywords_md(data: dict) -> str:
    group_order = data["group_order"]
    group_labels = data["group_labels"]
    entries = data["entries"]

    by_group: Dict[str, List[dict]] = {group: [] for group in group_order}
    for entry in entries:
        by_group[entry["group"]].append(entry)

    lines: List[str] = [
        "# Keywords",
        "",
        "Canonical keyword taxonomy for task indexing and related-task search.",
        "",
        "Use canonical kebab-case terms.",
        "Store canonical keywords only.",
        "Use aliases for matching.",
        "Keep terms reusable and broad enough to cover multiple tasks.",
        "",
        "---",
        "",
    ]

    for index, group in enumerate(group_order, start=1):
        label = group_labels[group]
        lines.append(f"## {index}. {label}")
        lines.append("")

        for entry in sorted(by_group[group], key=lambda item: item["canonical"]):
            aliases = ", ".join(entry["aliases"])
            related = ", ".join(entry["related"])
            lines.append(f"- canonical: {entry['canonical']}")
            lines.append(f"  group: {entry['group']}")
            lines.append(f"  aliases: [{aliases}]")
            lines.append(f"  related: [{related}]")
            lines.append("")

        if index < len(group_order):
            lines.append("---")
            lines.append("")

    return "\n".join(lines) + "\n"


def main() -> int:
    app_dir = Path(__file__).resolve().parent
    repo_root = resolve_repo_root()

    config = load_config(app_dir / "config.json")
    rules = load_rules(app_dir / "rules.json")

    source_md = resolve_repo_path(repo_root, config["source_keywords_md"])
    source_json = resolve_repo_path(repo_root, config["source_keywords_json"])
    generated_md = resolve_repo_path(repo_root, config["generated_keywords_md"])

    entries = parse_keywords_md(source_md)
    validate_entries(entries, rules["allowed_groups"])

    keywords_json = build_keywords_json(
        entries=entries,
        group_order=config["group_order"],
        group_labels=rules["group_labels"],
        version=rules["default_version"],
    )
    save_json(source_json, keywords_json)

    reloaded = load_keywords_json(source_json)
    exported_md = export_keywords_md(reloaded)
    generated_md.parent.mkdir(parents=True, exist_ok=True)
    generated_md.write_text(exported_md, encoding="utf-8")

    print(f"Wrote {source_json}")
    print(f"Wrote {generated_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
