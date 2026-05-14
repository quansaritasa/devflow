# jira-keywords-sync

Rebuild `dev/keywords.md` from existing index and task files. Run after `jira-bulk-pull` to consolidate all keywords into a canonical list.

## Usage

```
jira-keywords-sync
```

```
jira-keywords-sync --min-count 1
```

```
sync keywords
```

```
rebuild keywords
```

## Recommended workflow

```
# Step 1 — bulk import all tasks (keywords.md sparse → free invention)
jira-bulk-pull "project = RMASUP AND issuekey >= RMASUP-1 AND issuekey <= RMASUP-100 ORDER BY issuekey ASC"

# Step 2 — consolidate all invented keywords
jira-keywords-sync

# Step 3 — manually review dev/keywords.md
#   - Move keywords to appropriate sections
#   - Merge synonyms (dispatch-api vs dispatch_api)
#   - Remove noise

# Step 4 — future pulls reuse canonical keywords, no new index files spawned
jira-task-pull RMASUP-9999
```

## Options

| Option | Default | Description |
|---|---|---|
| `--min-count N` | `2` | Min tasks a keyword must appear in to be promoted |
| `--min-count 1` | — | Include all keywords (bypass frequency filter) |

**Bootstrap mode:** auto-activates when `keywords.md` has no keyword entries. Bypasses `--min-count` so first run captures everything.

## What it does

1. Reads `dev/tasks/index/by-keyword/*.json` — each filename is a keyword, file length = count
2. Scans `dev/tasks/index/shards/*.jsonl` for `"keywords"` arrays
3. Merges, deduplicates, removes generic noise
4. Keywords with count ≥ min-count → `## Uncategorized`
5. Keywords with count < min-count → `## Rare (review before keeping)`
6. Never deletes or overwrites existing content

## Output

```
Keywords sync complete.
  Existing  : 15  (unchanged)
  Promoted  : 6   (appended to ## Uncategorized)
  Rare      : 4   (appended to ## Rare — review before keeping)
  File      : dev/keywords.md
```

## Notes

- Merge only — safe to run multiple times
- Existing sections and keywords always preserved
- Review `## Rare` section — promote keepers, delete noise
- Curated `keywords.md` = fewer new index files on future `jira-task-pull` runs
