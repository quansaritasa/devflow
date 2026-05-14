---
name: jira-task-pull
description: Pull Jira issue into dev/tasks/[KEY]/, write task.md and raw.md using external templates, then update JSONL index for search. Trigger with "dev-intake ABC-123", "task/pull ABC-123", or paste a Saritasa Jira URL.
triggers:
  - "jira-task-pull"
  - "jira/pull"
  - "task/pull"
  - "import jira"
  - "import task"
  - "import ticket"
  - "pull jira"
  - "pull task"
  - "pull ticket"  
---

## Paths
<!-- Change these if team moves folders -->
- TASKS_DIR: `dev/tasks`
- TEMPLATES_DIR: `dev/templates`
- KEYWORDS_FILE: `dev/keywords.md`
- INDEX_DIR: `dev/tasks/index`
- TASK_TEMPLATE: `dev/templates/task.md` → fallback `templates/task.md` (next to SKILL)
- RAW_TEMPLATE: `dev/templates/raw.md` → fallback `templates/raw.md` (next to SKILL)

---

## When to use

Trigger on:
- `jira-task-pull ABC-123` ← primary command
- `task/pull ABC-123` ← legacy alias
- "pull jira", "import jira", "pull ticket", "import ticket"
- Jira URL from `https://saritasa.atlassian.net/...` + request to import

## 1. Parse Jira key

- Word after `jira-task-pull` or `task/pull` = key.
- Else find first match of `[A-Z][A-Z0-9_]+-\d+` in user text.
- Not found → ask "Give Jira key like ABC-123." Stop.

## 2. Get cloudId

- Call Atlassian resource list.
- Pick entry where `url == "https://saritasa.atlassian.net"`. Use its `id`.
- Not found → tell human "Saritasa Atlassian not connected." Stop.

## 3. Fetch Jira issue

Call `getJiraIssue`:
- `cloudId`: from step 2
- `issueIdOrKey`: key
- `fields`: `["summary", "priority", "components", "description", "status", "issuetype", "issuelinks", "comment"]`
- `responseContentFormat`: `"markdown"`

Fail → show real error. Stop.

Extract:
- `summary` = `fields.summary`
- `priority` = `fields.priority.name` or null
- `components` = `fields.components[].name` list
- `status` = `fields.status.name` or null
- `issuetype` = `fields.issuetype.name` or null
- `description` = `fields.description` (markdown) or null
- `issuelinks` = `fields.issuelinks[]` — extract `.outwardIssue.key` and `.inwardIssue.key` from each entry (skip nulls)
- `comments` = `fields.comment.comments[]` — extract `.author.displayName`, `.created` (ISO date), `.body` (markdown) from each entry; empty array if none

## 4. Check existing files

Check:
- `TASKS_DIR/[KEY]/task.md`
- `TASKS_DIR/[KEY]/raw.md`

One/both exist → tell human which. Ask "Overwrite [KEY] task files? (yes/no)". No → stop.

## 5. Ensure folder

Create `TASKS_DIR/[KEY]/` if not exists. All paths relative to repo root.

## 6. Write task.md

- Resolve TASK_TEMPLATE: check `TEMPLATES_DIR/task.md` first. Fallback: `templates/task.md` next to SKILL.
- Read template. Replace placeholders. Write to `TASKS_DIR/[KEY]/task.md`.

Placeholders:
- `[TASK_KEY]` — Jira key
- `[TASK_TITLE]` — summary
- `[PRIORITY]` — priority or `None`
- `[COMPONENT]` — components joined by `, ` or `None`
- `[RELATED_ISSUES]` — render as:
  ```
  ## Related Issues

  - KEY — summary _(link type, status)_
  - KEY — summary _(link type, status)_
  ```
  Omit entire section (including heading) if no related tasks.

Free-text sections — infer from Jira description:

**Objective** — one sentence. Outcome for user/system, not implementation detail.

**Constraints** — 2-3 bullets. Pull from: related tickets, tech stack signals, business/deployment rules. Gap → `[Constraint - not clear from ticket, fill manually]`.

**Acceptance Criteria** — use "Acceptance criteria" section in description if exists. Else derive 2-3 testable outcomes from problem. Each needs ≥1 happy-path + ≥1 edge/error test case.

**Open Questions** — 2-3 questions on scope, edge cases, related tickets, unknowns. Leave answers blank.

Rule: infer, never invent. Truly no info → `[Not enough info in ticket - fill manually]`.

## 7. Write raw.md

- Resolve RAW_TEMPLATE: check `TEMPLATES_DIR/raw.md` first. Fallback: `templates/raw.md` next to SKILL.
- Read template. Replace placeholders. Write to `TASKS_DIR/[KEY]/raw.md`.

Placeholders:
- `[KEY]` — Jira key
- `[TITLE]` — summary
- `[STATUS]` — status or `Unknown`
- `[ISSUETYPE]` — issuetype or `Unknown`
- `[PRIORITY]` — priority or `None`
- `[COMPONENTS]` — components joined by `, ` or `None`
- `[RELATED_ISSUES]` — same format as task.md: render as `## Related Issues` section with one bullet per linked issue. Omit entire section if no related tasks.
- `[DESCRIPTION]` — full Jira description verbatim markdown, or `_(no description)_`
- `[COMMENTS]` — each comment rendered as:
  ```
  **Author Name** — YYYY-MM-DD
  > comment body (verbatim markdown)
  ```
  Multiple comments separated by blank line. No comments → `_(no comments)_`.

Never summarize description or comments. Dump verbatim.

## 8. Compute metadata

### Primary component

- Components not empty → pick main one as `primary_component` (where main behavior change happens). Rest → `related_components`.
- No components → guess only if obvious from description. Else `primary_component = null`, `related_components = []`.

### Keywords

- Open KEYWORDS_FILE if exists → use as priority source. Pick only keywords matching Jira summary + description. No invented keywords unless no match.
- Not found → extract from summary + description directly. Use domain words, component names, feature names.

**Hard cap: 5 keywords max** (2-3 for tiny task). Lower-case kebab-case.
Rank by specificity — most domain-specific first. If more than 5 match, take top 5, discard rest.
Avoid generic: `fix`, `update`, `bug`, `change`, `page`, `component`, `task`. No duplicates.

### Related tasks

- Extract keys from `issuelinks` (Step 3): both `outwardIssue.key` and `inwardIssue.key`. Add to list.
- Scan description for Jira key patterns `[A-Z]+-\d+`. Add to list (deduplicate).
- Scan each comment body for Jira key patterns `[A-Z]+-\d+`. Add to list (deduplicate). Skip the issue's own key.
- Optionally check `INDEX_DIR/by-component/*.json` + `INDEX_DIR/by-keyword/*.json` for tasks sharing `primary_component` + ≥1 keyword.
- Max 5.

## 9. Update JSONL index

Index lives in `INDEX_DIR/`. Files: `manifest.json`, `shards/*.jsonl`, `by-component/*.json`, `by-keyword/*.json`.

### Shard

Numeric = digits from key (e.g. `PROJ-1234` → 1234).
- `rangeStart = floor(n / 1000) * 1000`
- `rangeEnd = rangeStart + 999`
- Path: `INDEX_DIR/shards/[rangeStart]-[rangeEnd].jsonl`

Create if missing.

### JSONL record

Append one JSON line:

```json
{"jira":"PROJ-1234","title":"Add inline reply","status":"todo","primary_component":"inbox","related_components":["settings"],"keywords":["inbox","inline-reply","oauth"],"updated_at":"2026-05-08T10:00:00+07:00","paths":{"task":"dev/tasks/PROJ-1234/task.md","raw":"dev/tasks/PROJ-1234/raw.md"},"related_tasks":["PROJ-1198"]}
```

Same `jira` key appears multiple times → keep record with latest `updated_at`.

### manifest.json

Ensure shard entry: `id`, `path`, `jira_min`, `jira_max`, `task_count`.
New shard → add entry. Always increment `task_count`, update `generated_at`.

### Secondary indexes

By component — `INDEX_DIR/by-component/[primary_component].json`:
```json
{"component":"inbox","tasks":["PROJ-1234"]}
```
Append key if not present. Create if missing.

By keyword — `INDEX_DIR/by-keyword/[keyword].json`:
```json
{"keyword":"oauth","tasks":["PROJ-1234"]}
```
Append key if not present. Create if missing.

## 10. Report

Short summary after done:
- Files written: task.md + raw.md paths
- Header fields: ID, Title, Priority, Component
- Counts: Constraints, AC items, Open Questions
- Index: primary_component, keywords, related_tasks
- Next: review task.md, answer Open Questions, adjust text
- Remind: raw.md = full Jira source

## Global rules

- Never change template shape from inside skill. Team edits templates only.
- Infer from Jira. Never invent business rules.
- Always ask before overwriting task.md or raw.md.
- JSONL index = metadata only. No markdown content.
- All `dev/` paths relative to repo root.
- No commit, no push. Local edits only.
