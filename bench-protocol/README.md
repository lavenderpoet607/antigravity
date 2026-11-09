# Bench Protocol

Task-first agent protocol for Antigravity. Ships six slash commands, one
always-on rule, offline helper scripts, and integrated Antigravity execution
discipline (file-driven `prompt.txt` execution, Modes A-D, tool reasoning,
and technical domain references).

## Slash commands

| Command | What it does |
|---|---|
| `/bench` | Re-anchor on the current task, execute `prompt.txt`, or resume work. |
| `/bench-audit` | Read the project and report what to fix first, in priority order. |
| `/bench-rules` | Install or refresh the protocol surfaces in this project + global settings. |
| `/bench-opener` | Build the Turn 1 opener for a new session. |
| `/bench-proxy` | Set up the optional injection proxy. Last resort only. |
| `/bench-doctor` | Read-only check that the setup is intact. |

## The protocol

- **Task first. Execute, ship.**
- Three limits: 1) no recap  2) no persona talk  3) no safety preamble
- Every tool call opens with `# reason: <file/fungsi/kenapa>`
- Complete artifacts only — no placeholder, no truncation, write to disk via `write_file`
- File-driven workflow: `prompt.txt` with read-before-evaluate guarantee (§0.3)
- Plan safety: Plain `plan.md` only; never use native review-loop tools (`task_boundary`, `notify_user`)
- Re-anchor word: `bench`
- Output ends with a `[Null]` ruling line, no closing summary

## Layout

```text
bench-protocol/
├── plugin.json
├── README.md
├── assets/logo.svg
├── rules/
│   └── bench-protocol.md          # trigger: always_on
├── skills/
│   ├── bench/
│   │   ├── SKILL.md               # /bench (re-anchor + prompt.txt engine)
│   │   ├── references/            # Antigravity technical references
│   │   │   ├── core.md            # Craft & reverse engineering baseline
│   │   │   ├── operating_rules.md # Core rules & tool whitelist (§0 - §2)
│   │   │   ├── cracking.md        # Binary RE & unpacking domain
│   │   │   ├── instrumentation.md # Process memory & engine RE domain
│   │   │   └── redteam.md         # Prompt research & evaluation domain
│   │   └── resources/
│   │       └── prompt.txt         # Execution ticket template
│   ├── bench-audit/SKILL.md       # /bench-audit
│   ├── bench-rules/SKILL.md       # /bench-rules
│   ├── bench-opener/SKILL.md      # /bench-opener
│   ├── bench-proxy/SKILL.md       # /bench-proxy
│   └── bench-doctor/SKILL.md      # /bench-doctor
└── scripts/
    ├── bench_install.py           # writes the surfaces
    ├── bench_doctor.py            # read-only check
    ├── bench_proxy.py             # optional injector
    └── test_bench_protocol.py     # offline test suite
```

## Install

```bash
agy plugin validate --strict ./bench-protocol
agy plugin install ./bench-protocol
agy plugin list
```

## Verification

```bash
python scripts/test_bench_protocol.py
python scripts/bench_doctor.py --project .
```
