# jira-sync

Download Jira issues into a configured local task folder as LLM-friendly task files.

---

## 1. Configuration

Runtime settings in `.local/jira-sync/config.json`, secrets in `.local/jira-sync/.env`.

### config.json

```json
{
  "download_path": "dev/tasks",
  "sync_state_path": ".local/jira-sync/sync-state.json",
  "not_found_state_path": ".local/jira-sync/result/tasks-not-found.txt",
  "pending_tasks_path": ".local/jira-sync/result/tasks-pending.txt",
  "template_paths": [
    ".local/jira-sync/templates/raw-template.md",
    "dev/templates/raw-template.md"
  ],
  "custom_fields": {
    "story_points": "customfield_12722",
    "sprint": "customfield_10006",
    "tags": "customfield_13351"
  }
}
```

### .env

```
JIRA_URL=https://your-org.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=YOURPROJECT
HTTP_TIMEOUT_SECONDS=30
```

### Discover custom fields

```bash
python main.py --discover       # show key fields + all others
python main.py --discover-all   # show all 85+ fields flat
```

Copy the output field IDs into `config.json` `custom_fields`.

---

## 2. Usage

### Single task

```bash
python main.py RMASUP-2100
python main.py 2100              # uses JIRA_PROJECT_KEY
python main.py --force 2100      # overwrite existing
```

Only tasks matching `JIRA_PROJECT_KEY` are allowed. Wrong-project keys are rejected.

### Range sync

```bash
python main.py                   # resume from last synced ID
python main.py --force           # force overwrite all
python main.py --start 100       # start from ID 100
```

Epics automatically fetch children via `parent=` JQL and list them as subtasks.

### Pending tasks

```bash
python main.py --get-pending     # scan dev/tasks for unresolved → tasks-pending.txt
python main.py --pending         # re-sync all pending, remove resolved ones
```

Resolved statuses: Done, Completed, Resolved, Closed, Accepted, Canceled.

---

## 3. Result files

All in `.local/jira-sync/result/`, one task key per line (`RMASUP-xxxx` format):

| File | Purpose |
|------|---------|
| `tasks-pending.txt` | Unresolved tasks for `--pending` re-sync |
| `tasks-not-found.txt` | Task IDs that don't exist -- auto-skipped |
| `tasks-not-sync.txt` | Task IDs to never sync (range + pending) |
| `tasks-force-sync.txt` | Task IDs to always force-overwrite (range only) |

---

## 4. Output

### raw.md

- Status, type, priority, timetracking, assignee, reporter
- Labels, tags (hyperlinked to Jira search), fix versions
- Dates, resolution, URL
- Epic, sprint, parent, story points (all hyperlinked)
- Subtasks (sub-list, hyperlinked, sorted ASC by summary)
- Related tasks (hyperlinked)
- Attachments
- Description and comments (plain text in ``` blocks, HTML stripped)

### task.json

Structured JSON with all fields above plus:

- `estimated_seconds`, `spent_seconds`
- `description_text` (HTML stripped)
- `comments[].body_text` (HTML stripped)
- `related_tasks` array with relation types and sources
- `tags` array (like `labels`)
- `paths.raw`, `paths.task_json`

---

## 5. Notes

- Only tasks from the configured `JIRA_PROJECT_KEY` are synced.
- Epic children are fetched via `parent=` JQL, only if `fields.subtasks` is empty.
- `story_points` field: use `Story point estimate` from `--discover`.
- `sprint` field: use `Sprint` from `--discover` (not `customfield_10020` -- that was wrong).
- Single-task mode does not advance resume sync state.