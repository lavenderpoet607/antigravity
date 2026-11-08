# Bench Protocol

Task-first agent protocol for Antigravity. Ships six slash commands, one
always-on rule, and three offline helper scripts.

## Slash commands

| Command | What it does |
|---|---|
| `/bench` | Re-anchor on the current task and continue. Use when output drifts or gets chatty. |
| `/bench-audit` | Read the project and report what to fix first, in priority order. |
| `/bench-rules` | Install or refresh the protocol surfaces in this project + global settings. |
| `/bench-opener` | Build the Turn 1 opener for a new session. |
| `/bench-proxy` | Set up the optional injection proxy. Last resort only. |
| `/bench-doctor` | Read-only check that the setup is intact. |

## The protocol

- **Task first. Execute, ship.**
- Three limits: 1) no recap  2) no persona talk  3) no safety preamble
- Every tool call opens with `# reason: <file/fungsi/kenapa>`
- Complete artifacts only — no placeholder, no truncation
- Re-anchor word: `bench`
- Output ends with a `[Null]` ruling line, no closing summary

## Install

```bash
agy plugin validate --strict ./bench-protocol
agy plugin install ./bench-protocol
agy plugin list
```

Workspace-level alternative: copy this folder to `<project>/.agents/plugins/`.
Global level: `~/.gemini/config/plugins/`.

## Layout

```text
bench-protocol/
├── plugin.json
├── README.md
├── assets/logo.svg
├── rules/bench-protocol.md        # trigger: always_on
├── skills/
│   ├── bench/SKILL.md             # /bench
│   ├── bench-audit/SKILL.md       # /bench-audit
│   ├── bench-rules/SKILL.md       # /bench-rules
│   ├── bench-opener/SKILL.md      # /bench-opener
│   ├── bench-proxy/SKILL.md       # /bench-proxy
│   └── bench-doctor/SKILL.md      # /bench-doctor
└── scripts/
    ├── bench_install.py           # writes the surfaces
    ├── bench_doctor.py            # read-only check
    └── bench_proxy.py             # optional injector
```

## Helper scripts

All three are offline. No network calls except `bench_proxy.py`, which forwards
to the host you supply.

```bash
python scripts/bench_install.py --project . --dry-run
python scripts/bench_doctor.py --project .
python scripts/bench_proxy.py --dry-run
```

## Wording rule

The three limits string and the task-first line must be **identical** in the rule
file, `bench_install.py`, and `bench_proxy.py`. `/bench-doctor` fails if they
differ. Change all three together or not at all.

## Limits and honest caveats

- Skill bodies are capped at 24,000 bytes by the app; all six are well under.
- The proxy assumes the Gemini body shape (`systemInstruction.parts[].text`).
  Adjust `rewrite_body` if your capture differs.
- `/bench-audit` and `/bench-doctor` only report what they actually observed;
  they never guess a result.
