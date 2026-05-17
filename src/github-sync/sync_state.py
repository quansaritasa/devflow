import json
from datetime import datetime, timedelta, timezone

from config import SYNC_STATE_PATH

_DEFAULT_STATE = {"tasks": {}, "last_full_sync_at": None, "range_progress": {}}
_NOT_FOUND_RETRY_DAYS = (1, 3, 7)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _now_utc().isoformat()


def _load_state() -> dict[str, object]:
    if not SYNC_STATE_PATH.exists():
        return dict(_DEFAULT_STATE)
    try:
        with SYNC_STATE_PATH.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULT_STATE)
    return data if isinstance(data, dict) else dict(_DEFAULT_STATE)


def _save_state(data: dict[str, object]) -> None:
    data["last_full_sync_at"] = _iso_now()
    SYNC_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SYNC_STATE_PATH.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")


def _task_state_with_defaults(
    task_state: dict[str, object] | None = None,
) -> dict[str, object]:
    source = task_state if isinstance(task_state, dict) else {}
    return {
        "last_synced_at": source.get("last_synced_at"),
        "last_checked_at": source.get("last_checked_at"),
        "last_pr_ids": source.get("last_pr_ids", []),
        "last_result": source.get("last_result"),
        "not_found_count": source.get("not_found_count", 0),
        "retry_after": source.get("retry_after"),
    }


def load_task_state(task_key: str) -> dict[str, object]:
    data = _load_state()
    tasks = data.get("tasks", {})
    if not isinstance(tasks, dict):
        return _task_state_with_defaults()
    task_state = tasks.get(task_key)
    return _task_state_with_defaults(
        task_state if isinstance(task_state, dict) else None
    )


def should_skip_not_found_task(task_key: str) -> str | None:
    task_state = load_task_state(task_key)
    if task_state.get("last_result") != "not_found":
        return None
    retry_after = task_state.get("retry_after")
    if not isinstance(retry_after, str) or not retry_after.strip():
        return None
    try:
        retry_after_dt = datetime.fromisoformat(retry_after)
    except ValueError:
        return None
    if retry_after_dt.tzinfo is None:
        retry_after_dt = retry_after_dt.replace(tzinfo=timezone.utc)
    if retry_after_dt > _now_utc():
        return retry_after_dt.isoformat()
    return None


def save_task_state(task_key: str, pr_ids: list[str]) -> None:
    data = _load_state()
    tasks = data.get("tasks")
    if not isinstance(tasks, dict):
        tasks = {}

    now_iso = _iso_now()
    tasks[task_key] = {
        "last_synced_at": now_iso,
        "last_checked_at": now_iso,
        "last_pr_ids": sorted(set(pr_ids)),
        "last_result": "found",
        "not_found_count": 0,
        "retry_after": None,
    }
    data["tasks"] = tasks
    _save_state(data)


def save_task_not_found(task_key: str) -> None:
    data = _load_state()
    tasks = data.get("tasks")
    if not isinstance(tasks, dict):
        tasks = {}

    previous_state = tasks.get(task_key)
    normalized_previous = _task_state_with_defaults(
        previous_state if isinstance(previous_state, dict) else None
    )
    previous_count = normalized_previous.get("not_found_count", 0)
    count = previous_count if isinstance(previous_count, int) else 0
    count += 1

    retry_days = _NOT_FOUND_RETRY_DAYS[min(count - 1, len(_NOT_FOUND_RETRY_DAYS) - 1)]
    now_dt = _now_utc()
    tasks[task_key] = {
        "last_synced_at": now_dt.isoformat(),
        "last_checked_at": now_dt.isoformat(),
        "last_pr_ids": [],
        "last_result": "not_found",
        "not_found_count": count,
        "retry_after": (now_dt + timedelta(days=retry_days)).isoformat(),
    }
    data["tasks"] = tasks
    _save_state(data)


def load_project_resume_issue_id(project_key: str) -> int | None:
    data = _load_state()
    range_progress = data.get("range_progress", {})
    if not isinstance(range_progress, dict):
        return None
    project_state = range_progress.get(project_key)
    if not isinstance(project_state, dict):
        return None
    last_task_id = project_state.get("last_task_id")
    return last_task_id if isinstance(last_task_id, int) else None


def save_project_resume_issue_id(project_key: str, issue_id: int) -> None:
    data = _load_state()
    range_progress = data.get("range_progress")
    if not isinstance(range_progress, dict):
        range_progress = {}
    range_progress[project_key] = {
        "last_task_id": issue_id,
        "updated_at": _iso_now(),
    }
    data["range_progress"] = range_progress
    _save_state(data)


def clear_project_resume_issue_id(project_key: str) -> None:
    data = _load_state()
    range_progress = data.get("range_progress")
    if not isinstance(range_progress, dict):
        return
    if project_key in range_progress:
        del range_progress[project_key]
        data["range_progress"] = range_progress
        _save_state(data)
