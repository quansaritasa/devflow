import json
import os
from datetime import datetime, timezone
from pathlib import Path

_DEFAULT_STATE = {"max_downloaded_id": 0, "last_sync_at": None}


def _write_json_atomic(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
    os.replace(temp_path, path)


def _load_json_object(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def load_state(sync_state_path: Path, project_key: str) -> dict[str, object]:
    data = _load_json_object(sync_state_path)
    project_state = data.get(project_key, _DEFAULT_STATE)
    if not isinstance(project_state, dict):
        return dict(_DEFAULT_STATE)

    max_downloaded_id = project_state.get("max_downloaded_id", 0)
    try:
        max_downloaded_id = int(max_downloaded_id)
    except (TypeError, ValueError):
        max_downloaded_id = 0

    last_sync_at = project_state.get("last_sync_at")
    if last_sync_at is not None and not isinstance(last_sync_at, str):
        last_sync_at = None

    return {
        "max_downloaded_id": max_downloaded_id,
        "last_sync_at": last_sync_at,
    }


def save_state(sync_state_path: Path, project_key: str, max_id: int) -> None:
    data = _load_json_object(sync_state_path)
    data[project_key] = {
        "max_downloaded_id": max_id,
        "last_sync_at": datetime.now(timezone.utc).isoformat(),
    }
    _write_json_atomic(sync_state_path, data)


def load_not_found_ids(not_found_state_path: Path, project_key: str) -> set[int]:
    data = _load_json_object(not_found_state_path)
    raw_ids = data.get(project_key, [])
    if not isinstance(raw_ids, list):
        return set()
    return {int(value) for value in raw_ids if str(value).isdigit()}


def add_not_found_id(
    not_found_state_path: Path, project_key: str, issue_id: int
) -> None:
    data = _load_json_object(not_found_state_path)
    existing = data.get(project_key, [])
    issue_ids = (
        {int(value) for value in existing if str(value).isdigit()}
        if isinstance(existing, list)
        else set()
    )
    issue_ids.add(issue_id)
    data[project_key] = sorted(issue_ids)
    _write_json_atomic(not_found_state_path, data)
