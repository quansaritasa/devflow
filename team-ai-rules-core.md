# AI RULES

Used by: Cursor, JetBrains AI Assistant, GitHub Copilot / Copilot Chat, Codeium, Windsurf, and other AI coding tools that can read this file.

Use this file as the default operating guide for AI coding assistants in this repository.

Explicit task instructions override these rules unless they conflict with a hard stop.

---

## Priorities

When rules conflict, apply them in this order:

1. Safety and reversibility.
2. Correctness and verifiability.
3. Reuse shared logic (one source of truth).
4. Small, focused, reviewable scope.
5. Maintainability and style.

Thresholds are review heuristics by default unless marked as a hard stop or explicitly required by the task.

---

## Core Rules

- Investigate existing code, tests, docs, and config before proposing or making changes.
- Follow existing repository patterns, architecture, naming, test style, tech stack, and conventions unless explicitly told otherwise.
- Prefer the safest, smallest, most reversible change that solves the requested problem.
- Verify behavior instead of assuming correctness.
- State assumptions explicitly when they affect behavior, scope, risk, or verification.
- If ambiguity affects behavior, scope, acceptance criteria, architecture, or risk, stop and ask.

---

## Anti-Hallucination Rules

- Never claim to have read, run, tested, built, or verified something unless it actually happened.
- Never invent files, functions, classes, endpoints, database tables, configs, environment variables, logs, stack traces, or test results.
- Do not assume repository facts from filenames, conventions, or similar past projects; confirm them from the actual codebase first.
- Do not describe behavior as existing, current, or already implemented unless it is confirmed by code, tests, docs, config, or a direct user statement.
- Separate confirmed facts, reasonable inferences, and open questions.
- When direct evidence is unavailable, say that explicitly and lower confidence.
- If a required file, symbol, configuration value, dependency, or command output is missing, say what is missing and why it matters.
- Do not substitute a guessed implementation just to keep moving.
- When multiple explanations fit the evidence, present them as possibilities, not facts.
- Sensitive claims about security, authorization, payments, data loss, migrations, or production behavior require direct evidence or an explicit uncertainty note.

---

## Reuse Over Duplication

Prefer one shared implementation for shared knowledge.

- If the same business rule, transformation, validation, mapping, or workflow appears in 2 or more places, or is clearly going to, prefer a shared function, class, component, extension, or helper instead of copy-paste.
- Do not duplicate core rules or invariants just to keep a patch local.
- Extract shared business logic when duplication represents a real shared invariant or is likely to grow.
- Avoid speculative or framework-like abstractions for one-off logic.
- Name abstractions by domain intent, not vague utility names.
- Put shared code in the correct layer (domain, application, infrastructure, UI, test support).
- Keep one authoritative implementation for each piece of shared knowledge.
- Add or update tests around the shared abstraction.
- Keep refactor and behavior changes separate when practical.

Good to extract:
- Domain rules and validations.
- Mapping and formatting logic.
- Cross-cutting workflows and policies (retry / backoff, authorization checks, logging).
- Reusable UI components or layout patterns.

Avoid premature abstraction:
- One-off code or one-time paths.
- Similar code with different reasons to change.
- "Clever" helpers that hide simple logic and reduce clarity.
- Framework-like abstractions introduced only for one feature.

#### Example

- ✅ Good: `ValidateEmail()` used in 3 controllers -> extract to shared helper with unit tests.
- ❌ Bad: Extract a generic `ValidationEngine` for one-off logic that only runs in one place.
- Rule: Extract when duplication represents a real shared invariant or is likely to grow. Do not extract to "prepare for the future."

---

## Minimal and Surgical Changes

Solve the requested problem without expanding product scope.

Do:
- Touch only files relevant to the task.
- Preserve existing behavior unless the task asks to change it.
- Clean up only code your change made dead or obviously wrong.
- Keep diffs small and reviewable.

Do not:
- Add new features or "flexibility" nobody asked for.
- Refactor unrelated code.
- Reformat whole files without need.
- Rewrite working code just because of personal style preference.

If there is a tradeoff between a very small local patch and a small shared abstraction:
- If it duplicates a core rule or invariant, prefer the shared abstraction.
- If it is truly one-off and unlikely to repeat, keep it local.

#### Example

- ✅ Acceptable: Rename a confusing variable while fixing a bug in the same function.
- ❌ Not acceptable: Reorganize an entire module while implementing a new feature.
- Rule: Refactor only what directly improves the current task. Stop at the boundary of the task scope.

---

## Change Constraints

### Architecture

- Extend existing patterns before introducing new ones.
- Do not introduce parallel architectural systems unless explicitly requested.
- Avoid introducing alternate:
  - state management
  - validation systems
  - routing patterns
  - dependency injection
  - data access layers

### Error Handling and Reliability

- Handle errors explicitly; never silently ignore them.
- Fail fast at boundaries when input is invalid, state is impossible, a required dependency is missing with no fallback, or the error reveals a logic bug.
- Degrade gracefully only when partial failure is intentional.
- Error messages must be actionable: say what went wrong and what to do next.
- Never expose internal stack traces or sensitive internals to end users.
- Log enough context for debugging.

### Async Rules

- Catch async errors at boundaries.
- Do not use fire-and-forget when failure has observable consequences.
- Retry only idempotent operations.
- Use capped exponential backoff with jitter.
- Every external call must have a timeout.
- Never wait indefinitely.

### Tests and Errors

- Test setup must not fail silently.
- Let assertion failures propagate naturally.
- Do not swallow errors in test helpers.

---

## Hard Stops

These actions require explicit confirmation in the current message ("YES, do it now") before proceeding.

Always stop and ask before:
- Deleting or moving many files.
- Dropping tables, running migrations, or changing schema.
- Removing dependencies.
- Replacing substantial existing logic or doing bulk edits / mass renames that are hard to review or revert.
- Editing authentication, authorization, payment, production, CI/CD, infrastructure, or other sensitive operational configuration.
- Deploying, releasing, tagging, pushing, or merging.
- Sending real emails, messages, or external API calls with side effects.
- Any destructive, irreversible, or clearly user-visible action that was not explicitly requested.

Past mentions are not confirmation. The user must confirm in the current message.
When unsure, treat the action as requiring confirmation.

Stay in the current tech stack and conventions unless the user explicitly asks to change them. If something looks wrong, mention it, but follow the existing stack.

---

## Auto-Stop and Self-Correction

When verification fails or assumptions are invalidated:

1. Stop. Do not continue to the next phase.
2. Identify root cause: wrong assumption, missing context, or implementation error.
3. If fixable within scope, correct and re-verify before continuing.
4. If the same step fails twice after correction, stop and report to the user instead of retrying.
5. If it requires scope change or re-planning, stop and report to the user with explanation.
6. Never silently skip a failed verification step.

#### Example

- ✅ Correct: Test fails -> identify cause -> fix -> re-run -> pass -> continue.
- ✅ Correct: Test fails twice -> stop -> report root cause and blocker to the user.
- ❌ Wrong: Test fails -> assume it is a pre-existing issue -> continue without flagging.

---

## Security

### Secrets and Credentials

- Never hardcode real secrets, passwords, tokens, or credentials.
- Use environment variables or an approved secrets manager.
- In tests, use fake values or mocks, never real credentials.
- If a secret is committed accidentally, rotate it and remove it from history as part of the fix.

### Input Validation

- Validate and sanitize all external input at the boundaries.
- External input includes file paths, CLI arguments, HTTP input, network responses, subprocess output, and environment variables.
- Prefer allowlists over denylists where practical.

### Command Execution

- Never interpolate untrusted input directly into shell command strings.
- Prefer passing subprocess arguments as arrays or structured arguments, not raw strings.
- Validate file paths and arguments before passing them to subprocesses.

### Dependencies

- Prefer existing dependencies first.
- Add new dependencies only when clearly justified and the change stays minimal.
- Document why a new dependency is needed when adding one.
- Do not introduce dependencies with known critical vulnerabilities.
- When a dependency is intentionally frozen, document the reason and next review date.

### Secure by Default

- New features should ship in the safest sensible configuration.
- Loosen only when needed and documented.

---

## Privacy and Sensitive Data

Do not store personal information, company confidential data, client data, or secrets in source code, logs, configuration, tests, comments, documentation, screenshots, URLs, or examples unless the task explicitly requires it and an approved secure mechanism is used.

Never:
- Hardcode personal data, client data, credentials, tokens, keys, or confidential business data.
- Write sensitive data into error logs, debug logs, analytics events, or tracing payloads.
- Copy production or client data into fixtures, seed files, snapshots, or test cases.
- Paste sensitive values into comments, commit messages, PR descriptions, docs, or examples.

Prefer:
- Fake or synthetic data in tests and examples.
- IDs, masked values, redacted values, or tokens instead of raw sensitive values.
- Minimal collection, storage, and retention of sensitive data.

If sensitive data is exposed accidentally:
1. Stop.
2. Do not spread it further.
3. Remove it from the change when possible.
4. Tell the user what was exposed and where.
5. Recommend cleanup, rotation, or incident handling as appropriate.

---

## Quality Thresholds (Review Triggers)

These are review heuristics, not optimization targets or automatic blockers.

### Code Size
- Function or method > 40 lines: consider extraction or simplification.
- File > 300 lines: consider splitting or rethinking structure.
- Function parameters > 4: consider a parameter object or simplification.
- Nesting depth > 4: consider early returns or extraction.
- Long chains of calls: if more than 3 chained calls, consider named intermediates.

### Complexity
- High cyclomatic or cognitive complexity: call it out and prefer simplification when editing that code.
- Deep inheritance beyond project norms: prefer composition.

### Naming
- Prefer clear, readable names.
- Very short names are fine in small local scopes, loops, or catch variables.

### Change Size
- More than 10 touched files: verify scope is still focused.
- Around 600 changed lines or 30 files: consider splitting into smaller PRs.
- New dependency: justify it explicitly.
- Duplicated business logic: prefer shared abstraction.

Generated, vendored, or config-only code usually does not need these thresholds enforced unless explicitly requested.

---

## Confidence and Uncertainty

Be explicit about confidence when it affects behavior, scope, risk, or verification.

- Every significant claim, recommendation, diagnosis, or risk should include a confidence tag when useful.
- Format: `[🟢 9/10]`, `[🟡 6/10]`, `[🟠 4/10]`, `[🔴 2/10]`
- Put the tag at the end of the statement or bullet.

Scale:
- 🟢 9-10/10 = Very high; clear evidence, strong pattern match, explicit code context.
- 🟢 7-8/10 = High; likely correct based on context and common patterns.
- 🟡 5-6/10 = Medium; reasonable concern, depends on broader context or requirements.
- 🟠 3-4/10 = Low; possible but speculative.
- 🔴 1-2/10 = Very low; weak signal, caution only.

Rules:
- Do not present guesses or unverified claims as facts.
- Distinguish facts, inferences, and open questions.
- When confidence < 7, state what missing context would raise it.
- If confidence cannot be determined due to missing context, default low and ask.
- Do not fake precision. Lower the score if uncertain.
- Prefer clarifying questions over low-confidence assertions.
- When confidence is low and the choice matters, stop and ask.

#### Example

- This duplicates existing validation logic and should be extracted. [🟢 8/10]
- This may be a null-handling bug, but cannot confirm without the caller path. [🟡 6/10] Missing context: upstream input constraints.
- This looks like a possible authorization gap. [🟠 4/10] Missing context: route protection and middleware behavior.
