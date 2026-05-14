---
name: "jira-keywords-sync"
description: "Rebuild dev/keywords.md from existing index by-keyword files and task.md keyword sections. Run after jira-bulk-pull to consolidate all invented keywords into a canonical list."
triggers:
  - "jira-keywords-sync"
  - "keywords-sync"
  - "sync keywords"
  - "rebuild keywords"
  - "update keywords"
---

## Paths
- TASKS_DIR: `dev/tasks`
- KEYWORDS_FILE: `dev/keywords.md`
- INDEX_DIR: `dev/tasks/index`
- BY_KEYWORD_DIR: `dev/tasks/index/by-keyword`

---

## When to use

Trigger on:
- `jira-keywords-sync` ← primary command
- `jira-keywords-sync --min-count 1` ← include all keywords regardless of frequency
- "sync keywords", "rebuild keywords", "update keywords"

Best run **after** `jira-bulk-pull` to consolidate all keywords generated during bulk import into a canonical list that future `jira-task-pull` runs will reuse.

---

## 0. Parse options

- `--min-count N` → minimum number of tasks a keyword must appear in to be promoted to `## Uncategorized`. Default: `2`.
- `--min-count 1` → include all keywords (bypass frequency filter).

---

## 1. Collect from index (primary source)

Read `BY_KEYWORD_DIR/*.json` files:
- Each filename (without `.json` extension) = one keyword
- Read file content to get `tasks[]` array → `count = tasks.length`
- Collect into `index_keywords[]` as `{keyword, count}`

If directory missing or empty → note "No index keywords found, continuing with shard scan."

---

## 2. Collect from shards (secondary source)

Read `INDEX_DIR/shards/*.jsonl`. For each line, extract `"keywords"` array.

Build frequency map: `keyword → count` across all lines.

Merge into `index_keywords[]` — if keyword already present from step 1, use the higher count.

---

## 3. Merge + clean

Combine all collected keywords:
- Lowercase, kebab-case only (replace spaces/underscores with `-`)
- Remove generic noise: `fix`, `update`, `bug`, `change`, `page`, `component`, `task`, `feature`, `improvement`
- Deduplicate (exact match after normalization)

Produce `keyword_counts{}` map: `keyword → count`.

---

## 4. Load existing keywords.md

Read `KEYWORDS_FILE` if exists.

Parse:
- Preserve all section headers and their keywords → `existing[]`
- `is_bootstrap = existing[].length == 0` (file missing or contains only manually-written section headers with no keywords)

**Bootstrap mode:** if `is_bootstrap == true`, treat all collected keywords as qualifying regardless of `--min-count`. Reason: first run after bulk-pull has everything at count=1.

---

## 5. Apply frequency threshold

For each keyword in `keyword_counts{}` not in `existing[]`:

| Count | Threshold met? | Destination |
|---|---|---|
| ≥ min-count | Yes | `promote[]` → `## Uncategorized` |
| < min-count AND not bootstrap | No | `rare[]` → `## Rare (review before keeping)` |
| Any count AND bootstrap mode | Yes (bypass) | `promote[]` → `## Uncategorized` |

---

## 6. Confirm before writing

Show preview:

```
Keywords sync summary:
  min-count        : N  (bootstrap mode: off/on)
  Existing         : X  (unchanged)
  Found in index   : Y  (unique, after cleaning)
  To promote       : P  (count ≥ N → ## Uncategorized)
  Rare (count < N) : R  (→ ## Rare for manual review)

Promote:
  - keyword-a  (5 tasks)
  - keyword-b  (3 tasks)

Rare:
  - keyword-c  (1 task)
  - keyword-d  (1 task)

Proceed? (yes/no)
```

No → stop. Yes → continue.

---

## 7. Write updated keywords.md

**Merge mode only** — never delete existing content.

If `promote[]` and `rare[]` both empty → report "keywords.md already up to date. No changes made." Stop.

Append sections at bottom:

**If `promote[]` non-empty:**
```markdown
## Uncategorized

- keyword-a
- keyword-b
```
If `## Uncategorized` already exists → append to it (no duplicate section).

**If `rare[]` non-empty:**
```markdown
## Rare (review before keeping)

- keyword-c  <!-- 1 task -->
- keyword-d  <!-- 1 task -->
```
If `## Rare (review before keeping)` already exists → append to it.

Write updated file to `KEYWORDS_FILE`.

---

## 8. Report

```
Keywords sync complete.
  Existing  : X  (unchanged)
  Promoted  : P  (appended to ## Uncategorized)
  Rare      : R  (appended to ## Rare — review before keeping)
  File      : dev/keywords.md

Next: review dev/keywords.md
  - Move keywords to appropriate sections
  - Merge synonyms (e.g. dispatch-api + dispatch_api)
  - Delete entries from ## Rare that are too specific
  - Promote rare keywords you want to keep
Curated keywords.md = fewer new index files on future jira-task-pull runs.
```

---

## Global rules

- Never delete or overwrite existing keywords.md content.
- Never invent keywords not found in index or shard files.
- Merge only — append new keywords, preserve all existing sections and entries.
- No commit, no push. Local edits only.
- If KEYWORDS_FILE missing → create it fresh with standard header + sections.
- Bootstrap mode auto-activates when keywords.md has no keyword entries — ensures first run captures everything.
