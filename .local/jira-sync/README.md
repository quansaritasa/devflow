# jira-sync

Download Jira issues into a configured local task folder as LLM-friendly task files.

## Configuration

Runtime settings live in:

- `.local/jira-sync/config.json`

Environment secrets and connection settings live in:

- `.local/jira-sync/.env`

## Config file

Example `config.json` keys:

```/dev/null/config.json#L1-16
{
  "download_path": "dev/tasks",
  "sync_state_path": ".local/jira-sync/sync-state.json",
  "template_paths": [
    ".local/jira-sync/templates/raw-template.md",
    "dev/templates/raw-template.md"
  ],
  "custom_fields": {
    "epic_link": "customfield_xxxxx",
    "epic_name": "customfield_xxxxx",
    "story_points": "customfield_xxxxx",
    "sprint": "customfield_xxxxx"
  }
}
```

You can change paths and Jira custom field IDs there without editing Python source.

## Env file

A placeholder `.local/jira-sync/.env` file is checked into this worktree. Replace the placeholder values with your local Jira connection settings before running the sync.

```/dev/null/.env#L1-5
JIRA_URL=https://your-org.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=replace-with-your-jira-api-token
JIRA_PROJECT_KEY=YOURPROJECT
HTTP_TIMEOUT_SECONDS=30
```

## Usage

### Resume or range sync

```/dev/null/usage.txt#L1-4
python main.py
python main.py --force
python main.py --start 100
python main.py --force --start 100
```

### Download a single task

If you pass a positional target and do not pass `--start`, the script downloads only that one issue.

```/dev/null/single-task.txt#L1-4
python main.py YOURPROJECT-2100
python main.py 2100
python main.py --force YOURPROJECT-2100
python main.py --force 2100
```

Behavior:

- `YOURPROJECT-2100` uses the project key from the provided issue key
- `2100` uses `JIRA_PROJECT_KEY` from `.local/jira-sync/.env`
- single-task mode writes `raw.md` and `task.json`
- single-task mode does not advance resume sync state

## Output

The script writes:

- `[KEY]/raw.md` files under the configured `download_path`
- `[KEY]/task.json` files under the configured `download_path`
- sync state at the configured `sync_state_path`

## Features

- Resumes from the last successful issue ID using the configured sync state file.
- Skips deleted or missing issue numbers automatically.
- Reuses `.local/jira-sync/not-found.json` to avoid re-fetching issue IDs already known to be missing and prints a skip message instead.
- Uses Jira Cloud `POST /rest/api/3/search/jql` for max issue lookup.
- Writes rich `raw.md` task files.
- Writes structured `task.json` files.
- Includes estimated and spent time from Jira timetracking.
- Supports configurable Jira custom fields for epic link, epic name, story points, and sprint.

## raw.md contents

Each task includes:

- status, type, priority
- estimated time and spent time
- assignee, reporter, components, labels, fix versions
- created/updated/due/resolution fields
- epic, sprint, parent, story points, subtasks
- related tasks
- attachments
- technical signals
- acceptance clues
- description and comments

## task.json contents

Each task also includes a structured JSON representation with fields such as:

- task key and summary
- estimated and spent time
- status, type, priority
- assignee, reporter, labels, components, fix versions
- epic, sprint, parent, subtasks
- related tasks
- attachments
- comments
- local file paths for `raw.md` and `task.json`

## Notes

- The app is intentionally task-scoped and does not write aggregate index files.
- Best practice: keep rich human-readable content in `raw.md` and structured task metadata in `task.json`.
