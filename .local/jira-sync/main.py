"""Jira task sync driven by local config and environment settings."""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import cast

from config import (
    CONFIG_PATH,
    JIRA_PROJECT_KEY,
    PENDING_TASKS_PATH,
    REPO_ROOT,
    load_app_config,
    validate_project_key,
)
from fetcher import (
    discover_fields,
    fetch_children,
    fetch_issue,
    get_max_issue_id,
    should_fetch_children,
)
from persistence import write_raw_md, write_task_json
from sync_state import add_not_found_id, load_not_found_ids, load_state, save_state

ISSUE_KEY_PATTERN = re.compile(r"^(?P<project>[A-Z][A-Z0-9]+)-(?P<issue_id>\d+)$")


def parse_target(value: str, default_project_key: str) -> tuple[str, int]:
    target = value.strip().upper()
    key_match = ISSUE_KEY_PATTERN.match(target)
    if key_match:
        project = key_match.group("project")
        validate_project_key(project)
        return project, int(key_match.group("issue_id"))
    if target.isdigit():
        return default_project_key, int(target)
    raise ValueError(
        "Target must be an issue number like '2100' or an issue key like 'ABC-2100'"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sync Jira tasks to local markdown files. "
            "Without a positional target, the script resumes or range-syncs issues. "
            "With a positional target and no --start, it downloads only that one issue."
        )
    )
    _ = parser.add_argument(
        "target",
        nargs="?",
        help=(
            "Single issue to download when --start is not provided, "
            "as issue number or full issue key."
        ),
    )
    _ = parser.add_argument(
        "--config",
        type=Path,
        default=CONFIG_PATH,
        help=f"Path to config file (default: {CONFIG_PATH})",
    )
    _ = parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing raw.md and task.json files.",
    )
    _ = parser.add_argument(
        "--start",
        type=int,
        default=None,
        help="Override start ID and run range sync instead of single-target mode.",
    )
    _ = parser.add_argument(
        "--discover",
        action="store_true",
        help="Discover key custom fields (epic, sprint, story points, tags) from Jira.",
    )
    _ = parser.add_argument(
        "--discover-all",
        action="store_true",
        help="Discover ALL custom fields from Jira.",
    )
    _ = parser.add_argument(
        "--get-pending",
        action="store_true",
        help="Scan /dev/tasks for unresolved tasks and write to pending-tasks.txt.",
    )
    _ = parser.add_argument(
        "--pending",
        action="store_true",
        help="Re-sync all tasks in pending-tasks.txt, remove resolved ones.",
    )
    return parser.parse_args()


def sync_one_issue(
    project_key: str,
    issue_id: int,
    force: bool,
    download_path: str,
    download_path_rel: str,
    not_found_state_path: Path,
) -> int:
    key = f"{project_key}-{issue_id}"
    print(f"Project:       {project_key}")
    print(f"Download path: {download_path}")
    print(f"Target:        {key}")
    print(f"Mode:          {'force overwrite' if force else 'skip existing'}")
    print()

    try:
        issue = fetch_issue(project_key, issue_id)
        if issue is None:
            add_not_found_id(not_found_state_path, project_key, issue_id)
            print(
                f"  {key}: not found (deleted or never existed) - added to skipped list"
            )
            print()
            print("--- Done ---")
            print("Created:     0")
            print("Overwritten: 0")
            print("Skipped:     0")
            print("Not found:   1")
            print("Errors:      0")
            return 0

        children = _fetch_children(issue)

        result = write_raw_md(
            issue, force=force, download_path=download_path, epic_children=children
        )
        _ = write_task_json(
            issue,
            force=force,
            download_path=download_path,
            download_path_rel=download_path_rel,
            epic_children=children,
        )

        created = int(result == "created")
        overwritten = int(result == "overwritten")
        skipped = int(result == "skipped")

        if children:
            print(f"  {key}: {result} (with {len(children)} children)")
        else:
            print(f"  {key}: {result}")
        print()
        print("--- Done ---")
        print(f"Created:     {created}")
        print(f"Overwritten: {overwritten}")
        print(f"Skipped:     {skipped}")
        print("Not found:   0")
        print("Errors:      0")
        return 0
    except Exception as e:
        print(f"  {key}: ERROR - {e}")
        print()
        print("--- Done ---")
        print("Created:     0")
        print("Overwritten: 0")
        print("Skipped:     0")
        print("Not found:   0")
        print("Errors:      1")
        return 1


def _fetch_children(issue: dict[str, object]) -> list[dict[str, object]] | None:
    """Fetch child issues for Epics, skipping if subtasks already exist."""
    if not should_fetch_children(issue):
        return None
    key = str(issue.get("key", "")).strip()
    if not key:
        return None
    try:
        children = fetch_children(key)
    except Exception as e:
        print(f"  {key}: ERROR fetching children - {e}")
        return None
    return children


RESOLVED_STATUSES = {"done", "completed", "resolved", "closed", "accepted", "canceled"}

NOT_SYNC_PATH = REPO_ROOT / ".local" / "jira-sync" / "result" / "tasks-not-sync.txt"
FORCE_SYNC_PATH = REPO_ROOT / ".local" / "jira-sync" / "result" / "tasks-force-sync.txt"


def _load_not_sync() -> set[str]:
    """Load task keys that should never be synced."""
    if not NOT_SYNC_PATH.is_file():
        return set()
    return {
        line.strip()
        for line in NOT_SYNC_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def _load_force_sync() -> set[str]:
    """Load task keys that should always be force-overwritten."""
    if not FORCE_SYNC_PATH.is_file():
        return set()
    return {
        line.strip()
        for line in FORCE_SYNC_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def _get_pending(download_path: str) -> None:
    """Scan downloaded tasks for unresolved ones, write to pending-tasks.txt."""
    tasks_dir = Path(download_path)
    if not tasks_dir.is_dir():
        print(f"Download path not found: {download_path}")
        return

    pending: list[str] = []
    not_sync = _load_not_sync()
    for task_dir in sorted(tasks_dir.iterdir()):
        if not task_dir.is_dir():
            continue
        task_json = task_dir / "task.json"
        if not task_json.is_file():
            continue
        try:
            data = json.loads(task_json.read_text(encoding="utf-8"))
        except Exception:
            continue
        status = (data.get("status") or "").strip().lower()
        task_key = data.get("task_key", task_dir.name)
        if not task_key.startswith(JIRA_PROJECT_KEY + "-"):
            continue
        if task_key in not_sync:
            continue
        if status not in RESOLVED_STATUSES:
            pending.append(task_key)

    PENDING_TASKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PENDING_TASKS_PATH.write_text("\n".join(pending) + "\n", encoding="utf-8")
    print(f"Wrote {len(pending)} pending tasks to tasks-pending.txt")


def _sync_pending(
    project_key: str,
    force: bool,
    download_path: str,
    download_path_rel: str,
    not_found_state_path: Path,
) -> None:
    """Re-sync all tasks in pending-tasks.txt, remove resolved ones."""
    if not PENDING_TASKS_PATH.is_file():
        print(f"No pending tasks file at {PENDING_TASKS_PATH}")
        return

    lines = [
        line.strip()
        for line in PENDING_TASKS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not lines:
        print("Pending tasks list is empty.")
        return

    print(f"Syncing {len(lines)} pending tasks...")
    print()

    remaining: list[str] = []
    not_sync = _load_not_sync()
    for task_key in lines:
        if not task_key.startswith(project_key + "-"):
            print(f"  {task_key}: skip - wrong project")
            continue
        try:
            project, issue_id = parse_target(task_key, project_key)
        except ValueError as e:
            print(f"  {task_key}: skip - {e}")
            remaining.append(task_key)
            continue

        key = f"{project}-{issue_id}"
        if key in not_sync:
            print(f"  {key}: in not-sync list - skip")
            continue
        issue = fetch_issue(project, issue_id)
        if issue is None:
            print(f"  {key}: not found - keeping in list")
            remaining.append(key)
            continue

        status = (
            (((issue.get("fields") or {}).get("status") or {}).get("name", "") or "")
            .strip()
            .lower()
        )

        children = _fetch_children(issue)
        write_raw_md(
            issue, force=True, download_path=download_path, epic_children=children
        )
        _ = write_task_json(
            issue,
            force=True,
            download_path=download_path,
            download_path_rel=download_path_rel,
            epic_children=children,
        )

        if status in RESOLVED_STATUSES:
            print(f"  {key}: {status} - removed from pending")
        else:
            print(f"  {key}: {status} - keeping in pending")
            remaining.append(key)

    PENDING_TASKS_PATH.write_text("\n".join(remaining) + "\n", encoding="utf-8")
    print()
    print(f"Remaining pending: {len(remaining)}")


def _range_sync_issue(
    project_key: str,
    issue_id: int,
    force: bool,
    download_path: str,
    download_path_rel: str,
    sync_state_path: Path,
    not_found_state_path: Path,
    known_not_found_ids: set[str],
    not_sync: set[str],
    force_sync: set[str],
) -> tuple[str, int]:
    """Sync one issue during range sync. Returns (result, children_count)."""
    key = f"{project_key}-{issue_id}"
    if key in not_sync:
        print(f"  {key}: in not-sync list - skip")
        save_state(sync_state_path, project_key, issue_id)
        return ("skipped", 0)
    if key in known_not_found_ids:
        print(f"  {key}: known missing - skip")
        save_state(sync_state_path, project_key, issue_id)
        return ("not_found", 0)

    effective_force = force or key in force_sync
    issue = fetch_issue(project_key, issue_id)
    if issue is None:
        add_not_found_id(not_found_state_path, project_key, issue_id)
        print(f"  {key}: not found")
        save_state(sync_state_path, project_key, issue_id)
        return ("not_found", 0)

    children = _fetch_children(issue)
    clen = len(children) if children else 0
    result = write_raw_md(
        issue,
        force=effective_force,
        download_path=download_path,
        epic_children=children,
    )
    _ = write_task_json(
        issue,
        force=effective_force,
        download_path=download_path,
        download_path_rel=download_path_rel,
        epic_children=children,
    )
    save_state(sync_state_path, project_key, issue_id)
    suffix = f" ({clen} children)" if children else ""
    print(f"  {key}: {result}{suffix}")
    return (result, clen)


def main() -> None:
    args = parse_args()
    config_path = cast(Path, args.config)
    app_config = load_app_config(config_path)

    default_project_key = JIRA_PROJECT_KEY
    download_path = str(app_config.download_path)
    download_path_rel = app_config.download_path.relative_to(REPO_ROOT).as_posix()
    sync_state_path = app_config.sync_state_path
    not_found_state_path = app_config.not_found_state_path
    force = bool(args.force)
    target = cast(str | None, args.target)
    start_override = cast(int | None, args.start)
    discover = bool(args.discover)
    discover_all = bool(args.discover_all)
    get_pending = bool(args.get_pending)
    do_pending = bool(args.pending)

    if discover or discover_all:
        discover_fields(show_all=discover_all)
        sys.exit(0)

    if get_pending:
        _get_pending(download_path)
        sys.exit(0)

    if do_pending:
        _sync_pending(
            default_project_key,
            True,
            download_path,
            download_path_rel,
            not_found_state_path,
        )
        sys.exit(0)

    if target is not None and start_override is None:
        try:
            project_key, issue_id = parse_target(target, default_project_key)
        except ValueError as e:
            print(f"ERROR: {e}")
            sys.exit(2)
        sys.exit(
            sync_one_issue(
                project_key,
                issue_id,
                force,
                download_path,
                download_path_rel,
                not_found_state_path,
            )
        )

    project_key = default_project_key
    state = load_state(sync_state_path, project_key)
    known_not_found_ids = load_not_found_ids(not_found_state_path, project_key)
    not_sync = _load_not_sync()
    force_sync = _load_force_sync()
    start_id = (
        start_override
        if start_override is not None
        else int(state["max_downloaded_id"]) + 1
    )

    print(f"Fetching max issue ID for project {project_key}...")
    try:
        max_id = get_max_issue_id(project_key)
    except Exception as e:
        print(f"ERROR: Could not fetch max issue ID from Jira: {e}")
        sys.exit(1)

    if max_id == 0:
        print("No issues found in project. Nothing to download.")
        sys.exit(0)

    print(f"Project:       {project_key}")
    print(f"Download path: {download_path}")
    print(f"Range:         {project_key}-{start_id} -> {project_key}-{max_id}")
    print(f"Mode:          {'force overwrite' if force else 'skip existing'}")
    print()

    created = skipped = overwritten = not_found = errors = 0
    last_successful_id = int(state["max_downloaded_id"])

    for issue_id in range(start_id, max_id + 1):
        try:
            result, _clen = _range_sync_issue(
                project_key,
                issue_id,
                force,
                download_path,
                download_path_rel,
                sync_state_path,
                not_found_state_path,
                known_not_found_ids,
                not_sync,
                force_sync,
            )
            if result == "skipped":
                skipped += 1
            elif result == "overwritten":
                overwritten += 1
            elif result == "not_found":
                not_found += 1
            else:
                created += 1
            last_successful_id = issue_id
        except Exception as e:
            errors += 1
            print(f"  {project_key}-{issue_id}: ERROR - {e}")

    print()
    print("--- Done ---")
    print(f"Created:     {created}")
    print(f"Overwritten: {overwritten}")
    print(f"Skipped:     {skipped}")
    print(f"Not found:   {not_found}")
    print(f"Errors:      {errors}")
    print(f"MaxDownloadedId saved: {last_successful_id}")


if __name__ == "__main__":
    main()
