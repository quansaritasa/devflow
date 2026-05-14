"""Jira task sync driven by local config and environment settings."""

import argparse
import re
import sys
from pathlib import Path
from typing import cast

from config import CONFIG_PATH, JIRA_PROJECT_KEY, REPO_ROOT, load_app_config
from fetcher import fetch_issue, get_max_issue_id
from persistence import write_raw_md, write_task_json
from sync_state import add_not_found_id, load_not_found_ids, load_state, save_state

ISSUE_KEY_PATTERN = re.compile(r"^(?P<project>[A-Z][A-Z0-9]+)-(?P<issue_id>\d+)$")


def parse_target(value: str, default_project_key: str) -> tuple[str, int]:
    target = value.strip().upper()
    key_match = ISSUE_KEY_PATTERN.match(target)
    if key_match:
        return key_match.group("project"), int(key_match.group("issue_id"))
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

        result = write_raw_md(issue, force=force, download_path=download_path)
        _ = write_task_json(
            issue,
            force=force,
            download_path=download_path,
            download_path_rel=download_path_rel,
        )

        created = int(result == "created")
        overwritten = int(result == "overwritten")
        skipped = int(result == "skipped")

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
        key = f"{project_key}-{issue_id}"
        if issue_id in known_not_found_ids:
            print(f"  {key}: known missing from not-found state - skip Jira fetch")
            not_found += 1
            last_successful_id = issue_id
            save_state(sync_state_path, project_key, last_successful_id)
            continue

        try:
            issue = fetch_issue(project_key, issue_id)
            if issue is None:
                add_not_found_id(not_found_state_path, project_key, issue_id)
                print(
                    f"  {key}: not found (deleted or never existed) - added to skipped list"
                )
                not_found += 1
                last_successful_id = issue_id
                save_state(sync_state_path, project_key, last_successful_id)
                continue

            result = write_raw_md(issue, force=force, download_path=download_path)
            _ = write_task_json(
                issue,
                force=force,
                download_path=download_path,
                download_path_rel=download_path_rel,
            )
            last_successful_id = issue_id
            save_state(sync_state_path, project_key, last_successful_id)

            if result == "skipped":
                skipped += 1
                print(f"  {key}: skipped")
            elif result == "overwritten":
                overwritten += 1
                print(f"  {key}: overwritten")
            else:
                created += 1
                print(f"  {key}: created")

        except Exception as e:
            errors += 1
            print(f"  {key}: ERROR - {e}")

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
