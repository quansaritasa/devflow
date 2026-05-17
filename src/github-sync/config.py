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
    task_download_path: Path
    pr_download_path: Path
    sync_state_path: Path
    template_paths: list[Path]
    default_project_key: str
    repositories: list[str]


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Config root must be an object: {path}")
    return data


def _resolve_repo_path(value: str, key: str) -> Path:
    if not value.strip():
        raise ValueError(f"Config value '{key}' must be a non-empty string")
    return (REPO_ROOT / value).resolve()


def load_app_config(config_path: Path = CONFIG_PATH) -> AppConfig:
    raw = _load_json(config_path)
    repositories_raw = raw.get("repositories", [])
    if not isinstance(repositories_raw, list):
        raise ValueError("Config value 'repositories' must be a list")

    template_paths_raw = raw.get("template_paths", [])
    if not isinstance(template_paths_raw, list):
        raise ValueError("Config value 'template_paths' must be a list")

    repositories = [str(item).strip() for item in repositories_raw if str(item).strip()]

    default_project_key = (
        str(raw.get("default_project_key", os.getenv("DEFAULT_PROJECT_KEY", "")))
        .strip()
        .upper()
    )

    return AppConfig(
        task_download_path=_resolve_repo_path(
            str(raw.get("task_download_path", "dev/tasks")), "task_download_path"
        ),
        pr_download_path=_resolve_repo_path(
            str(raw.get("pr_download_path", "dev/prs")), "pr_download_path"
        ),
        sync_state_path=_resolve_repo_path(
            str(raw.get("sync_state_path", ".local/github-sync/sync-state.json")),
            "sync_state_path",
        ),
        template_paths=[
            _resolve_repo_path(str(item), "template_paths")
            for item in template_paths_raw
            if str(item).strip()
        ],
        default_project_key=default_project_key,
        repositories=repositories,
    )


APP_CONFIG = load_app_config()

GITHUB_API_URL = os.getenv("GITHUB_API_URL", "https://api.github.com").rstrip("/")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
HTTP_TIMEOUT_SECONDS = float(os.getenv("HTTP_TIMEOUT_SECONDS", "30"))

if not GITHUB_TOKEN:
    raise EnvironmentError("Missing required env vars. Check .env file:  GITHUB_TOKEN")

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
}
TASK_DOWNLOAD_PATH = str(APP_CONFIG.task_download_path)
PR_DOWNLOAD_PATH = str(APP_CONFIG.pr_download_path)
PR_DOWNLOAD_PATH_REL = APP_CONFIG.pr_download_path.relative_to(REPO_ROOT).as_posix()
SYNC_STATE_PATH = APP_CONFIG.sync_state_path
TEMPLATE_PATHS = APP_CONFIG.template_paths
DEFAULT_PROJECT_KEY = APP_CONFIG.default_project_key
GITHUB_REPOSITORIES = APP_CONFIG.repositories
