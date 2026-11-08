---
name: bench-doctor
description: Check that the Bench Protocol setup is intact — plugin installed, rule active, surfaces present, settings valid, wording consistent. Use when the protocol stops working, after an app update, or when the user types /bench-doctor.
---

# Bench Doctor — check the setup

Read-only diagnosis. Report problems and the one-line fix for each. Do not change
files unless the user asks.

## Checks

Run in order and record pass or fail:

1. **Plugin present** — the plugin folder exists and `plugin.json` parses.
2. **Plugin installed** — run the app's plugin list and confirm this plugin is
   listed and enabled. If the CLI is unavailable, say so and skip.
3. **Rule active** — the plugin rule file has frontmatter with `trigger:` set to
   `always_on`, `model_decision`, `glob`, or `manual`. A rule without a valid
   trigger never applies.
4. **Workspace surfaces** — `<project>/.agents/rules/bench-protocol.md` and the
   `AGENTS.md` pointer exist.
5. **Global settings valid** — the settings file parses as JSON. Report a BOM or
   trailing comma if found.
6. **Wording consistent** — the three limits string and the task-first line are
   identical across the plugin rule, the workspace rule, and the proxy's injected
   text. Report any surface that differs.
7. **Size limits** — each `SKILL.md` body is under 24,000 bytes and each rule file
   under 24,000 bytes. The app truncates anything larger without warning.

## Report

Table: `Check | Result | Fix`. Then one line naming the single most important fix.

The bundled helper runs checks 1, 4, 5, 6, and 7 offline:

```bash
python scripts/bench_doctor.py --project <path>
```

Exit code 0 means clean. Non-zero means at least one check failed; the output
names each one.
