# Keywords Sync Prompt

Use this prompt to generate `dev/config/keywords.md`.

---

## 1. Config

- Output file: `dev/config/keywords.md`
- Template file: `.local/keywords-sync/keywords-template.md`
- Task files:
  - `dev/tasks/*/task.json`
  - `dev/tasks/*/raw.md`

- Allowed groups:
  - `product-area`
  - `domain-entity`
  - `workflow`
  - `auth-access`
  - `technical`
  - `ui-ux`
  - `integration`
  - `environment`
  - `issue-shape`

- Output rules:
  - output markdown only
  - output final file content only
  - no explanation
  - no analysis
  - no JSON
  - no code fences

---

## 2. Job

Generate a full `keywords.md` file from:
- task data
- template file

Read template first.
Treat template as strict output contract.

Scan tasks.
Find repeated:
- product areas
- business entities
- workflows
- auth and access topics
- technical topics
- UI/UX topics
- integrations
- environments and release terms
- issue shapes

Build one clean keyword taxonomy.

---

## 3. Rules

- keep exact section order from template
- keep exact field names:
  - `canonical`
  - `group`
  - `aliases`
  - `related`
- use only allowed groups
- use canonical kebab-case
- canonical values must be unique
- aliases must be inline lists
- related must be inline lists
- use `aliases: []` when none
- use `related: []` when none
- related values must point to real canonical keywords in same final file

---

## 4. Pick good keywords

- prefer repeated concepts across many tasks
- merge obvious synonyms
- use stable words
- keep keywords reusable
- better few strong keywords than many weak ones
- avoid one-off ticket wording unless it clearly repeats

Avoid weak canonicals like:
- `system`
- `page`
- `data`
- `process`
- `item`
- `record`
- `service`
- `module`

Avoid broad aliases like:
- `api`
- `user`
- `review`
- `sync`
- `admin`
- `error`

Only keep broad alias if clearly safe for this project.

---

## 5. How to read source

Use all useful signals from tasks:
- summary
- description
- comments
- components
- labels
- issue type
- repeated raw markdown phrases

Cluster similar phrases.
Normalize to one canonical keyword.
Add aliases from real task wording.
Add related links only when relation is useful.

---

## 6. Process

1. read template
2. scan all task files
3. collect repeated phrases and concepts
4. cluster synonyms
5. choose canonical keywords
6. assign one allowed group to each keyword
7. add precise aliases
8. add valid related links
9. output final markdown only

---

## 7. Quality bar

Final file must:
- match template format exactly
- be usable by index tool
- be parser-safe
- be compact
- be useful for related-task matching

Now generate the final contents of `dev/config/keywords.md`.
