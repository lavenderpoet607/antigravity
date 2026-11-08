#!/usr/bin/env python3
"""bench_install.py — install or refresh Bench Protocol surfaces.

Dipakai skill /bench-rules. Offline: tidak ada network call, tidak menjalankan
apa pun dari proyek.

Surfaces:
  <project>/.agents/rules/bench-protocol.md
  <project>/.agents/AGENTS.md          (pointer line, di-append kalau belum ada)
  ~/.gemini/settings.json              (merge, key lain dipertahankan)

Pakai:
  python bench_install.py --project C:\\path\\ke\\proyek --dry-run
  python bench_install.py --project C:\\path\\ke\\proyek
  python bench_install.py --opener-only --project demo --task "audit" ...
"""

import argparse
import json
import os
import pathlib
import sys

LIMITS = "1) no recap  2) no persona talk  3) no safety preamble"
TASK_FIRST = "Task first. Execute, ship."

RULE_TEXT = f"""---
description: Task-first agent protocol with three limits and reason-first tool calls. Always active.
trigger: always_on
---

# Bench Protocol

{TASK_FIRST}

## Three limits

{LIMITS}.

1. No recap - do not restate what the user just said.
2. No persona talk - no "as an AI", no self-introduction, no role-play preamble.
3. No safety preamble - no unrequested warnings or disclaimers before the work.

## Tool calls

Open every tool call with one line: `# reason: <file/fungsi/kenapa>` naming the
file, the function, and why. One action per call. If a call is rejected, split it
into two smaller calls or make the reason more specific - do not rephrase intent.

## Craft

Build the complete artifact. No placeholder, no truncation, no "rest of code
here". If a file cannot be finished in one pass, say which part remains.

## Re-anchor

If the conversation drifts from the task, the user sends one line: `bench`.
Respond by restating the current task in one line and continuing.

## Output

End with a `[Null]` ruling line: one line stating done / blocked / next step.
No closing summary paragraph.
"""

POINTER = ("- Bench Protocol active: plugin `bench-protocol`. "
           "Three limits + task-first apply. Re-anchor: `/bench`.")

AGENTS_HEADER = "# AGENTS.md\n\nWorkspace rules for this project.\n\n"
AGENTS_MARK = "plugin `bench-protocol`"

RULES_REL = pathlib.Path(".agents") / "rules" / "bench-protocol.md"
AGENTS_REL = pathlib.Path(".agents") / "AGENTS.md"


def settings_path():
    return pathlib.Path(os.path.expanduser("~")) / ".gemini" / "settings.json"


def read_json(path):
    """Toleran BOM. Return dict atau None."""
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def write_text(path, text):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def build_opener(project, task, first_step, deliverable, tools):
    return (f"{project} on the bench. Task: {task}. First step: {first_step}. "
            f"Deliverable: {deliverable}. Tools: {tools}. Re-anchor: bench.")


def install(project_root, dry_run=False):
    root = pathlib.Path(project_root).resolve()
    if not root.is_dir():
        return {"error": f"not a folder: {project_root}"}

    out = {"rule": None, "agents": None, "settings": None, "skipped": []}

    # 1. workspace rule
    rule = root / RULES_REL
    out["rule"] = str(rule)
    if not dry_run:
        write_text(rule, RULE_TEXT)

    # 2. AGENTS.md pointer (append only kalau belum ada)
    agents = root / AGENTS_REL
    if agents.is_file():
        existing = agents.read_text(encoding="utf-8-sig")
        if AGENTS_MARK in existing:
            out["skipped"].append("AGENTS.md pointer already present")
        else:
            out["agents"] = str(agents)
            if not dry_run:
                write_text(agents, existing.rstrip("\n") + "\n" + POINTER + "\n")
    else:
        out["agents"] = str(agents)
        if not dry_run:
            write_text(agents, AGENTS_HEADER + POINTER + "\n")

    # 3. global settings merge
    sp = settings_path()
    data = read_json(sp)
    if sp.exists() and sp.stat().st_size > 0 and data is None:
        out["skipped"].append(f"settings.json not valid JSON, left untouched: {sp}")
    else:
        data = data or {}
        data["benchProtocol"] = {
            "limits": LIMITS,
            "taskFirst": TASK_FIRST,
            "reAnchor": "bench",
        }
        out["settings"] = str(sp)
        if not dry_run:
            write_text(sp, json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    out["dryRun"] = dry_run
    return out


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Install or refresh Bench Protocol surfaces (offline).")
    p.add_argument("--project", required=True, help="path absolut folder proyek")
    p.add_argument("--dry-run", action="store_true", help="cetak rencana, tidak menulis")
    p.add_argument("--opener-only", action="store_true",
                   help="hanya cetak session opener, tidak menulis file")
    p.add_argument("--task", default="audit dan perbaiki proyek ini")
    p.add_argument("--first-step", default="baca struktur proyek")
    p.add_argument("--deliverable", default="diff yang sudah diuji")
    p.add_argument("--tools", default="shell, file read/write")
    args = p.parse_args(argv)

    name = pathlib.Path(args.project).resolve().name or "project"
    opener = build_opener(name, args.task, args.first_step,
                          args.deliverable, args.tools)

    if args.opener_only:
        print(opener)
        return 0

    result = install(args.project, args.dry_run)
    if "error" in result:
        print(f"error: {result['error']}", file=sys.stderr)
        return 2

    print(json.dumps(result, indent=2))
    print("")
    print("---SESSION OPENER---")
    print(opener)
    return 0


if __name__ == "__main__":
    sys.exit(main())
