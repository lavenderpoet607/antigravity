---
name: bench-rules
description: Install or refresh the Bench Protocol surfaces in the current project and the global settings file. Use when setting up a new project, after an app update wiped settings, or when the user types /bench-rules.
---

# Bench Rules — install or refresh surfaces

Writes the protocol into four surfaces so an app update cannot wipe it all.

## Surfaces

| Surface | Location | Content |
|---|---|---|
| Workspace rule | `<project>/.agents/rules/bench-protocol.md` | three limits + task-first |
| Global settings | `~/.gemini/settings.json` | `rules` key pointing at the plugin rule |
| Agent note | `<project>/.agents/AGENTS.md` | one-line pointer to this plugin |
| Session opener | printed to chat | Turn 1 text for the next session |

Antigravity reads workspace rules from `AGENTS.md`, `GEMINI.md`, or
`.agents/rules/*.md`, and global rules from `~/.gemini/AGENTS.md`,
`~/.gemini/GEMINI.md`, or `~/.gemini/config/rules/*.md`. Write to
`.agents/rules/` — it is the least likely to collide with an existing file.

## Steps

1. Confirm the project root with the user if the open folder is ambiguous. One
   question, then proceed.
2. Write `<project>/.agents/rules/bench-protocol.md` with the three limits and
   task-first, in the same wording as the plugin rule. Do not paraphrase.
3. If `<project>/.agents/AGENTS.md` exists, append the pointer line only if it is
   not already there. If it does not exist, create it with the pointer line.
4. Merge `~/.gemini/settings.json` if it exists: keep every existing key, add the
   protocol keys. If it does not exist, create it. Tolerate a UTF-8 BOM — read
   with `utf-8-sig`.
5. Print the session opener for the next session.
6. Report which surfaces were written and which were skipped.

## Limits

- Never overwrite a settings file that is not valid JSON. Report it and stop that step.
- Never touch keys outside the protocol's own key namespace.
- Idempotent: running twice must produce identical files. Verify with a hash.

The bundled helper does all of this offline:

```bash
python scripts/bench_install.py --project <path> --dry-run   # preview
python scripts/bench_install.py --project <path>             # write
```
