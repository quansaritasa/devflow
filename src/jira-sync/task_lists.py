"""Manage task list files: pending, not-found, not-sync, force-sync."""

import json
from pathlib import Path

from config import JIRA_PROJECT_KEY, PENDING_TASKS_PATH, REPO_ROOT

RESOLVED_STATUSES = {"done", "completed", "resolved", "closed", "accepted", "canceled"}

NOT_SYNC_PATH = REPO_ROOT / ".local" / "jira-sync" / "result" / "tasks-not-sync.txt"
FORCE_SYNC_PATH = REPO_ROOT / ".local" / "jira-sync" / "result" / "tasks-force-sync.txt"


class TaskListManager:
    """Read/write pending, not-sync, and force-sync task list files."""

    def __init__(self) -> None:
        self._not_sync: set[str] | None = None
        self._force_sync: set[str] | None = None

    @property
    def not_sync(self) -> set[str]:
        if self._not_sync is None:
            self._not_sync = self._load_lines(NOT_SYNC_PATH)
        return self._not_sync

    @property
    def force_sync(self) -> set[str]:
        if self._force_sync is None:
            self._force_sync = self._load_lines(FORCE_SYNC_PATH)
        return self._force_sync

    def load_pending(self) -> list[str]:
        """Return list of pending task keys from tasks-pending.txt."""
        if not PENDING_TASKS_PATH.is_file():
            return []
        return [
            line.strip()
            for line in PENDING_TASKS_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def save_pending(self, keys: list[str]) -> None:
        """Write pending task keys to tasks-pending.txt."""
        PENDING_TASKS_PATH.parent.mkdir(parents=True, exist_ok=True)
        PENDING_TASKS_PATH.write_text("\n".join(keys) + "\n", encoding="utf-8")

    def build_pending(self, download_path: str) -> int:
        """Scan downloaded tasks for unresolved ones, write to tasks-pending.txt."""
        tasks_dir = Path(download_path)
        if not tasks_dir.is_dir():
            print(f"Download path not found: {download_path}")
            return 0

        pending: list[str] = []
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
            if task_key in self.not_sync:
                continue
            if status not in RESOLVED_STATUSES:
                pending.append(task_key)

        self.save_pending(pending)
        print(f"Wrote {len(pending)} pending tasks to tasks-pending.txt")
        return len(pending)

    @staticmethod
    def _load_lines(path: Path) -> set[str]:
        if not path.is_file():
            return set()
        return {
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
