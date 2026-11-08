---
name: bench-opener
description: Build the Turn 1 session opener for a new Antigravity session so the agent starts task-first without a recap. Use when opening a fresh session, when the user types /bench-opener, or when a session keeps starting with preamble.
---

# Bench Opener — Turn 1 text

Produces one message the user pastes as the first message of a new session. The
opener fixes project, task, first step, deliverable, and tools in one line.

## Steps

1. Gather five fields. Infer from the open project when possible; ask only for
   what cannot be inferred, in one combined question:
   - **project** — short name
   - **task** — what this session must finish
   - **first_step** — the very first concrete action
   - **deliverable** — the artifact produced when done
   - **tools** — tools expected to be used
2. Emit exactly this shape, one paragraph, no bullet list:

   ```
   <project> on the bench. Task: <task>. First step: <first_step>. Deliverable: <deliverable>. Tools: <tools>. Re-anchor: bench.
   ```

3. Say in one line: paste this as the first message of the new session.

## Rules for the fields

- `task` names an outcome, not an activity: "merge split APKs into one standalone"
  not "look at the APKs".
- `first_step` is a command or a file to open — something executable now.
- `deliverable` is a file or artifact name, not "an analysis".
- `tools` lists only tools that exist in the environment. Never list a tool the
  project does not have installed.

The bundled helper prints the same line from flags:

```bash
python scripts/bench_install.py --opener-only --project demo --task "audit" \
  --first-step "run tests" --deliverable "audit report" --tools "shell, pytest"
```
