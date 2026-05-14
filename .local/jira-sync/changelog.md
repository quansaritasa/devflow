# Changelog

## 0.1.0

### Improved
- Added configurable HTTP request timeout via `HTTP_TIMEOUT_SECONDS` in `config.py`.
- Hardened Jira max issue key parsing in `fetcher.py` using right-split validation instead of a brittle fixed index split.
- Added request timeouts to Jira search and issue fetch calls to avoid indefinite hangs.
- Made sync state loading resilient to missing, unreadable, or invalid JSON content in `sync-state.json`.
- Improved Jira text normalization in `writer.py` so rendered and structured field content is handled more consistently.
- Improved comment parsing and relation extraction to prefer rendered comment bodies when available and normalize fallback raw content.
- Improved acceptance clue extraction to work more reliably across rendered and structured Jira content.

### Notes
- No diagnostics were reported after the review before these changes.
- After the hardening edits, static diagnostics surfaced additional strict type-checking issues in existing code paths.
- Applied a first follow-up pass to fix the new generic type annotation errors in `fetcher.py`, `sync_state.py`, and key `writer.py` function signatures.
- Changes focused on reliability and runtime hardening rather than altering the output format or sync behavior.
- Next changelog entry should auto-increment from this version.
