# AI Session Setup

Orchestration file for this repository.
Read this before starting any work if available.

---

## Paths

| Name | Path |
|---|---|
| Rules file | `AGENTS.md` |
| Memory file | `.ai/memory.md` |
| Agents folder | `.ai/agents/` |
| Skills folder | `.ai/skills/` |
| Sync script (macOS/Ubuntu) | `sync.sh` |
| Sync script (Windows) | `sync.ps1` |

Reuse these paths. Do not guess new ones.

---

## Start of every session

| Step | Action |
|---|---|
| 1 | Read `.ai/setup.md` (this file) |
| 2 | Read `.ai/memory.md` if it exists |
| 3 | Read `AGENTS.md` for rules |
| 4 | Keep all in mind for the whole session |

If session is long, task changes, or context is fuzzy, re-read them.

---

## When user says use an agent

| Step | Action |
|---|---|
| 1 | Go to `.ai/agents/` |
| 2 | Find best agent for the task |
| 3 | Read that agent file |
| 4 | Do task using that agent's job and limits |

If many agents fit, pick best match.
If no agent fits, say no good agent found, then continue with memory and rules only.

---

## When task needs a skill

| Step | Action |
|---|---|
| 1 | Go to `.ai/skills/` |
| 2 | Find best skill for the task |
| 3 | Read that skill file |
| 4 | Use that skill alongside memory and rules |

If many skills fit, pick best match.
If no skill fits, say no good skill found, then continue with memory and rules only.

---

## Priority order

| Priority | Source |
|---|---|
| 1 | User instruction |
| 2 | Chosen agent from `.ai/agents/` |
| 3 | Chosen skill from `.ai/skills/` |
| 4 | `AGENTS.md` rules |
| 5 | `.ai/memory.md` |
| 6 | Default AI behavior |

---

## Check before work

| Check | Required |
|---|---|
| `.ai/setup.md` was read | yes |
| `.ai/memory.md` was read (if exists) | yes |
| `AGENTS.md` was read | yes |
| `.ai/agents/` checked (if user asked for agent) | yes |
| `.ai/skills/` checked (if task needs a skill) | yes |

If not done yet, do it first.

---

## Missing files

| Rule | Detail |
|---|---|
| Missing file | Say it clearly. Do not pretend it exists. |
| Optional files | Skip gracefully if not present. |
| Required files | Stop and notify user if `AGENTS.md` or `.ai/memory.md` is missing. |

---

## Sync scripts

### macOS / Ubuntu — `sync.sh`

```bash
#!/bin/bash
mkdir -p .ai
cp AGENTS.md CLAUDE.md
cp AGENTS.md GEMINI.md
cp AGENTS.md .windsurfrules
cp AGENTS.md .codeiumrules
cp AGENTS.md CONVENTIONS.md
cp AGENTS.md .rules
cp AGENTS.md .github/copilot-instructions.md
echo "AI rules synced."
```

Make it executable and run:

```bash
chmod +x sync.sh
./sync.sh
```

### Windows — `sync.ps1`

```powershell
New-Item -ItemType Directory -Force -Path .ai | Out-Null
Copy-Item AGENTS.md CLAUDE.md
Copy-Item AGENTS.md GEMINI.md
Copy-Item AGENTS.md .windsurfrules
Copy-Item AGENTS.md .codeiumrules
Copy-Item AGENTS.md CONVENTIONS.md
Copy-Item AGENTS.md .rules
Copy-Item AGENTS.md .github\copilot-instructions.md
Write-Host "AI rules synced."
```

Run:

```powershell
.\sync.ps1
```

---

## When to sync

| Trigger | Action |
|---|---|
| After editing `AGENTS.md` | Run sync script |
| Before committing | Run sync script |
| After pulling changes to `AGENTS.md` | Run sync script |

---

## Optional: auto-sync on commit (Git hook)

```bash
# .git/hooks/pre-commit
#!/bin/bash
./sync.sh
git add CLAUDE.md GEMINI.md .windsurfrules .codeiumrules CONVENTIONS.md .rules .github/copilot-instructions.md
```

Make it executable:

```bash
chmod +x .git/hooks/pre-commit
```