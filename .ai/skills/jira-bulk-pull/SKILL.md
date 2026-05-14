---
name: "jira-bulk-pull"
description: "Bulk import all Jira issues for a project into dev/tasks/. Skips issues that are already indexed and done. Overwrites everything else."
triggers:
  - "jira-bulk-pull"
  - "bulk import"
  - "import all tasks"
  - "pull all tickets"
  - "import all jira"
---

## Paths
<!-- Same as jira-task-pull — change here if team moves folders -->
- TASKS_DIR: `dev/tasks`
- TEMPLATES_DIR: `dev/templates`
- KEYWORDS_FILE: `dev/keywords.md`
- INDEX_DIR: `dev/tasks/index`

---

## When to use

Trigger on:
- `jira-bulk-pull RMASUP` ← project key
- `jira-bulk-pull "project = RMASUP AND assignee = currentUser()"` ← raw JQL
- "bulk import", "import all tasks from project", "pull all jira tickets"

---

## 1. Parse input

- Arg is a bare word (no spaces, no `=`) → treat as project key. Build JQL: `project = [KEY] ORDER BY created DESC`
- Arg contains spaces or `=` → treat as raw JQL.
- No arg → ask "Provide a project key or JQL query." Stop.

---

## 2. Get cloudId

- Call `getAccessibleAtlassianResources`.
- Pick entry where `url == "https://saritasa.atlassian.net"`. Use its `id`.
- Not found → tell human "Saritasa Atlassian not connected." Stop.

---

## 3. Confirm before fetching

Show the resolved JQL and ask:

```
JQL : project = RMASUP ORDER BY created DESC
This will fetch all matching issues from Jira.
Cap : 200 issues max per run. Add filters to JQL to narrow scope if needed.

Proceed? (yes/no)
```

No → stop. Yes → continue.

---

## 4. Fetch all issue keys + statuses (paginated)


Call `searchJiraIssuesUsingJql` in a loop until all pages consumed:
- `cloudId`: from step 2
- `jql`: from step 1
- `fields`: `["summary", "status"]`
- `maxResults`: 100
- `nextPageToken`: omit on first call; use returned token for subsequent calls

Collect for each issue:
- `key`
- `fields.summary`
- `fields.status.name`
- `fields.status.statusCategory.key` — `"done"` means completed

Stop loop when no `nextPageToken` returned.

**Hard cap:** if total collected > 200, stop collecting and warn:
> "Found N issues — exceeds 200 limit. Narrow your JQL (e.g. add `AND assignee = currentUser()` or `AND sprint in openSprints()`) and re-run."
Stop.

---

## 5. Apply skip / overwrite logic

For each collected issue key, determine action:

**Skip** if ALL of:
1. `dev/tasks/[KEY]/task.md` exists
2. `dev/tasks/[KEY]/raw.md` exists
3. Key found in index shard (calculate shard: `n = digits from key`, `rangeStart = floor(n/1000)*1000`, read `INDEX_DIR/shards/[rangeStart]-[rangeEnd].jsonl`, scan lines for `"jira":"[KEY]"`)
4. Jira `statusCategory.key == "done"`

**Overwrite** (process) if ANY of:
- Local files missing
- Key not in index
- Jira statusCategory ≠ `"done"`

Build two lists: `to_skip[]`, `to_process[]`.

Show breakdown and ask for confirmation:

```
Found N total.
  Skip      : X  (completed + already indexed)
  Write new : Y
  Overwrite : Z  (exists but not done / not indexed)

Proceed? (yes/no)
```

No → stop. Yes → continue.

---

## 6. Process each issue

Process `to_process[]` in **batches of 25**. After each batch completes fully, print a checkpoint before starting the next:
> `Checkpoint: [batch N] done — X written, Y failed so far.`

This allows safe interruption between batches with a consistent state.

For every key in each batch:

### 6a. Fetch full issue details

Call `getJiraIssue` (fetch all 5 in batch in parallel):
- `fields`: `["summary", "priority", "components", "description", "status", "issuetype", "issuelinks", "comment"]`
- `responseContentFormat`: `"markdown"`

Fetch failure → log error for that key, skip it, continue batch.

### 6b. Write task.md and raw.md

Follow **Steps 5–7 from `jira-task-pull` SKILL.md** exactly:
- Ensure folder exists
- Write task.md using TASK_TEMPLATE — fill all placeholders including `[RELATED_ISSUES]`
- Write raw.md using RAW_TEMPLATE — fill all placeholders including `[RELATED_ISSUES]` and `[COMMENTS]`

### 6c. Compute metadata + update index IMMEDIATELY

**Do not batch index updates.** Write index entry for each issue right after writing its files — before moving to the next issue in the batch.

Follow **Steps 8–9 from `jira-task-pull` SKILL.md** exactly:
- Compute primary_component, keywords, related_tasks
- Append/update JSONL shard record (same key → replace with latest `updated_at`)
- Update manifest.json (increment task_count only for new keys, not overwrites)
- Update by-component and by-keyword secondary indexes

---

## 7. Report

Print summary when done:

```
Bulk import complete.
  Total found : N
  Skipped     : X  (completed + already indexed)
  Written     : Y  (new)
  Overwritten : Z  (existed but not done or not indexed)
```

List any errors (failed fetches, missing templates) separately.

---

## Global rules

- Never commit or push. Local edits only.
- Never delete existing task files without writing replacements first.
- Respect jira-task-pull SKILL.md rules for template shape, keyword selection, infer-don't-invent.
- If TASK_TEMPLATE or RAW_TEMPLATE missing → stop and report error before processing any issues.
- Hard cap: 200 issues per run. Require narrower JQL to go beyond.
- Index must be written atomically with task files — never defer index updates to end of run.
- Batches of 25: checkpoint after each batch so partial runs leave a consistent state.
