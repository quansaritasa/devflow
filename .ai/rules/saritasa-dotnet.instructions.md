---
applyTo: "**/*.cs,**/*.vb,**/*.razor,**/*.cshtml"
---

# C# Code Style Instructions (Saritasa)

Follow Microsoft C# style standards with the following Saritasa additions.

## 1. Identifiers & Abbreviations
- Private fields do NOT start with `_` (use `private string id;`).
- Static fields do NOT start with `s_`.
- Do not use `protected`, `public`, `protected static`, or `public static` fields.
- **2-letter abbreviations**: Capitalize both (e.g., `PK`, `EF`, `userId`).
- **Shortened words**: Capitalize first letter only (e.g., `Db`, `Id`).
- **3+ letters**: Treat as a normal word (e.g., `fromBmp`, `GenerateSha1()`).

## 2. Formatting & Braces
- **Allman style**: Braces MUST be on a new line. Always use braces, even for single-line `if` statements.
- **Indentation**: 4 spaces for C# files. 2 spaces for JSON/HTML/CSS.
- **Line Length**: Max 120 characters (+/- 10).
- **Chains**: Break long LINQ/method chains onto separate lines.
- **Blank lines**: One blank line between methods, properties, and blocks.

## 3. English Spelling & Comments
- Use **US English** (`color`). No slang/jargon.
- Do NOT use contracted verbs (use `Do not` instead of `Don't`, `Cannot` instead of `Can't`).
- Comments and exception messages MUST end with a period (`.`).
- XML docs required for all `public` classes, properties, and methods.
- Inline comments: Space after `//`, start uppercase, end with period.
- Comment the "why", not the "how". No dead code.
- TODOs: `// TODO: [Initials] Description.`

## 4. Logic & Naming
- **Conditions**: Put preferred/common branch first (`true` case). Prefer early exits over nested `else`.
- **Classes**: Use singular nouns for services/controllers (`UserController`, not `UsersController`).
- **Full names**: Avoid cryptic abbreviations (`ProductCtrl`). Exceptions: `uow`, `xml`, `json`.

## 5. Directives & Async
- Place `using` directives ABOVE the namespace.
- Order: System -> Third-party -> Application.
- Namespaces must map 1:1 to folder structure.
- **Async**: Do NOT append `Async` to method names unless a sync version also exists in the class.
- Always include `CancellationToken` in async signatures.
- Use `.ConfigureAwait(false)` for NuGet packages/libraries.