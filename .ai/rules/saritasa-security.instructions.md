# Security Best Practices (.NET / Saritasa)

These instructions define security standards based on OWASP Top Ten and internal guidelines. Follow these rules when generating, reviewing, or suggesting any code.

---

## 1. SQL Injection Prevention

- Always use an **ORM** (e.g., Entity Framework) or **stored procedures** to interact with the database.
- When raw SQL is unavoidable, use **parameterized queries only**. Never concatenate user input into SQL strings.
- When using `SqlCommand`, always pass query parameters via `Parameters.Add()`, never via string interpolation or concatenation.

**BAD:**
```csharp
command.CommandText = "SELECT * FROM Users WHERE name = '" + userName + "'";
```

**GOOD:**
```csharp
command.CommandText = "SELECT * FROM Users WHERE name = @name";
command.Parameters.Add("@name", SqlDbType.NVarChar).Value = userName;
```

---

## 2. Authentication

- Support and encourage **multi-factor authentication (MFA)**.
- Implement **weak-password checks** on registration and password reset.
- Log all authentication failures and alert administrators when brute force, credential stuffing, or dictionary attacks are detected.
- Use a **server-side session manager** that generates a new random, high-entropy session ID after login.
- Use **CAPTCHA** where appropriate to prevent automated attacks.
- Never use default administrative account credentials.

---

## 3. Sensitive Data Exposure

- **Encrypt** all sensitive data at rest (passwords, credit card numbers, SSNs, etc.).
- Always use **TLS** for data in transit.
- Use **strong hashing algorithms**. Do NOT use MD5 or SHA-128/SHA-1 for sensitive data.
- For password hashing, use `Saritasa.Tools.Misc` or equivalent strong bcrypt/PBKDF2-based library.
- Never log or expose sensitive data (tokens, passwords, PII) in logs, error messages, or API responses.

---

## 4. XML External Entities (XXE)

- If targeting **.NET 4.5.2 or higher**, the default XML parser is safe against XXE by default.
- For older versions, explicitly disable DTD processing and external entity resolution in XML parsers.

---

## 5. Broken Access Control

- Apply the `[Authorize]` attribute to every controller or action that requires authentication. Never omit it by mistake.
- When querying user-related data, always scope queries to the current user:
```sql
  AND UserId = @UserId
```
- Configure **CORS** to allow only specific, explicitly whitelisted domains. Never use wildcard (`*`) origins in production.
- Implement **Insecure Direct Object Reference (IDOR)** protection: never expose direct file or resource links. Always verify user access for every entity or file request before returning it.

---

## 6. Security Misconfiguration

- Ensure the following are **disabled in production**:
  - `<customErrors mode="off" />` → must be set to `On` or `RemoteOnly`
  - `<compilation debug="true" />` → must be `false`
  - `<trace enabled="true" />` → must be `false`
- Never use default passwords for any service, database, or admin account.
- Use well-known, tested framework features and libraries for security — do not roll your own cryptography or auth.
- Keep all server software, the .NET framework, and dependencies up to date with the latest security patches.

---

## 7. Cross-Site Scripting (XSS)

- Sanitize and encode all user-supplied data before rendering it in HTML (Reflected, Stored, and DOM XSS).
- Follow the [OWASP XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html).
- Use framework-level output encoding wherever available (e.g., Razor auto-encodes by default).

---

## 8. Insecure Deserialization

- Log all deserialization exceptions and failures.
- Monitor deserialization activity; alert if a user deserializes data at an abnormally high rate.
- Where possible, run deserialization code in **low-privilege environments** (use Code Access Security / sandboxing).
- Implement **integrity checks** (e.g., digital signatures or HMACs) on serialized objects to detect tampering before deserialization.

---

## 9. Vulnerable Dependencies

- Always **validate input** before passing data to third-party libraries or external components.
- Regularly check for and apply **updates** to all libraries and frameworks.
- Add **security wrappers** around external components where appropriate.
- Keep the **.NET framework updated** with the latest security patches.
- Use tools like SonarQube or dependency scanners to identify known vulnerabilities in packages.

---

## 10. Logging and Monitoring

- Log the following at minimum:
  - User login attempts (success and failure).
  - Validation exceptions.
  - Application errors.
- Send logs to a **central log server**. Do not store logs locally only.
- Set up **monitoring and alerting** so that suspicious activity is detected and acted upon in a timely manner.

---

## 11. CSRF (Cross-Site Request Forgery)

- All state-changing forms must include **Anti-Forgery Tokens**.
- Use the `[ValidateAntiForgeryToken]` attribute on all POST/PUT/DELETE controller actions.
- For APIs, use SameSite cookie policies and/or token-based CSRF protection.

---

## 12. IDOR (Insecure Direct Object References)

- Never expose direct links to files or database records as static resources.
- Always verify the requesting user's access rights **for every entity or file request**, not just at login.
- Use server-side handlers (e.g., a controller or HTTP handler) to serve protected resources after an access check.

---

## 13. HTML Comments and Hidden Pages

- Do not store sensitive information (credentials, internal paths, logic) in **HTML comments** that are visible through browser source view. Use server-side-only comments instead.
- All administrative or hidden pages must be properly **authorized** and not publicly accessible.

---

## 14. Input Validation

- Validate **all** data that originates from the client side before processing:
  - Form postbacks
  - Cookies
  - Local storage
  - IndexedDB
- Never trust client-supplied data without server-side validation.

---

## 15. Session Fixation

- On **logout**, explicitly delete the `ASP.NET_SessionId` cookie from the user's browser in addition to calling `Session.Abandon()` / `Session.Clear()`.
- Failure to remove the session cookie can allow session hijacking via XSS even after the user has logged out.

```csharp
// On logout
Session.Abandon();
Response.Cookies.Append("ASP.NET_SessionId", "", new CookieOptions
{
    Expires = DateTimeOffset.UtcNow.AddDays(-1)
});
```