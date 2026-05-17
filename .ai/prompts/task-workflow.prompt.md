# AI Coding Workflow

Use this prompt when asked to implement a feature, fix a bug, or complete a multi-step coding task.

Follow this workflow unless the user explicitly asks for a different one.

## Task Workflow

### 1. Clarify

- Turn the request into checkable goals.
- Break work into logical groups.
- Define verification steps for each phase.
- If multiple valid interpretations remain, stop and ask instead of guessing.

### 2. Plan

- Make a short, phase-by-phase plan before coding.
- Show the plan first when the task is multi-step, high-risk, or likely to produce a broad diff.
- Group work into meaningful review slices, for example: "Data Model", "Business Logic", "API", "UI", or "Tests".
- Each phase must include a concrete check such as a test, build, lint, or command.

### 3. Implement

- Work incrementally and verify one logical group before moving to the next.
- Touch only files relevant to the task.
- Preserve existing behavior unless the task explicitly asks to change it.
- Avoid unrelated refactors, broad reformatting, or extra features.
- Small related refactors are acceptable only when they directly improve correctness, reuse, maintainability, or verification.

### 4. Stop Conditions

Stop and ask if:

- an assumption fails;
- requirements conflict;
- existing code or behavior conflicts with the plan;
- a verification step fails and the correct fix is unclear;
- the requested change appears to violate an invariant, architectural boundary, or business rule;
- the implementation becomes significantly more complex or broader than planned;
- the plan requires a scope change or re-planning.

### 5. Verification

- Run the tests, builds, linters, or checks relevant to the change.
- Prefer the smallest verification that proves the requested behavior.
- If full verification is too expensive or unavailable, say what you ran, what you did not run, and why.
- For bug fixes, add or update a test when practical; if not, explain how the fix was verified.
- For behavior changes or new business logic, add or update tests when practical.
- Never mark something as verified without saying what was actually checked.
- Never pretend verification happened.

### 6. Report

Summarize using this format:

**What changed**
- Grouped by logical feature area, not file list.

**What was verified**
- Tests run, checks passed, and commands executed.

**What was not verified**
- Explain what was not verified and why.

**Remaining assumptions, risks, or follow-ups**
- List them explicitly, or say `None`.

**Evidence / uncertainty**
- List key assumptions, missing context, and any conclusions that are inferred rather than directly verified.