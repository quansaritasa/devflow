# Security Best Practices (.NET / Saritasa)

Follow these OWASP/Saritasa standards for all generated or reviewed code.

## 1. SQL Injection
- Use ORMs (Entity Framework) or stored procedures.
- When raw SQL is required, use **parameterized queries only**. Never concatenate input.
- `SqlCommand`: Pass parameters via `Parameters.Add()`, not string interpolation.

## 2. Authentication & Broken Access Control
- Apply `[Authorize]` to every controller/action needing auth. Never omit it.
- Scope queries to the current user (e.g., `AND UserId = @UserId`).
- Support MFA and weak-password checks.
- Log auth failures to detect brute force/stuffing.
- Implement IDOR protection: Verify user access before returning *any* entity or file. Never expose direct resource links.
- Configure CORS securely; never use `*` in production.

## 3. Sensitive Data & Crypto
- Encrypt sensitive data at rest and use TLS in transit.
- Use strong hashing (bcrypt/PBKDF2 via `Saritasa.Tools.Misc`). NEVER use MD5 or SHA-1.
- Never log or expose sensitive data (tokens, passwords, PII) in logs, errors, or APIs.

## 4. XSS & CSRF
- Sanitize and encode user data before HTML rendering (Razor auto-encodes).
- State-changing forms must use Anti-Forgery Tokens (`[ValidateAntiForgeryToken]`).
- APIs must use SameSite cookies or token-based CSRF protection.

## 5. Misconfiguration & Dependencies
- Production disables: `<customErrors mode="off" />` (use On/RemoteOnly), `<compilation debug="true" />`, `<trace enabled="true" />`.
- Validate input before passing to external components.
- Do not roll your own crypto/auth.
- XML (pre-4.5.2): Disable DTD processing to prevent XXE.

## 6. Deserialization & Input Validation
- Validate ALL client data (forms, cookies, storage) server-side.
- Log deserialization failures. Use integrity checks (HMAC) on serialized objects.

## 7. Logging & Session
- Log logins, validation exceptions, and app errors to a central server.
- On logout, delete `ASP.NET_SessionId` cookie AND call `Session.Abandon()` to prevent fixation.
- Keep sensitive data out of HTML comments.