# jira-bulk-pull

Bulk import all Jira issues for a project into `dev/tasks/`. Skips completed + indexed tasks. Overwrites everything else.

## Usage

```
jira-bulk-pull RMASUP
```

```
jira-bulk-pull "project = RMASUP AND assignee = currentUser()"
```

```
bulk import all tasks from RMASUP
```

### Fetch by key range

```
jira-bulk-pull "project = RMASUP AND issuekey >= RMASUP-1 AND issuekey <= RMASUP-100 ORDER BY issuekey ASC"
```

## Skip logic

| Local files exist | In index | Jira status category | Action |
|---|---|---|---|
| No | — | — | Pull + write |
| Yes | No | — | Overwrite |
| Yes | Yes | not done | Overwrite |
| Yes | Yes | done | **Skip** |

## Output

```
Bulk import complete.
  Total found : N
  Skipped     : X  (completed + already indexed)
  Written     : Y  (new)
  Overwritten : Z  (existed but not done or not indexed)
```

## Dependencies

- Requires Saritasa Atlassian MCP connected
- Reads templates from `dev/templates/` (falls back to skill-local `templates/`)
- Follows same processing rules as `jira-task-pull` for each issue
