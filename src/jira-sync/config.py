import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = (
    BASE_DIR.parent.parent if BASE_DIR.parent.name == ".local" else BASE_DIR.parent
)
CONFIG_PATH = BASE_DIR / "config.json"

load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class AppConfig:
    download_path: Path
    sync_state_path: Path
    not_found_state_path: Path
    template_paths: list[Path]
    custom_fields: dict[str, str]
    pending_tasks_path: Path
    pr_template_path: Path
    github_repo: str


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Config root must be an object: {path}")
    return data


def _resolve_repo_path(value: str, key: str) -> Path:
    if not value.strip():
        raise ValueError(f"Config value '{key}' must be a non-empty string")
    resolved = (REPO_ROOT / value).resolve()
    try:
        resolved.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise ValueError(
            f"Config value '{key}' must stay within the repository root: {value}"
        ) from exc
    return resolved


def load_app_config(config_path: Path = CONFIG_PATH) -> AppConfig:
    raw = _load_json(config_path)

    custom_fields = raw.get("custom_fields")
    if not isinstance(custom_fields, dict):
        raise ValueError("Config value 'custom_fields' must be an object")

    template_paths_raw = raw.get("template_paths")
    if not isinstance(template_paths_raw, list):
        raise ValueError("Config value 'template_paths' must be a list")

    github_repo_from_config = str(raw.get("github_repo", "")).strip()

    return AppConfig(
        download_path=_resolve_repo_path(
            str(raw.get("download_path", "")), "download_path"
        ),
        sync_state_path=_resolve_repo_path(
            str(raw.get("sync_state_path", "")), "sync_state_path"
        ),
        not_found_state_path=_resolve_repo_path(
            str(raw.get("not_found_state_path", "")), "not_found_state_path"
        ),
        template_paths=[
            _resolve_repo_path(str(item), "template_paths")
            for item in template_paths_raw
            if str(item).strip()
        ],
        custom_fields={
            str(key).strip(): str(value).strip()
            for key, value in custom_fields.items()
            if str(key).strip() and str(value).strip()
        },
        pending_tasks_path=_resolve_repo_path(
            str(
                raw.get("pending_tasks_path", "")
                or ".local/jira-sync/result/tasks-pending.txt"
            ),
            "pending_tasks_path",
        ),
        pr_template_path=_resolve_repo_path(
            str(raw.get("pr_template_path", "")), "pr_template_path"
        ),
        github_repo=github_repo_from_config,
    )


APP_CONFIG = load_app_config()

JIRA_URL = os.getenv("JIRA_URL", "").rstrip("/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "")

AUTH = (JIRA_EMAIL, JIRA_API_TOKEN)
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}
HTTP_TIMEOUT_SECONDS = float(os.getenv("HTTP_TIMEOUT_SECONDS", "30"))

if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY]):
    raise EnvironmentError(
        "Missing required env vars. Check .env file:"
        "  JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY"
    )

DOWNLOAD_PATH = str(APP_CONFIG.download_path)
DOWNLOAD_PATH_REL = APP_CONFIG.download_path.relative_to(REPO_ROOT).as_posix()
SYNC_STATE_PATH = APP_CONFIG.sync_state_path
NOT_FOUND_STATE_PATH = APP_CONFIG.not_found_state_path
TEMPLATE_PATHS = APP_CONFIG.template_paths
PENDING_TASKS_PATH = APP_CONFIG.pending_tasks_path
PR_TEMPLATE_PATH = APP_CONFIG.pr_template_path
STORY_POINTS_FIELD = APP_CONFIG.custom_fields.get("story_points", "")
SPRINT_FIELD = APP_CONFIG.custom_fields.get("sprint", "")
TAGS_FIELD = APP_CONFIG.custom_fields.get("tags", "")

GITHUB_REPO = os.getenv("GITHUB_REPO", "") or APP_CONFIG.github_repo

JIRA_FIELDS = [
    "summary",
    "priority",
    "components",
    "description",
    "status",
    "issuetype",
    "comment",
    "issuelinks",
    "parent",
    "subtasks",
    "assignee",
    "reporter",
    "created",
    "updated",
    "duedate",
    "resolution",
    "resolutiondate",
    "labels",
    "fixVersions",
    "attachment",
    "timetracking",
    *[
        field_name
        for field_name in [
            STORY_POINTS_FIELD,
            SPRINT_FIELD,
            TAGS_FIELD,
        ]
        if field_name
    ],
]


def validate_project_key(project_key: str) -> None:
    """Raise ValueError if project_key does not match the configured JIRA_PROJECT_KEY."""
    if project_key != JIRA_PROJECT_KEY:
        raise ValueError(
            f"Project key '{project_key}' does not match configured"
            f" project '{JIRA_PROJECT_KEY}'. Only tasks in"
            f" '{JIRA_PROJECT_KEY}' can be downloaded."
        )
