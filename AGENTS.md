---
Used by Cursor, JetBrains AI Assistant, GitHub Copilot, Copilot Chat, Codeium, Windsurf, and similar AI coding tools.
Use this file as the default operating guide for AI assistants in this repository.
Explicit task instructions override these rules unless they conflict with a hard stop.
---

> If `.ai/startup.md` exists, read it before starting work.

# AI RULES

## Priority Order

1. Safety and reversibility
2. Correctness and verification
3. Reuse shared logic
4. Small, reviewable changes
5. Maintainability and style

## Core Rules

- Follow existing repository patterns and architecture unless explicitly instructed otherwise.
- Prefer the safest, smallest, most reversible change.
- Reuse shared business logic instead of duplicating it.
- Keep one authoritative implementation for each business rule or workflow.
- Verify behavior instead of assuming correctness.
- Ask when ambiguity affects behavior, scope, architecture, or risk.
- Thresholds are review heuristics, not optimization targets or automatic blockers.
- Do not refactor solely to satisfy heuristics.

---

## 1. Core Principles

- Investigate existing code, tests, docs, and config before coding.
- Follow existing patterns before introducing new ones.
- State important assumptions explicitly.
- If ambiguity changes behavior or multiple valid implementations exist, ask.

---

## 2. Task Workflow

### Clarify

- Convert requests into checkable goals.
- Break work into logical groups.
- Define verification steps for each phase.

### Plan

- Work incrementally and verify each logical group before continuing.
- Extract shared business logic when duplication represents a real shared invariant or is likely to grow.
- Avoid speculative or framework-like abstractions for one-off logic.
- Stop and ask if:
  - assumptions fail
  - requirements conflict
  - verification fails
  - complexity expands significantly

### Implement

- Touch only relevant files.
- Preserve existing behavior unless the task requests change.
- Avoid unrelated refactors, features, or broad reformatting.
- Small related refactors are acceptable when they directly improve correctness, reuse, maintainability, or verification.

#### Reuse vs. Speculative Abstraction

- ✅ Good: `ValidateEmail()` used in 3 controllers → extract to shared helper with unit tests.
- ❌ Bad: Extract a generic `ValidationEngine` for one-off logic that only runs in one place.
- Rule: Extract when duplication represents a real shared invariant or is likely to grow. Do not extract to "prepare for the future."

#### Small Refactor Boundary

- ✅ Acceptable: Rename a confusing variable while fixing a bug in the same function.
- ❌ Not acceptable: Reorganize an entire module while implementing a new feature.
- Rule: Refactor only what directly improves the current task. Stop at the boundary of the task scope.

### Verify

- Run relevant tests, builds, linters, or checks.
- Prefer the smallest verification proving behavior.
- Prefer deterministic tests.
- If full verification is too expensive, explain what was run and why.
- "Verified" means: tests pass, behavior matches intent, no regressions in affected paths.
- Do not mark a step as verified if only partial checks were run without explanation.

### Report

- Summarize using this format:

  ### What changed
  - [grouped by logical feature area, not file list]

  ### What was verified
  - [tests run, checks passed]

  ### What was NOT verified
  - [explain why]

  ### Remaining assumptions, risks, or follow-ups
  - [list or "none"]

---

## 3. Change Constraints

### Architecture

- Extend existing patterns before introducing new ones.
- Do not introduce parallel architectural systems unless explicitly requested.
- Avoid introducing alternate:
  - state management
  - validation systems
  - routing patterns
  - dependency injection
  - data access layers

### Errors and Reliability

- Handle errors explicitly.
- Fail fast on invalid state, invalid input, or missing required dependencies.
- Degrade gracefully only when partial failure is intentional.
- Error messages must be actionable.
- Never expose sensitive internals to end users.
- Log enough context for debugging.

#### Async Rules

- Catch async errors at boundaries.
- Do not use fire-and-forget when failures matter.
- Retry only idempotent operations.
- Use capped exponential backoff with jitter.
- Every external call must have a timeout.

---

## 4. Safety Rules

### Hard Stops

Require explicit confirmation in the current message before proceeding with:

- destructive or irreversible actions
- migrations or schema changes
- bulk edits or mass renames
- deleting or moving many files
- editing auth, payments, CI/CD, infra, or production config
- deployments, releases, merges, or pushes
- external side effects: emails, messages, API calls

When unsure, stop and ask.

### Security

- Never hardcode secrets, credentials, or tokens.
- Use approved secret management.
- Validate and sanitize external input.
- Prefer structured subprocess arguments over raw shell strings.
- Prefer existing dependencies first.
- Add dependencies only when justified and minimal.
- Do not introduce dependencies with known critical vulnerabilities.

### Privacy

- Never expose or store sensitive user, company, client, or production data in:
  - source code, logs, tests, fixtures, comments, docs, screenshots, or examples.
- Prefer fake or synthetic data, masked or redacted values, minimal data retention.
- If sensitive data is exposed:
  1. Stop.
  2. Avoid spreading it further.
  3. Remove it when possible.
  4. Notify the user.
  5. Recommend cleanup or credential rotation.

---

## 5. Quality Heuristics

These are review triggers, not automatic blockers.

### Complexity

- Function > 40 lines → consider extraction
- File > 300 lines → consider splitting
- Parameters > 4 → consider simplification
- Nesting depth > 4 → consider flattening
- Long call chains → consider intermediates
- High cognitive complexity → prefer simplification
- Deep inheritance → prefer composition when editing

#### Borderline Example

- A 45-line function with clear single responsibility and no nesting: **do not extract** — threshold is a trigger for review, not a rule.
- A 35-line function with 5 nesting levels and 3 responsibilities: **extract** — complexity matters more than line count.

### Naming

- Prefer clear, readable names.
- Short names are acceptable in small local scopes.

### Change Size

- More than 10 touched files → verify scope remains focused.
- 600 changed lines or 30 files → consider splitting PRs.
- New dependencies → justify explicitly.
- Duplicated business logic → prefer shared abstraction.
- Generated, vendored, lockfile, or config-only changes usually do not require these thresholds unless explicitly requested.

---

## 6. Confidence and Uncertainty

- Every significant claim, recommendation, diagnosis, or risk must include a confidence tag.
- Format: `[🟢 9/10]`, `[🟡 6/10]`, `[🟠 4/10]`, `[🔴 2/10]`
- Put the tag at the end of the statement or bullet.
- Scale:
  - 🟢 9-10/10 = Very high; clear evidence, strong pattern match, explicit code context.
  - 🟢 7-8/10 = High; likely correct based on context and common patterns.
  - 🟡 5-6/10 = Medium; reasonable concern, depends on broader context or requirements.
  - 🟠 3-4/10 = Low; possible but speculative.
  - 🔴 1-2/10 = Very low; weak signal, caution only.
- When confidence < 7, state what missing context would raise it.
- If confidence cannot be determined due to missing context, default to [🟠 3/10] and ask.
- Do not fake precision. Lower the score if uncertain.
- Prefer clarifying questions over low-confidence assertions.
- Never present a significant finding without a confidence tag.

#### Example Output

- This duplicates existing validation logic and should be extracted. [🟢 8/10]
- This may be a null-handling bug, but cannot confirm without the caller path. [🟡 6/10] Missing context: upstream input constraints.
- This looks like a possible authorization gap. [🟠 4/10] Missing context: route protection and middleware behavior.

---

## 7. Self-Correction

When verification fails or assumptions are invalidated:

1. **Stop.** Do not continue to the next phase.
2. **Identify root cause:** wrong assumption, missing context, or implementation error.
3. **If fixable within scope:** correct and re-verify before continuing.
4. **If the same step fails twice after correction:** stop and report to the user instead of retrying.
5. **If requires scope change or re-planning:** stop and report to user with explanation.
6. **Never silently skip a failed verification step.**

#### Example

- ✅ Correct: Test fails → identify cause → fix → re-run → pass → continue.
- ✅ Correct: Test fails twice → stop → report root cause and blocker to user.
- ❌ Wrong: Test fails → assume pre-existing issue → continue without flagging.