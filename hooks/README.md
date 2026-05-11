# hooks/

## session-start.mjs

Single Node.js script (replaces bash + cmd duplicates). Node is a hard dependency
of Claude Code on all platforms.

Triggered on SessionStart. Detects ADVPL projects + suggests next steps:

- No `.prw|.tlpp|.prx` in project root (depth <= 2) -> silent
- ADVPL files but no `.plugadvpl/index.db` -> suggests `/plugadvpl:init`
- Both exist but `status --check-stale` reports stale -> suggests reindex
- Version drift (parser/lookup_bundle_hash differ) -> suggests full ingest

Errors fail silently (exit 0) to never break user sessions.

### Why `CLAUDE_PROJECT_DIR` and not `CLAUDE_PLUGIN_ROOT`?

Per spec section 13.5, `CLAUDE_PLUGIN_ROOT` has a known bug in `SessionStart`
events. We use `CLAUDE_PROJECT_DIR` (which points at the user's project root,
exactly what we want to scan) with `process.cwd()` as a fallback.

### Smoke test

```bash
# Silent on a directory with no ADVPL files
node hooks/session-start.mjs < /dev/null

# Should emit additionalContext suggesting /plugadvpl:init
mkdir -p /tmp/fakeproject && touch /tmp/fakeproject/X.prw
CLAUDE_PROJECT_DIR=/tmp/fakeproject node hooks/session-start.mjs < /dev/null
```
