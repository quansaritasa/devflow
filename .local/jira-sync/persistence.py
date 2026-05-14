import json
import os

from config import DOWNLOAD_PATH, DOWNLOAD_PATH_REL
from writer import build_task_json_record, render_raw_md


def _write_text_atomic(path: str, content: str) -> None:
    temp_path = f"{path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as handle:
        handle.write(content)
    os.replace(temp_path, path)


def write_task_json(
    issue: dict[str, object],
    force: bool = False,
    download_path: str = DOWNLOAD_PATH,
    download_path_rel: str = DOWNLOAD_PATH_REL,
) -> str:
    key = str(issue.get("key", ""))
    folder = os.path.join(download_path, key)
    path = os.path.join(folder, "task.json")
    os.makedirs(folder, exist_ok=True)
    existed = os.path.exists(path)
    if existed and not force:
        return "skipped"
    content = build_task_json_record(issue, download_path_rel)
    _write_text_atomic(
        path,
        json.dumps(content, ensure_ascii=False, indent=2) + "\n",
    )
    return "overwritten" if existed else "created"


def write_raw_md(
    issue: dict[str, object], force: bool = False, download_path: str = DOWNLOAD_PATH
) -> str:
    key = str(issue.get("key", ""))
    folder = os.path.join(download_path, key)
    path = os.path.join(folder, "raw.md")
    os.makedirs(folder, exist_ok=True)
    existed = os.path.exists(path)
    if existed and not force:
        return "skipped"
    content = render_raw_md(issue)
    _write_text_atomic(path, content)
    return "overwritten" if existed else "created"
