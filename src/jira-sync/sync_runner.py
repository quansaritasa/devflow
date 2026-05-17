"""Sync runner: single-task and range-sync orchestration."""

from pathlib import Path

from fetcher import fetch_children, fetch_issue, should_fetch_children
from github_pr import fetch_and_write_pr
from config import GITHUB_REPO
from persistence import write_raw_md, write_task_json
from sync_state import add_not_found_id, save_state


def _fetch_children_if_epic(issue: dict[str, object]) -> list[dict[str, object]] | None:
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


def sync_one_issue(
    project_key: str,
    issue_id: int,
    force: bool,
    download_path: str,
    download_path_rel: str,
    not_found_state_path: Path,
    with_prs: bool = False,
) -> int:
    """Sync a single Jira issue to raw.md and task.json."""
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
            _print_result(key, "not_found", 0)
            return 0

        children = _fetch_children_if_epic(issue)
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

        if with_prs and GITHUB_REPO:
            fetch_and_write_pr(key, download_path, GITHUB_REPO, force=force)

        clen = len(children) if children else 0
        _print_result(key, result, clen)
        return 0
    except Exception as e:
        print(f"  {key}: ERROR - {e}")
        _print_result(key, "error", 0)
        return 1


def _print_result(key: str, result: str, children_count: int) -> None:
    suffix = f" (with {children_count} children)" if children_count else ""
    if result == "not_found":
        print(f"  {key}: not found - added to skipped list")
        print()
    else:
        print(f"  {key}: {result}{suffix}")
        print()
    print("--- Done ---")
    if result == "not_found":
        print(
            "Created:     0\nOverwritten: 0\nSkipped:     0\nNot found:   1\nErrors:      0"
        )
    elif result == "error":
        print(
            "Created:     0\nOverwritten: 0\nSkipped:     0\nNot found:   0\nErrors:      1"
        )
    else:
        created = int(result == "created")
        overwritten = int(result == "overwritten")
        skipped = int(result == "skipped")
        print(f"Created:     {created}")
        print(f"Overwritten: {overwritten}")
        print(f"Skipped:     {skipped}")
        print("Not found:   0")
        print("Errors:      0")


def range_sync_issue(
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

    children = _fetch_children_if_epic(issue)
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
