---
applyTo: "**/*.cs,**/*.vb,**/*.razor,**/*.cshtml"
---

# C# Code Style Instructions (Saritasa Guidelines)

These instructions define the C# code style standards to follow when generating, reviewing, or suggesting code. The overall style follows Microsoft code style standards with the additions below.

---

## 1. Identifiers

- Private field names do NOT start with `_`. Use `private string id;` not `private string _id;`.
- Static fields do NOT start with `s_`. Use `public static string DefaultName = "Unknown";` not `public static string s_DefaultName = "Unknown";`.
- Do not use `protected`, `public`, `protected static`, or `public static` fields.
- Keep identifier declarations near their usage.

---

## 2. Abbreviations

- **Two-letter abbreviations**: capitalize both letters (e.g., `PK` for Primary Key, `EF` for Entity Framework). Use as: `formI9PK`, `scanPK`, `tableId`, `userId`.
- **Single shortened words**: capitalize first letter only (e.g., `Db` for Database, `Id` for Identifier).
- **Three or more letters**: treat like a normal word (e.g., `fromBmp`, `toBmp`, `newPdf`, `GenerateSha1()`).
- Common abbreviated words: `id`, `DB`, `doc`, etc.

---

## 3. Braces

- All braces MUST be on a new line (Allman style).

**GOOD:**
```csharp
if (someVariable)
{
}
else
{
}
```

**BAD:**
```csharp
if (someVariable) {
} else {
}
```

- Always use braces even if the body after `if` is a single simple expression.

---

## 4. Spaces and Indentation

- Use **4 spaces** for indentation (not tabs) in C# files.
- Use **2 spaces** for JSON, XAML, HTML, CSS, etc.
- Keep a space after operators, keywords, literals, and commas.
- For long chain calls, break each chained call onto its own line:

```csharp
ProductPackageID = packages
    .FirstOrDefault()
    .Upgrades
    .Where(u => u.ProductClass == ProductClass.TrafficSchool)
    .Select(u => u.ProductPackageID)
    .FirstOrDefault() ?? -1;
```

---

## 5. Line Length and Organization

- Maximum recommended line length is **120 characters** (+/- 10).
- Use blank lines to separate code into logical blocks.
- Have only **one blank line** between different code blocks, methods, classes, structs, properties, and field declarations.

---

## 6. English Spelling

- Use **US English** spelling (e.g., `color` not `colour`).
- Use simple, clear English. Avoid slang, jargon, and long sentences.
- Do not use contracted verb forms in comments or messages. Prefer:
  - `Do not` over `Don't`
  - `Does not` over `Doesn't`
  - `Would not` over `Wouldn't`
  - `Could not` over `Couldn't`
  - `Have not` over `Haven't`
  - `Has not` over `Hasn't`
  - `Cannot` over `Can't`
  - `It is` over `It's`
- Comments and exception messages must **end with a period (`.`)**.

---

## 7. XML Documentation Comments

- All `public` classes, properties, and methods **must** have XML doc comments.
- Summary comments must begin with an uppercase letter and end with a period.
- Put a space after `//` for inline comments.
- Write comments in **English only**.
- Inline comments must begin with an uppercase letter and end with a period.

**GOOD:**
```csharp
/// <summary>
/// Manages the list of suspension remote URLs using cache.
/// </summary>
public class SuspensionUrlList
{
    // Send confirm email.
}
```

- Comment the **"why"**, not the "how". Prefer self-explanatory code by extracting meaningful small methods.
- Do not leave dead (commented-out) code.
- Mark incomplete/TODO code with your initials:
```csharp
// TODO: [XX] Description of what needs refactoring.
```

---

## 8. Conditions

- Put the **preferred or most common** branch first (usually the `true` case).
- Prefer **early exits** over nested else blocks:

**GOOD:**
```csharp
if (condition)
{
    return "true";
}
return "false";
```

**BAD:**
```csharp
if (condition)
{
    return "true";
}
else
{
    return "false";
}
```

---

## 9. Naming Conventions

- Use the **singular form** for services, factories, controllers, and similar classes.
  - Prefer `UserController` over `UsersController`.
  - Prefer `ProductService` over `ProductsService`.
- Use the **full entity name** — avoid cryptic abbreviations like `ProductCtrl` or `UsrSrv`.
- Exceptions: well-known abbreviations like `uow` (unit of work), `xml`, `json`.

---

## 10. Using Directives

- Always place `using` directives **above** the namespace declaration.
- Order: system usings first, then package/third-party usings, then application usings.
- Namespaces should map one-to-one to the file system folder structure (with exceptions for extension classes and special cases).

---

## 11. Asynchronous Code

- Do **not** add the `Async` suffix to asynchronous method names. Exception: when both a synchronous and an asynchronous version exist in the same class.
- Always include **cancellation tokens** in asynchronous method signatures.
- Add `.ConfigureAwait(false)` to all `await` calls when writing NuGet packages or libraries that may be consumed by desktop applications.