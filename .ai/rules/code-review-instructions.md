# Code Review Instructions

## Role & Priorities
Review changes as a maintainer.
Priorities: (1) Safety/Security, (2) Correctness, (3) Reuse, (4) Scope, (5) Style.

## Core Review Behavior
- Read changes in context. Do not guess; ask if behavior, scope, or risk is unclear.
- Prioritize bugs, security risks, broken contracts, and duplicated business logic.
- Be concise. Reference exact code. Group repeated issues.
- Say what is wrong, why it breaks rules, and what to do instead.
- Ignore minor style nitpicks unless they violate repository guidelines.

## Hard Stops (MUST BLOCK PR)
Block approval immediately for:
1. Bugs breaking correctness or data integrity.
2. Security holes (unvalidated input, hardcoded secrets, missing `[Authorize]` checks).
3. Business logic duplicated 3+ times instead of using a shared abstraction.
4. Destructive/irreversible changes without explicit confirmation.

## Correctness & Quality
- Identify logic bugs, unsafe assumptions, and missing edge cases.
- Flag dead code, unused parameters, hidden side effects, and over-engineering.
- Ensure error handling is explicit (no silent failures).
- Avoid premature optimization, but flag heavy operations on hot paths.

## Reuse vs. Duplication
- Flag duplicated business logic or repeated patterns. 
- If the same rule/validation appears 2+ times, demand extraction to one authoritative implementation.
- *Example:* ✅ Extract `ValidateEmail()` to a utility. ❌ Copy the same regex into 3 controllers.

## Architecture & Design
- Respect existing boundaries and separation of concerns.
- Flag tight coupling and unclear contracts. 
- Prefer composition over duplication.

## Security & Reliability
- Flag unvalidated input reaching sensitive operations (SQL, shells).
- Check authorization, data safety, and failure recovery.
- Call out patterns that may cause inconsistent state.

## Testing & Documentation
- Ensure new behavior, bug fixes, and extracted shared logic have relevant tests.
- Flag fragile tests that depend heavily on implementation details.
- Demand clearer code over explanatory comments for confusing logic.
- Call out outdated or misleading comments.