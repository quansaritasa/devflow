"""GitHub pull request sync driven by local config and environment settings."""

import argparse
import os
import re
import sys
from pathlib import Path
from typing import cast

from config import (
    CONFIG_PATH,
    DEFAULT_PROJECT_KEY,
    PR_DOWNLOAD_PATH,
    TASK_DOWNLOAD_PATH,
)
from fetcher import (
    fetch_pull_request_details,
    filter_new_or_updated_pull_requests,
    find_pull_requests_for_task,
)
from sync_state import (
    clear_project_resume_issue_id,
    load_project_resume_issue_id,
    load_task_state,
    save_project_resume_issue_id,
    save_task_not_found,
    save_task_state,
    should_skip_not_found_task,
)
from writer import write_pr_files

TASK_KEY_PATTERN = re.compile(r"^(?P<project>[A-Z][A-Z0-9]+)-(?P<issue_id>\d+)$")
PROJECT_PREFIX_PATTERN = re.compile(r"^(?P<project>[A-Z][A-Z0-9]+)-\*$")
TASK_RANGE_PATTERN = re.compile(
    r"^(?P<project>[A-Z][A-Z0-9]+)-(?P<start>\d+)\.\.(?P<end>\d+)$"
)
TASK_DASH_RANGE_PATTERN = re.compile(
    r"^(?P<project>[A-Z][A-Z0-9]+)-(?P<start>\d+)-(?P<end>\d+)$"
)
NUMERIC_TARGET_PATTERN = re.compile(r"^(?P<issue_id>\d+)$")
NUMERIC_RANGE_PATTERN = re.compile(r"^(?P<start>\d+)-(?P<end>\d+)$")
NUMERIC_DOT_RANGE_PATTERN = re.compile(r"^(?P<start>\d+)\.\.(?P<end>\d+)$")


def parse_target(value: str) -> str:
    task_key = value.strip().upper()
    if not TASK_KEY_PATTERN.match(task_key):
        raise ValueError("Target must be a task key like 'ABC-2100'")
    return task_key


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Sync GitHub pull request summaries for a single Jira-style task key."
        )
    )
    _ = parser.add_argument(
        "target",
        nargs="?",
        help=(
            "Task selector to sync: single key like ABC-2100 or numeric 2100, "
            "project prefix like ABC-*, project range like ABC-2100..2125 or ABC-2100-2125, "
            "or numeric range like 2100-2125 or 2100..2125 using the default project key."
        ),
    )
    _ = parser.add_argument(
        "--all",
        action="store_true",
        help="Sync all task folders under the configured task download path.",
    )
    _ = parser.add_argument(
        "--config",
        type=Path,
        default=CONFIG_PATH,
        help=f"Path to config file (default: {CONFIG_PATH})",
    )
    _ = parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print repository-level debug output.",
    )
    _ = parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass cached no-PR skip state and force a fresh GitHub lookup.",
    )
    _ = parser.add_argument(
        "--reset-resume",
        action="store_true",
        help="Clear saved checkpoint progress for the selected project sync before syncing.",
    )
    return parser.parse_args()


def sync_task(task_key: str, force: bool = False) -> int:
    print(f"Task:          {task_key}")
    print(f"PR path:       {PR_DOWNLOAD_PATH}/{task_key}")

    try:
        retry_after = should_skip_not_found_task(task_key)
        if retry_after and not force:
            print("PR check:      skipped")
            print(f"Reason:        previously not found; retry after {retry_after}")
            return 0
        if retry_after and force:
            print("PR check:      forced")
            print("Reason:        bypassing cached not-found retry window")

        state = load_task_state(task_key)
        previous_ids_raw = state.get("last_pr_ids", [])
        previous_ids: list[str] = []
        if isinstance(previous_ids_raw, list):
            for pr_id in previous_ids_raw:
                if isinstance(pr_id, str):
                    previous_ids.append(pr_id)
        last_synced_at = state.get("last_synced_at")
        last_synced_value = last_synced_at if isinstance(last_synced_at, str) else None

        pulls = find_pull_requests_for_task(task_key)
        if not pulls:
            print("PRs found:     0")
            print("Saved:         no")
            print(
                "Note: no PRs were found. This task might not be a coding task, or the configured repositories may not contain its PRs."
            )
            save_task_not_found(task_key)
            return 0

        changed_pulls = (
            pulls
            if force
            else filter_new_or_updated_pull_requests(
                pulls,
                previous_ids,
                last_synced_value,
            )
        )
        current_ids: list[str] = []
        for pull in pulls:
            pull_number = pull.get("number")
            repository = pull.get("repository")
            if isinstance(pull_number, int) and isinstance(repository, str):
                current_ids.append(f"{repository}#{pull_number}")

        if not changed_pulls:
            save_task_state(task_key, current_ids)
            print(f"PRs found:     {len(pulls)}")
            print("PR changes:    0")
            print("Saved:         no changes")
            return 0

        details_list: list[dict[str, object]] = []
        for pull in changed_pulls:
            pull_number_raw = pull.get("number")
            repository = pull.get("repository")
            if not isinstance(pull_number_raw, int) or not isinstance(repository, str):
                continue
            details = fetch_pull_request_details(repository, pull_number_raw)
            details_list.append(details)

        total_written = write_pr_files(task_key, details_list, overwrite=force)
        save_task_state(task_key, current_ids)
        print(f"PRs found:     {len(pulls)}")
        print(f"PR changes:    {len(details_list)}")
        print(f"PRs saved:     {total_written}")
        print(f"Saved files:   {PR_DOWNLOAD_PATH}/{task_key}/pr.md, pr.json")
        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        return 1


def _discover_task_keys() -> list[str]:
    task_root = Path(TASK_DOWNLOAD_PATH)
    if not task_root.exists():
        return []
    task_keys: list[str] = []
    for child in sorted(task_root.iterdir()):
        if child.is_dir() and TASK_KEY_PATTERN.match(child.name):
            task_keys.append(child.name)
    return task_keys


def _build_project_range(project_key: str, start_id: int, end_id: int) -> list[str]:
    return [f"{project_key}-{issue_id}" for issue_id in range(start_id, end_id + 1)]


def _project_and_issue_id(task_key: str) -> tuple[str, int] | None:
    match = TASK_KEY_PATTERN.fullmatch(task_key)
    if not match:
        return None
    return match.group("project"), int(match.group("issue_id"))


def _select_task_keys(
    selector: str,
    reset_resume: bool = False,
) -> tuple[list[str], bool]:
    task_keys = _discover_task_keys()

    numeric_match = NUMERIC_TARGET_PATTERN.match(selector)
    if numeric_match:
        if not DEFAULT_PROJECT_KEY:
            raise ValueError(
                "Numeric selectors require default_project_key in config.json"
            )
        return [f"{DEFAULT_PROJECT_KEY}-{numeric_match.group('issue_id')}"], False

    numeric_range_match = NUMERIC_RANGE_PATTERN.match(
        selector
    ) or NUMERIC_DOT_RANGE_PATTERN.match(selector)
    if numeric_range_match:
        if not DEFAULT_PROJECT_KEY:
            raise ValueError(
                "Numeric range selectors require default_project_key in config.json"
            )
        start_id = int(numeric_range_match.group("start"))
        end_id = int(numeric_range_match.group("end"))
        if start_id > end_id:
            raise ValueError("Range start must be less than or equal to range end")
        return _build_project_range(DEFAULT_PROJECT_KEY, start_id, end_id), False

    prefix_match = PROJECT_PREFIX_PATTERN.match(selector)
    if prefix_match:
        project_key = prefix_match.group("project")
        project_task_keys = [
            task_key for task_key in task_keys if task_key.startswith(f"{project_key}-")
        ]
        if reset_resume:
            clear_project_resume_issue_id(project_key)
        last_task_id = load_project_resume_issue_id(project_key)
        if isinstance(last_task_id, int):
            project_task_keys = [
                task_key
                for task_key in project_task_keys
                if (
                    (parts := _project_and_issue_id(task_key)) is not None
                    and parts[1] > last_task_id
                )
            ]
        return project_task_keys, True

    range_match = TASK_RANGE_PATTERN.match(selector) or TASK_DASH_RANGE_PATTERN.match(
        selector
    )
    if range_match:
        project_key = range_match.group("project")
        start_id = int(range_match.group("start"))
        end_id = int(range_match.group("end"))
        if start_id > end_id:
            raise ValueError("Range start must be less than or equal to range end")
        return _build_project_range(project_key, start_id, end_id), False

    exact_task = parse_target(selector)
    if reset_resume:
        parts = _project_and_issue_id(exact_task)
        if parts:
            clear_project_resume_issue_id(parts[0])
    return [exact_task], False


def _sync_many(
    task_keys: list[str], update_checkpoint: bool = False, force: bool = False
) -> int:
    if not task_keys:
        print(f"No matching task folders found in {TASK_DOWNLOAD_PATH}")
        return 0
    failures = 0
    for task_key in task_keys:
        print()
        print(f"=== {task_key} ===")
        result = sync_task(task_key, force=force)
        failures += result
        if result == 0 and update_checkpoint:
            parts = _project_and_issue_id(task_key)
            if parts:
                project_key, issue_id = parts
                save_project_resume_issue_id(project_key, issue_id)
    return 1 if failures else 0


def main() -> None:
    args = parse_args()
    _ = cast(Path, args.config)
    target = cast(str | None, args.target)
    sync_all = cast(bool, args.all)
    verbose = cast(bool, args.verbose)
    force = cast(bool, args.force)
    reset_resume = cast(bool, args.reset_resume)

    if verbose:
        os.environ["GITHUB_SYNC_VERBOSE"] = "1"

    if sync_all:
        if reset_resume:
            print("ERROR: --reset-resume is not supported with --all")
            sys.exit(2)
        task_keys = _discover_task_keys()
        if not task_keys:
            print(f"No task folders found in {TASK_DOWNLOAD_PATH}")
            sys.exit(0)
        sys.exit(_sync_many(task_keys, force=force))

    if target is None:
        if not DEFAULT_PROJECT_KEY:
            print(
                "ERROR: Provide a task key, numeric selector, project prefix, range, or use --all"
            )
            print(
                "Hint: set default_project_key in config.json to make 'python main.py' use that project by default"
            )
            sys.exit(2)
        target = f"{DEFAULT_PROJECT_KEY}-*"

    try:
        task_keys, update_checkpoint = _select_task_keys(
            target.strip().upper(),
            reset_resume=reset_resume,
        )
    except ValueError as e:
        print(f"ERROR: {e}")
        sys.exit(2)

    normalized_target = target.strip().upper()
    is_single_target = TASK_KEY_PATTERN.fullmatch(
        normalized_target
    ) or NUMERIC_TARGET_PATTERN.fullmatch(normalized_target)

    if is_single_target:
        if len(task_keys) != 1:
            print(
                f"ERROR: Expected exactly one task for target '{normalized_target}', found {len(task_keys)}"
            )
            sys.exit(2)
        sys.exit(sync_task(task_keys[0], force=force))

    if update_checkpoint and not task_keys:
        print("No remaining tasks to sync for the requested project checkpoint")
        sys.exit(0)

    sys.exit(_sync_many(task_keys, update_checkpoint=update_checkpoint, force=force))


if __name__ == "__main__":
    main()
