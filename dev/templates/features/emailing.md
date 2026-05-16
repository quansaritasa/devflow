# [Feature name]

---

## [JIRA task ID]: [Task summary]

[YYYY/MM/DD]

Users can now define which subject prefixes are hidden from the inbox, replacing the previously hardcoded `[JIRA]` filter.

**Changes (2)**

- Added a "Subject Filters" card in Settings with a textarea (one prefix per line). Defaults to `[JIRA]`, `Accepted:`, `Rejected:`, and `Automatic reply:`. Filters are persisted in Supabase and applied on each inbox load. Matching is case-insensitive.

- Added a "Category Filters" card in Settings with a textarea (one prefix per line). Defaults to `Personal`, `Work` and `Misc`. Filters are persisted in Supabase and applied on each inbox load. Matching is case-insensitive.

---

## [JIRA task ID]: [Task summary]

[YYYY/MM/DD]

### Date filters for inbox

Added quick-filter buttons to narrow the inbox by time period.

**Fixes (1)**

- Added All / Today / Yesterday / This Week filter buttons below the search bar. "Today" shows emails from the last 24 h, "Yesterday" from the last 48 h, "This Week" from the last 7 days. Filters combine with the existing search query.

---

## [JIRA task ID]: [Task summary]

[YYYY/MM/DD]

Fixed the auth redirect loop that sent users back to the login page after completing Google sign-in.

**Fixes (1)**

- Added a dedicated `/auth/callback` route (`AuthCallback.tsx`) that explicitly handles both OAuth flows: PKCE (`?code=` query param via `exchangeCodeForSession`) and implicit (`#access_token=` hash fragment via `setSession`). Supabase was returning the implicit flow with tokens in the URL hash, which the previous automatic detection did not handle. Also simplified `useAuth` to rely solely on `onAuthStateChange` (Supabase v2 fires `INITIAL_SESSION` on startup, making the separate `getSession()` call redundant).

**Changes (1)**

- Clicking the "Unlinked" badge scans the email thread for a `<JiraProjectKey>-<Number>` pattern (using the project key from Settings) and saves the link immediately if found; falls back to the manual link dialog if no key is detected.
