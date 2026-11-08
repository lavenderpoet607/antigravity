---
name: bench-audit
description: Inspect the open project and report what to fix first, in priority order. Use when starting work in an unfamiliar project, when the user asks what to do next, or types /bench-audit.
---

# Bench Audit — what to fix first

Read the project, then report. Do not change files unless the user asks after the
report.

## Steps

1. Map the project: file tree to depth 3, language/framework from manifest files,
   entry points, test setup. Read the README if present.
2. Run the existing checks that are already configured (test suite, linter,
   type checker). Do not install new tooling.
3. Look for the four usual blockers, in this order:
   - **Broken build or failing tests** — highest priority, always first.
   - **Wrong or missing dependency** — manifest and lockfile disagree.
   - **Untested entry point** — main path with no coverage.
   - **Dead or duplicated code** — same logic in more than one place.
4. Report as a table: `Priority | Finding | File | Why it matters`.
5. Give the single next action in one line.

## Limits

- No file edits during the audit.
- No new dependencies, no new config files.
- If a check cannot run (missing tool, no permission), say so in one line and move on.
- Report only what you actually observed. Never guess a test result.

End with the `[Null]` ruling line.
