# github-sync

Sync important GitHub pull request data for a Jira-style task key into local LLM-friendly files.

## Configuration

Runtime settings live in:

- `.local/github-sync/config.json`

Environment secrets and connection settings live in:

- `.local/github-sync/.env`

## Config file

Example `config.json` keys:

```/dev/null/config.json#L1-10
{
  "task_download_path": "dev/tasks",
  "pr_download_path": "dev/prs",
  "sync_state_path": ".local/github-sync/sync-state.json",
  "template_paths": [".local/github-sync/templates/pr-template.md"],
  "default_project_key": "",
  "repositories": []
}
```

## Env file

Fill `.env` with your GitHub connection settings:

```/dev/null/.env#L1-3
GITHUB_TOKEN=
GITHUB_API_URL=https://api.github.com
HTTP_TIMEOUT_SECONDS=30
```

## Usage

```/dev/null/usage.txt#L1-10
python main.py
python main.py PROJECT-2100
python main.py 1444
python main.py 1444-1873
python main.py 1444..1873
python main.py PROJECT-*
python main.py PROJECT-* --reset-resume
python main.py PROJECT-2100..2125
python main.py PROJECT-2100-2125
python main.py OTHER-123
python main.py --all
```

## Templates

Markdown output is generated from the first readable path in `template_paths`.

The default checked-in template is:

- `.local/github-sync/templates/pr-template.md`

The generated `pr.md` renderer supports simple placeholders like `{{ title }}`, `{{ task_key }}`, `{{ body_or_no_description }}`, `{{ labels_bullets }}`, and `{{ commits_bullets }}`.

If no configured template can be read, the app falls back to the built-in markdown renderer.

## Output

The script writes:

- `dev/prs/[task-key]/pr.md`
- `dev/prs/[task-key]/pr.json`
- `.local/github-sync/sync-state.json`

If a task has multiple matching PRs, both files accumulate all PRs for that task.

## Incremental sync

The app keeps a small sync state file per task with:

- `last_synced_at`
- `last_pr_ids`
- `last_checked_at`
- `last_result`
- `not_found_count`
- `retry_after`

On later runs, it only refetches PR details when a matching PR is new or its GitHub `updated_at` is newer than the saved sync time.

Tasks that repeatedly have no matching PRs are temporarily skipped using retry backoff.

For full project sync selectors like `PROJECT-*`, the sync state also stores per-project progress with a saved `last_task_id`. Project sync always resumes from that checkpoint automatically, so the next run starts from tasks whose numeric id is greater than `last_task_id`.

Use `--reset-resume` to clear the saved project checkpoint before syncing that project again.

`default_project_key` can also be provided by `DEFAULT_PROJECT_KEY` in `.env`, but the config value takes precedence.

## Matching strategy

The app searches across every configured repository.

Selector behavior:

- `PROJECT-2100` syncs one exact task key
- `1444` auto-expands to `[default_project_key]-1444` using `default_project_key`
- `1444-1873` auto-expands to the inclusive project range `[default_project_key]-1444..[default_project_key]-1873`
- `1444..1873` does the same as `1444-1873`
- `PROJECT-*` syncs every local task folder for that Jira project prefix
- `PROJECT-2100..2125` syncs every local task folder in that project-specific inclusive range
- `PROJECT-2100-2125` does the same as `PROJECT-2100..2125`

A PR is considered related to a task when the Jira-style task key appears in any of these fields:

- PR title
- PR body
- head branch name
- base branch name

## Saved data

The sync stores important PR context for LLM use, including:

- title, state, draft, merged, timestamps
- author, reviewers, assignees, labels
- base/head branches
- PR description/body
- commit summaries
- changed file summaries
- issue comments
- reviews
- review comments

It intentionally does **not** store diff patches.
