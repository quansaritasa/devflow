# [JIRA-KEY] [Task Summary]

**ID:** [JIRA-KEY]
**Title:** [TASK-TITLE]
**Status:** Draft

## Plan

[One or two sentences. Overall goal of this task and the expected user/business outcome.]

---

## Scope

**In scope:**
1. [Work this task must complete.]
2. [Another explicit in-scope item.]

**Out of scope:**
1. [Work explicitly excluded from this task.]
2. [Another excluded area, refactor, or enhancement.]

**Do not modify:**
1. [Critical file, folder, artifact, API contract, or behavior that must remain unchanged.]
2. [Another protected area if applicable.]

---

## Proposed Changes

### 1. [Small meaningful feature or fix name]

- **User outcome:** [What user gets. One sentence.]
- **Why:** [Why this change exists. One sentence.]
- **Scope:** [Main component or module affected.]
- **Confidence:** [Confirmed | Likely | Needs verification]

- **Implementation**
  - `[path/to/file.ts or placeholder]` — [What changes and why. Class or method name if known.]
  - `[path/to/file.ts or placeholder]` — [What changes and why. Class or method name if known.]
  - **Verify:** [One concrete check. Proves this item is done.]

- **Test Impact**
  - **Add:** [New test needed for new logic in this change. "None" + reason if not needed.]
  - **Update:** [Existing test that breaks or needs change. "None" if not applicable.]
  - **Verify manually:** [Flow or area to verify manually or e2e for this change.]

---

### 2. [Small meaningful feature or fix name]

- **User outcome:** [What user gets. One sentence.]
- **Why:** [Why this change exists. One sentence.]
- **Scope:** [Main component or module affected.]
- **Confidence:** [Confirmed | Likely | Needs verification]

- **Implementation**
  - `[path/to/file.ts or placeholder]` — [What changes and why. Class or method name if known.]
  - **Verify:** [Concrete validation step.]

- **Test Impact**
  - **Add:** [New test. "None" + reason if not needed.]
  - **Update:** [Existing test. "None" if not applicable.]
  - **Verify manually:** [Integration area.]

---

## Done Criteria

1. [Observable condition proving the whole task is complete.]
2. [Protected areas remain unchanged.]
3. [Build, runtime, or manual verification passes.]
4. [Any task-level acceptance or parity requirement.]

---

## Risks, Constraints & Open Questions

**Constraints:**
1. [Hard constraint from task.md. Technical or business rule that must be respected.]
2. [Another rule that limits implementation choices.]

**Risks:**
1. [Risk or known limitation.]
2. [Potential regression, integration issue, or uncertainty.]

**Open Questions:**
1. [Unresolved question. Flag if it blocks implementation.]
2. [Decision that may require clarification.]

---

## Impact Related Tasks

| Source | Type | Impact (0-10) | Why |
|--------|------|----------------|-----|
| [Current repository / codebase] | Codebase | [0-10] | [How much the current codebase shaped the plan.] |
| [JIRA-KEY or task reference] | Related task | [0-10] | [Why this task is impacted or how much it informed the plan.] |
| [JIRA-KEY or task reference] | Related task | [0-10] | [Why this task is impacted or how much it informed the plan.] |

Impact guide:
- 9-10: Very impactful. Primary input to the plan, direct dependency, strong overlap, or high regression risk.
- 6-8: Meaningful impact. Shared codepath, contract, workflow, or implementation pattern likely affected.
- 3-5: Moderate relevance. Related area, useful precedent, or indirect implementation impact.
- 0-2: Noise only. Mentioned for context but contributed little to the plan.

Use this section to show what contributed most to the plan: the current codebase, related tasks, or both.

---

## Execution Order

1. [Item number and title]
2. [Item number and title]
3. [Validation / final verification]
