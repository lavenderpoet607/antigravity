#!/usr/bin/env python3
"""bench_doctor.py — cek setup Bench Protocol tanpa mengubah apa pun.

Dipakai skill /bench-doctor. Read-only.

Cek: plugin present, workspace surfaces, settings valid, wording konsisten,
batas ukuran. Exit 0 = bersih, 1 = ada yang gagal.

Pakai:
    python bench_doctor.py --project C:\\path\\ke\\proyek
"""

import argparse
import json
import os
import pathlib
import sys

LIMITS = "1) no recap  2) no persona talk  3) no safety preamble"
TASK_FIRST = "Task first. Execute, ship."
VALID_TRIGGERS = ("always_on", "model_decision", "glob", "manual")
MAX_BYTES = 24000


def plugin_root():
    return pathlib.Path(__file__).resolve().parent.parent


def global_settings():
    return pathlib.Path(os.path.expanduser("~")) / ".gemini" / "settings.json"


def frontmatter(text):
    """Ambil YAML frontmatter sederhana sebagai dict str->str. Tanpa dependency."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    out = {}
    for line in text[3:end].splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def read(path):
    try:
        return pathlib.Path(path).read_text(encoding="utf-8-sig")
    except OSError:
        return None


def check_plugin_present():
    root = plugin_root()
    manifest = root / "plugin.json"
    if not manifest.is_file():
        return False, f"plugin.json missing at {manifest}"
    try:
        data = json.loads(manifest.read_text(encoding="utf-8-sig"))
    except ValueError as e:
        return False, f"plugin.json not valid JSON: {e}"
    if not data.get("name"):
        return False, "plugin.json has no name"
    return True, f"plugin {data['name']} v{data.get('version', '?')}"


def check_workspace(project):
    root = pathlib.Path(project).resolve()
    rule = root / ".agents" / "rules" / "bench-protocol.md"
    agents = root / ".agents" / "AGENTS.md"
    problems = []
    if not rule.is_file():
        problems.append(f"missing {rule}")
    else:
        fm = frontmatter(read(rule) or "")
        trig = fm.get("trigger", "")
        if trig not in VALID_TRIGGERS:
            problems.append(f"rule trigger invalid: '{trig}' "
                            f"(need one of {', '.join(VALID_TRIGGERS)})")
    if not agents.is_file():
        problems.append(f"missing {agents}")
    elif "bench-protocol" not in (read(agents) or ""):
        problems.append("AGENTS.md has no bench-protocol pointer")
    if problems:
        return False, "; ".join(problems)
    return True, f"rule + AGENTS.md present in {root.name}"


def check_settings(_project=None):
    """_project diabaikan; argumen ada supaya signature sama dengan check_workspace."""
    sp = global_settings()
    if not sp.is_file():
        return False, f"missing {sp} (run /bench-rules)"
    raw = sp.read_bytes()
    try:
        json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, ValueError) as e:
        return False, f"settings.json not valid JSON: {e}"
    return True, str(sp)


def check_wording():
    root = plugin_root()
    sources = {
        "plugin rule": read(root / "rules" / "bench-protocol.md"),
        "bench_install RULE_TEXT": read(root / "scripts" / "bench_install.py"),
        "bench_proxy INJECT_SYSTEM": read(root / "scripts" / "bench_proxy.py"),
    }
    missing = [name for name, text in sources.items()
               if text is None or LIMITS not in text or TASK_FIRST not in text]
    if missing:
        return False, f"limits/task-first missing or different in: {', '.join(missing)}"
    return True, f"consistent across {len(sources)} surfaces"


def check_sizes():
    root = plugin_root()
    over = []
    for skill in sorted((root / "skills").glob("*/SKILL.md")):
        size = len(skill.read_bytes())
        if size > MAX_BYTES:
            over.append(f"{skill.parent.name}: {size} bytes")
    for rule in sorted((root / "rules").glob("*.md")):
        size = len(rule.read_bytes())
        if size > MAX_BYTES:
            over.append(f"{rule.name}: {size} bytes")
    if over:
        return False, "over 24000 bytes: " + "; ".join(over)
    return True, "all skills and rules under 24000 bytes"


def check_skill_names():
    """Setiap name di frontmatter harus sama dengan nama folder induknya."""
    root = plugin_root()
    bad = []
    for skill in sorted((root / "skills").glob("*/SKILL.md")):
        fm = frontmatter(read(skill) or "")
        name = fm.get("name", "")
        if not fm.get("description"):
            bad.append(f"{skill.parent.name}: no description")
        if name and name != skill.parent.name:
            bad.append(f"{skill.parent.name}: name '{name}' != folder")
    if bad:
        return False, "; ".join(bad)
    return True, "all skill names match folders"


CHECKS = [
    ("plugin present", check_plugin_present),
    ("skill names", check_skill_names),
    ("wording consistent", check_wording),
    ("sizes within limit", check_sizes),
]


def main(argv=None):
    p = argparse.ArgumentParser(description="Check Bench Protocol setup (read-only).")
    p.add_argument("--project", default=None,
                   help="path folder proyek untuk cek workspace")
    args = p.parse_args(argv)

    results = []
    for name, fn in CHECKS:
        try:
            ok, detail = fn()
        except Exception as e:  # noqa: BLE001 - doctor tidak boleh crash
            ok, detail = False, f"check crashed: {e}"
        results.append((name, ok, detail))

    if args.project:
        for name, fn in (("workspace surfaces", check_workspace),
                         ("settings valid", check_settings)):
            try:
                ok, detail = fn(args.project)
            except Exception as e:  # noqa: BLE001
                ok, detail = False, f"check crashed: {e}"
            results.append((name, ok, detail))

    failed = 0
    print(f"{'RESULT':<7} {'CHECK':<22} DETAIL")
    for name, ok, detail in results:
        if not ok:
            failed += 1
        print(f"{'PASS' if ok else 'FAIL':<7} {name:<22} {detail}")

    print("")
    if failed:
        print(f"{failed} check(s) failed")
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
