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
    REPO_ROOT,
    load_app_config,
    validate_project_key,
)
from fetcher import discover_fields, fetch_issue, get_max_issue_id
from persistence import write_raw_md, write_task_json
from github_pr import fetch_and_write_pr
from sync_runner import _fetch_children_if_epic, range_sync_issue, sync_one_issue
from sync_state import add_not_found_id, load_not_found_ids, load_state
from task_lists import RESOLVED_STATUSES, TaskListManager

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
        help="Discover key custom fields from Jira.",
    )
    _ = parser.add_argument(
        "--discover-all",
        action="store_true",
        help="Discover ALL custom fields from Jira.",
    )
    _ = parser.add_argument(
        "--get-pending",
        action="store_true",
        help="Scan dev/tasks for unresolved tasks and write to tasks-pending.txt.",
    )
    _ = parser.add_argument(
        "--pending",
        action="store_true",
        help="Re-sync all tasks in tasks-pending.txt, remove resolved ones.",
    )
    _ = parser.add_argument(
        "--with-prs",
        action="store_true",
        help="Also fetch GitHub PR data for each synced task.",
    )
    return parser.parse_args()


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

    # -- discover --
    if bool(args.discover) or bool(args.discover_all):
        discover_fields(show_all=bool(args.discover_all))
        sys.exit(0)

    lists = TaskListManager()

    # -- get-pending --
    if bool(args.get_pending):
        lists.build_pending(download_path)
        sys.exit(0)

    # -- pending re-sync --
    if bool(args.pending):
        _sync_pending_tasks(
            lists,
            default_project_key,
            download_path,
            download_path_rel,
            not_found_state_path,
        )
        sys.exit(0)

    # -- single task --
    if target is not None and start_override is None:
        try:
            project_key, issue_id = parse_target(target, default_project_key)
        except ValueError as e:
            print(f"ERROR: {e}")
            sys.exit(2)
        with_prs = bool(args.with_prs)
        sys.exit(
            sync_one_issue(
                project_key,
                issue_id,
                force,
                download_path,
                download_path_rel,
                not_found_state_path,
                with_prs=with_prs,
            )
        )

    # -- range sync --
    project_key = default_project_key
    state = load_state(sync_state_path, project_key)
    known_not_found_ids = load_not_found_ids(not_found_state_path, project_key)
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
            result, _clen = range_sync_issue(
                project_key,
                issue_id,
                force,
                download_path,
                download_path_rel,
                sync_state_path,
                not_found_state_path,
                known_not_found_ids,
                lists.not_sync,
                lists.force_sync,
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


def _sync_pending_tasks(
    lists: TaskListManager,
    project_key: str,
    download_path: str,
    download_path_rel: str,
    not_found_state_path: Path,
) -> None:
    """Re-sync all tasks in tasks-pending.txt, remove resolved ones."""
    lines = lists.load_pending()
    if not lines:
        print("Pending tasks list is empty.")
        return

    print(f"Syncing {len(lines)} pending tasks...")
    print()

    remaining: list[str] = []
    for task_key in lines:
        if not task_key.startswith(project_key + "-"):
            print(f"  {task_key}: skip - wrong project")
            continue
        if task_key in lists.not_sync:
            print(f"  {task_key}: in not-sync list - skip")
            continue

        try:
            project, issue_id = parse_target(task_key, project_key)
        except ValueError as e:
            print(f"  {task_key}: skip - {e}")
            remaining.append(task_key)
            continue

        key = f"{project}-{issue_id}"
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

        children = _fetch_children_if_epic(issue)
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

    lists.save_pending(remaining)
    print()
    print(f"Remaining pending: {len(remaining)}")


if __name__ == "__main__":
    main()
