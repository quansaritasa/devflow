# Changelog

## 0.2.0

### Added
- Epic children fetching via `parent=` JQL in range sync and single-task mode.
- `--discover` / `--discover-all` flags to find Jira custom field IDs.
- `--get-pending` to scan local tasks and build pending list.
- `--pending` to re-sync unresolved tasks, auto-remove resolved ones.
- Tags custom field (`customfield_13351`) with hyperlinks to Jira search.
- `result/tasks-pending.txt`, `result/tasks-not-found.txt`, `result/tasks-not-sync.txt`, `result/tasks-force-sync.txt` for tracking.
- Project key guard — rejects tasks from non-configured projects.
- Hyperlinks on Epic, Parent, Related Tasks, and Subtasks in raw.md.
- Subtasks now sub-listed, sorted ASC by summary.
- `story_points` and `tags` arrays in task.json.

### Changed
- Custom field IDs discovered and corrected via `--discover`:
  - `sprint`: `customfield_10020` → `customfield_10006`
  - `story_points`: `customfield_10016` → `customfield_12722`
  - `epic_link`, `epic_name` removed — replaced by `parent` field.
- Description and comments: HTML stripped, plain text in ``` blocks.
- `not-found.json` → `result/tasks-not-found.txt` (plain text, full keys).
- `pending-tasks.txt` → `result/tasks-pending.txt`.
- All result files use `RMASUP-xxxx` full-key format.
- Resolved statuses include `Canceled`.
- Functions refactored to reduce length (`build_task_relationships`, `discover_fields`, `main()`).

### Removed
- `epic_link` and `epic_name` custom fields — replaced by standard `parent` field.
- Technical Signals and Acceptance Clues sections from raw.md.

---

## 0.1.0

### Improved
- Added configurable HTTP request timeout via `HTTP_TIMEOUT_SECONDS` in `config.py`.
- Hardened Jira max issue key parsing in `fetcher.py` using right-split validation instead of a brittle fixed index split.
- Added request timeouts to Jira search and issue fetch calls to avoid indefinite hangs.
- Made sync state loading resilient to missing, unreadable, or invalid JSON content in `sync-state.json`.
- Improved Jira text normalization in `writer.py` so rendered and structured field content is handled more consistently.
- Improved comment parsing and relation extraction to prefer rendered comment bodies when available and normalize fallback raw content.
- Improved acceptance clue extraction to work more reliably across rendered and structured Jira content.

### Notes
- No diagnostics were reported after the review before these changes.
- After the hardening edits, static diagnostics surfaced additional strict type-checking issues in existing code paths.
- Applied a first follow-up pass to fix the new generic type annotation errors in `fetcher.py`, `sync_state.py`, and key `writer.py` function signatures.
- Changes focused on reliability and runtime hardening rather than altering the output format or sync behavior.
- Next changelog entry should auto-increment from this version.
