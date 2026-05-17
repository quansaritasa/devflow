import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("JIRA_URL", "https://example.atlassian.net")
os.environ.setdefault("JIRA_EMAIL", "test@example.com")
os.environ.setdefault("JIRA_API_TOKEN", "dummy-token")
os.environ.setdefault("JIRA_PROJECT_KEY", "APP")

from config import REPO_ROOT, load_app_config
from main import main
from persistence import write_raw_md, write_task_json
from sync_state import add_not_found_id, load_not_found_ids, load_state, save_state
from writer import build_task_json_record, render_raw_md


class ConfigTests(unittest.TestCase):
    def test_load_app_config_rejects_paths_outside_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "download_path": "../outside",
                        "sync_state_path": ".local/jira-sync/sync-state.json",
                        "not_found_state_path": ".local/jira-sync/not-found.json",
                        "template_paths": [
                            ".local/jira-sync/templates/raw-template.md"
                        ],
                        "custom_fields": {},
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError, "must stay within the repository root"
            ):
                load_app_config(config_path)

    def test_load_app_config_accepts_repo_relative_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "download_path": "dev/tasks",
                        "sync_state_path": ".local/jira-sync/sync-state.json",
                        "not_found_state_path": ".local/jira-sync/not-found.json",
                        "template_paths": [
                            ".local/jira-sync/templates/raw-template.md"
                        ],
                        "custom_fields": {"epic_link": "customfield_1"},
                    }
                ),
                encoding="utf-8",
            )

            app_config = load_app_config(config_path)

            self.assertEqual(
                app_config.download_path, (REPO_ROOT / "dev/tasks").resolve()
            )
            self.assertEqual(
                app_config.sync_state_path,
                (REPO_ROOT / ".local/jira-sync/sync-state.json").resolve(),
            )


class SyncStateTests(unittest.TestCase):
    def test_load_state_returns_defaults_for_missing_or_invalid_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "sync-state.json"

            self.assertEqual(
                load_state(state_path, "APP"),
                {"max_downloaded_id": 0, "last_sync_at": None},
            )

            state_path.write_text(
                '{"APP": {"max_downloaded_id": "bad", "last_sync_at": 123}}',
                encoding="utf-8",
            )

            self.assertEqual(
                load_state(state_path, "APP"),
                {"max_downloaded_id": 0, "last_sync_at": None},
            )

    def test_save_state_creates_parent_directory_and_persists_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "nested" / "sync-state.json"

            save_state(state_path, "APP", 42)

            self.assertTrue(state_path.exists())
            loaded = load_state(state_path, "APP")
            self.assertEqual(loaded["max_downloaded_id"], 42)
            self.assertIsInstance(loaded["last_sync_at"], str)

    def test_not_found_ids_are_deduplicated_and_sorted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            not_found_path = Path(temp_dir) / "nested" / "tasks-not-found.txt"

            add_not_found_id(not_found_path, "APP", 7)
            add_not_found_id(not_found_path, "APP", 3)
            add_not_found_id(not_found_path, "APP", 7)

            ids = load_not_found_ids(not_found_path, "APP")
            self.assertEqual(ids, {"APP-7", "APP-3"})
            content = not_found_path.read_text(encoding="utf-8")
            self.assertIn("APP-3", content)
            self.assertIn("APP-7", content)


class WriterTests(unittest.TestCase):
    def _sample_issue(self) -> dict[str, object]:
        return {
            "key": "APP-123",
            "fields": {
                "summary": "Add invoice sync endpoint",
                "status": {"name": "In Progress"},
                "issuetype": {"name": "Story"},
                "priority": {"name": "High"},
                "assignee": {"displayName": "Alice"},
                "reporter": {"displayName": "Bob"},
                "components": [{"name": "Billing"}],
                "labels": ["backend", "api"],
                "fixVersions": [{"name": "1.2.0"}],
                "created": "2024-01-02T10:00:00.000+0000",
                "updated": "2024-01-03T11:30:00.000+0000",
                "duedate": "2024-01-10",
                "resolution": None,
                "resolutiondate": None,
                "timetracking": {
                    "originalEstimateSeconds": 7200,
                    "timeSpentSeconds": 1800,
                },
                "comment": {
                    "comments": [
                        {
                            "author": {"displayName": "Carol"},
                            "created": "2024-01-04T08:15:00.000+0000",
                            "body": "Please verify APP-77 before release.",
                        }
                    ]
                },
                "issuelinks": [
                    {
                        "type": {"outward": "blocks"},
                        "outwardIssue": {
                            "key": "APP-77",
                            "fields": {
                                "summary": "Prepare release notes",
                                "status": {"name": "To Do"},
                                "issuetype": {"name": "Task"},
                            },
                        },
                    }
                ],
                "parent": {
                    "key": "APP-10",
                    "fields": {
                        "summary": "Invoice improvements epic",
                        "issuetype": {"name": "Epic"},
                        "status": {"name": "In Progress"},
                    },
                },
                "subtasks": [
                    {
                        "key": "APP-124",
                        "fields": {
                            "summary": "Add API client",
                            "status": {"name": "Done"},
                            "issuetype": {"name": "Sub-task"},
                        },
                    }
                ],
                "description": "Implement API endpoint and coordinate with APP-88.",
            },
            "renderedFields": {
                "description": "<p>Implement API endpoint and coordinate with APP-88.</p>",
                "comment": {
                    "comments": [
                        {"body": "<p>Please verify APP-77 before release.</p>"}
                    ]
                },
            },
        }

    def test_build_task_json_record_contains_structured_fields(self) -> None:
        record = build_task_json_record(
            self._sample_issue(), download_path_rel="dev/tasks"
        )

        self.assertEqual(record["task_key"], "APP-123")
        self.assertEqual(record["estimated"], "2h")
        self.assertEqual(record["spent"], "30m")
        self.assertEqual(record["components"], ["Billing"])
        self.assertEqual(record["labels"], ["backend", "api"])
        self.assertEqual(record["paths"]["task_json"], "dev/tasks/APP-123/task.json")
        self.assertEqual(record["subtasks"][0]["key"], "APP-124")
        self.assertEqual(record["comments"][0]["author"], "Carol")

    def test_render_raw_md_includes_key_sections(self) -> None:
        content = render_raw_md(self._sample_issue())

        self.assertIn("# APP-123 — Add invoice sync endpoint", content)
        self.assertIn("## Related Tasks", content)
        self.assertIn("APP-77", content)
        self.assertIn("## Comments", content)
        self.assertIn("Carol", content)


class MainTests(unittest.TestCase):
    def test_main_skips_known_missing_issue_without_fetching_jira(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            config_path = repo_root / "config.json"
            download_path = repo_root / "dev" / "tasks"
            sync_state_path = repo_root / ".local" / "jira-sync" / "sync-state.json"
            not_found_state_path = repo_root / ".local" / "jira-sync" / "not-found.json"

            config_path.write_text(
                json.dumps(
                    {
                        "download_path": "dev/tasks",
                        "sync_state_path": ".local/jira-sync/sync-state.json",
                        "not_found_state_path": ".local/jira-sync/not-found.json",
                        "template_paths": [
                            ".local/jira-sync/templates/raw-template.md"
                        ],
                        "custom_fields": {},
                    }
                ),
                encoding="utf-8",
            )
            download_path.mkdir(parents=True, exist_ok=True)
            add_not_found_id(not_found_state_path, "APP", 3)

            stdout = io.StringIO()
            with (
                patch(
                    "sys.argv",
                    ["main.py", "--config", str(config_path), "--start", "1"],
                ),
                patch("main.get_max_issue_id", return_value=3),
                patch("sync_runner.fetch_issue") as fetch_issue_mock,
                patch("main.load_not_found_ids", return_value={"APP-3"}),
                redirect_stdout(stdout),
            ):
                main()

            output = stdout.getvalue()
            self.assertEqual(fetch_issue_mock.call_count, 2)
            self.assertIn("APP-3: known missing - skip", output)
            self.assertIn("Not found:   1", output)


class PersistenceTests(unittest.TestCase):
    def _sample_issue(self) -> dict[str, object]:
        return {
            "key": "APP-200",
            "fields": {
                "summary": "Persist generated files",
                "status": {"name": "To Do"},
                "issuetype": {"name": "Task"},
                "priority": {"name": "Medium"},
                "assignee": None,
                "reporter": {"displayName": "Bob"},
                "components": [],
                "labels": [],
                "fixVersions": [],
                "created": "2024-02-01T10:00:00.000+0000",
                "updated": "2024-02-01T10:00:00.000+0000",
                "duedate": None,
                "resolution": None,
                "resolutiondate": None,
                "timetracking": {},
                "comment": {"comments": []},
                "issuelinks": [],
                "subtasks": [],
                "description": "Write files to disk.",
            },
            "renderedFields": {
                "description": "<p>Write files to disk.</p>",
                "comment": {"comments": []},
            },
        }

    def test_write_task_json_creates_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = write_task_json(
                self._sample_issue(),
                download_path=temp_dir,
                download_path_rel="dev/tasks",
            )
            path = Path(temp_dir) / "APP-200" / "task.json"

            self.assertEqual(result, "created")
            self.assertTrue(path.exists())
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["task_key"], "APP-200")
            self.assertEqual(data["paths"]["raw"], "dev/tasks/APP-200/raw.md")

    def test_write_raw_md_creates_markdown_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = write_raw_md(self._sample_issue(), download_path=temp_dir)
            path = Path(temp_dir) / "APP-200" / "raw.md"

            self.assertEqual(result, "created")
            self.assertTrue(path.exists())
            content = path.read_text(encoding="utf-8")
            self.assertIn("# APP-200 — Persist generated files", content)


if __name__ == "__main__":
    unittest.main()
