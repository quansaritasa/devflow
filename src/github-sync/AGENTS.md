# AI RULES

Used by: Cursor, JetBrains AI Assistant, GitHub Copilot / Copilot Chat, Codeium, Windsurf, and other LLM coding tools that can read this file.

Use this file as the default operating guide for AI coding assistants in this repository.

Explicit task instructions override these rules unless they conflict with a hard stop.

---

## Priorities

When rules conflict, apply them in this order:

1. Safety and reversibility.
2. Correctness and verifiability.
3. Reuse shared logic (one source of truth).
4. Small, focused scope.
5. Style and maintainability.

Thresholds are review triggers by default unless marked as a hard stop or explicitly required by the task.

---

## Task Protocol

Before coding:

- Say assumptions when they affect behavior or design.
- Check existing code, tests, docs, and config first.
- Ask only when behavior, scope, acceptance criteria, or risk is unclear.
- If multiple valid interpretations remain after that, stop and ask.
- Turn the request into checkable goals.
- Make a short plan; each step has a check (test, build, or command).

After coding:

- Say what changed and why.
- Say what you ran (tests, builds, commands) and the result.
- Call out any remaining assumptions, risks, or follow-ups.

---

## Reuse Over Duplication

Prefer one shared implementation for shared knowledge.

- If the same business rule, transformation, validation, mapping, or workflow appears in 2 or more places (or is clearly going to), prefer a shared function, class, component, extension, or helper instead of copy-paste.
- Do not copy-paste logic just to keep a change â€œlocalâ€.

Good to extract:

- Domain rules and validations.
- Mapping and formatting logic.
- Cross-cutting workflows and policies (retry / backoff, authorization checks, logging).
- Reusable UI components or layout patterns.

Avoid premature abstraction:

- One-off code or one-time paths.
- Similar code with different reasons to change.
- Clever utility helpers that hide simple logic and hurt readability.
- Framework-like abstractions introduced only for one feature.

Rules for extraction:

- Name abstractions by domain intent, not vague utility names.
- Put shared code in the correct layer (domain, application, infrastructure, UI, test support).
- Keep one authoritative implementation for each piece of shared knowledge.
- Add or update tests around the shared abstraction.
- Keep refactor and behavior changes as separate as practical.

If a local patch would duplicate a core rule or invariant, prefer extracting shared logic instead of repeating it.

---

## Minimal and Surgical Changes

Solve the requested problem without expanding product scope.

Do:

- Touch only files relevant to this task.
- Preserve existing behavior unless the task asks to change it.
- Clean up only code your changes made dead or obviously wrong.
- Keep diffs small and reviewable.

Do not:

- Add new features or â€œflexibilityâ€ nobody asked for.
- Refactor unrelated code.
- Reformat whole files.
- Rewrite existing code just because you prefer a different style.

If there is a tradeoff between a very small local patch and a small shared abstraction:

- If it duplicates a core rule or invariant â†’ prefer shared abstraction.
- If it is truly one-off and unlikely to repeat â†’ keep local.

---

## Hard Stops

These actions require explicit confirmation in the current message (â€œYES, do it nowâ€) before you proceed.

Always stop and ask before:

- Deleting or moving many files, dropping tables, removing dependencies, or discarding user data.
- Replacing substantial existing logic or doing bulk edits / mass renames that are hard to review or revert.
- Running migrations or schema changes.
- Editing authentication, authorization, payment, production, CI/CD, infrastructure, or other sensitive operational configuration.
- Deploying, releasing, tagging, pushing, or merging.
- Sending real emails, messages, or external API calls with side effects.
- Any irreversible or user-visible action that was not clearly requested.

Past mentions are not confirmation. The user must confirm in the current message.
When unsure, treat the action as requiring confirmation.

Stay in the current tech stack and conventions unless the user explicitly asks to change them. If something looks wrong, mention it, but follow the existing stack.

---

## Error Handling

Core rules:

- Handle errors explicitly; never silently ignore them.
- Fail fast at function or method boundaries when input is invalid, state is impossible, a required dependency is missing with no fallback, or the error reveals a logic bug.
- Degrade gracefully only when partial failure is an intentional part of the design (optional services, non-critical features, best-effort operations).
- Error messages must be actionable: say what went wrong and what to do next.
- Never expose internal stack traces or sensitive internals to end users.
- Log errors with enough context to debug.

Async and reliability:

- Catch unhandled async errors at boundaries.
- Do not use fire-and-forget when failure has observable consequences.
- Retry only idempotent operations.
- Use capped exponential backoff with jitter for retries.
- Every external call must have a timeout; never wait indefinitely.

Tests and errors:

- Test setup must not fail silently.
- Let assertion failures propagate naturally.
- Do not swallow errors in test helpers.

---

## Security

Secrets and credentials:

- Never hardcode real secrets, passwords, tokens, or credentials.
- Use environment variables or an approved secrets manager.
- In tests, use fake values or mocks, never real credentials.
- If a secret is committed accidentally, rotate it and remove it from history as part of the fix.

Input validation:

- Validate and sanitize all external input at the boundaries.
- External input includes file paths, CLI arguments, HTTP input, network responses, subprocess output, and environment variables.
- Prefer allowlists over denylists where practical.

Command execution:

- Never interpolate untrusted input directly into shell command strings.
- Prefer passing subprocess arguments as arrays or structured arguments, not raw strings.
- Validate file paths and arguments before passing them to subprocesses.

Dependencies:

- Prefer existing dependencies first.
- Add new dependencies only when clearly justified and the change stays minimal.
- Document why a new dependency is needed when adding one.
- Do not add dependencies with known critical vulnerabilities; run the appropriate audit tool first.
- When a dependency is intentionally frozen, document the reason and next review date.

Secure by default:

- New features ship in the safest sensible configuration; loosen only when needed and documented.

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

- Stop.
- Do not spread it further.
- Remove it from the change when possible.
- Tell the user what was exposed and where.
- Recommend cleanup, rotation, or incident handling as appropriate.

---

## Quality Thresholds (Review Triggers)

These are review triggers, not automatic blockers, unless tooling or the task says otherwise.

Code size:

- Function or method > 40 lines: consider extraction or simplification.
- File > 300 lines: consider splitting or rethinking structure.
- Function parameters > 4: consider a parameter object or simplification.
- Nesting depth > 4: consider early returns or extraction.
- Long chains of calls: if more than 3 chained calls, consider named intermediates.

Complexity:

- High cyclomatic or cognitive complexity: call it out and prefer simplification when editing that code.
- Deep inheritance (beyond project norms): prefer composition when touching that area.

Naming:

- Identifiers should be long enough to be clear and short enough to read easily.
- Very short names are fine for simple loop variables and catch variables.

PR and change size:

- Change touches > 10 files: make sure scope is still clear.
- PR would exceed ~600 changed lines or ~30 files: consider splitting into smaller PRs.
- New dependency: call it out and justify it.
- Shared business logic duplicated instead of reused: call it out and prefer a shared abstraction.

Generated, vendored, or config-only code (for example generated sources, vendor directories, lockfiles, basic JSON/YAML config) usually does not need these thresholds enforced unless explicitly requested.

---

## Tests and Verification

General:

- Tests are there to verify behavior, not just run lines.
- Prefer the smallest test that proves the requested behavior.

Bug fixes:

- When practical, write or update a test that reproduces the bug first, then make it pass.
- If you cannot write a test, explain how you reproduced and verified manually.

New business logic:

- Add or update unit tests for new business rules.
- For significant changes, also consider integration or end-to-end tests where appropriate.

Refactors:

- Preserve behavior.
- Keep relevant tests passing before and after.
- Do not remove tests unless they are clearly redundant or invalid; if you must, explain why.

UI copy, layout-only, config-only, or docs-only changes:

- Do not require new tests unless behavior changes.

Verification:

- Always run the tests or checks relevant to the change (unit tests, integration tests, linters, builds).
- If running a full suite is too expensive, state which subset you ran and why.

Never:

- Swallow errors in tests or test helpers.
- Pretend verification happened; be explicit.

---

## Behavior Summary

- Think before coding.
- Investigate locally before asking.
- Ask when ambiguity affects behavior, scope, or risk.
- Prefer shared abstractions over duplicated business logic.
- Keep one authoritative implementation for each shared rule.
- Keep product scope tight and changes reviewable.
- Handle errors and security explicitly.
- Protect personal, company, client, and secret data.
- Verify each meaningful step with tests or commands.
- Do not perform destructive or irreversible actions without explicit confirmation.
- Prefer the safer, smaller, more reversible change.
