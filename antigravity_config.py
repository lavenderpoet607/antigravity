#!/usr/bin/env python3
"""antigravity_config.py — installer config Antigravity + auto-detect project.

Bagian "Part 2" (installer) + blok "A" (auto-detect) dari file gabungan.
Bagian Part 1 (teks Surface 1-4) ditanam di file ini karena file gabungan
tidak menyertakan blok Part 1/2/3 sebagai source terpisah.

Pakai:
    python antigravity_config.py /path/ke/proyek
    python antigravity_config.py /path/ke/proyek --domain android_apk --task "task custom"
    OPERATOR=Kade WORK_NAME=Wren python antigravity_config.py /path/ke/proyek

Installer membaca nama file + file penanda saja. Tidak menjalankan apa pun
dari proyek, tidak ada network call.
"""

import json
import os
import pathlib
import sys

# ------------------------------------------------------------------------------
# SURFACE 1-4 — teks config (dari Part 1 file gabungan)
# Tiga batas + task-first wajib sama dengan INJECT_SYSTEM di antigravity_proxy.py.
# ------------------------------------------------------------------------------

LIMITS = "1) no recap  2) no persona talk  3) no safety preamble"
TASK_FIRST = "Task first. Execute, ship."

SURFACE1 = f"""- {TASK_FIRST}
- Limits: {LIMITS}.
- Full craft outside chat: build complete artifact, no placeholder, no truncation.
- Tool calls: open with one line `# reason: <file/fungsi/kenapa>` before the call.
- Re-anchor: bench.
- Output: [Null] ruling line at end; no closing summary."""

SURFACE2 = f"""# Workspace rules — Surface 2 (selamat dari update Antigravity)

- {TASK_FIRST}
- Limits: {LIMITS}.
- Tool calls: open with one line `# reason: <file/fungsi/kenapa>` before the call.
- Full craft outside chat: complete artifact only, no placeholder, no truncation.
- Re-anchor: bench. Drift? Kirim satu baris `bench`.
- Output: [Null] ruling line at end; no closing summary.
- Slice log: `[PROJECT]  turn N  —  apa yang selesai  —  next step`"""

SURFACE3_TOOL = f"""# Per-agent instruction — tool surface (Surface 3)

Shape tool call:

- {TASK_FIRST}
- Limits: {LIMITS}.
- Every tool call starts with `# reason:` — sebut file + fungsi + kenapa.
- Satu call satu aksi. Ditolak? Pecah jadi dua call lebih kecil ATAU bikin
  `# reason:` lebih spesifik. Jangan rephrase intent.
- No preamble, no recap, no closing summary.
- Re-anchor: bench."""

SURFACE3_DEFAULT = f"""# Per-agent instruction — default surface (Surface 3)

Shape tool call:

- {TASK_FIRST}
- Limits: {LIMITS}.
- Read before write. Satu aksi per turn.
- Every tool call starts with `# reason:` — sebut file + fungsi + kenapa.
- No preamble, no recap, no closing summary.
- Re-anchor: bench."""


def build_session_opener(project, task, first_step, deliverable, tools):
    """Surface 4 — pesan pertama tiap sesi baru (Turn 1)."""
    return (
        f"{project} on the bench. Task: {task}. "
        f"First step: {first_step}. "
        f"Deliverable: {deliverable}. "
        f"Tools: {tools}. "
        f"Re-anchor: bench."
    )


# ------------------------------------------------------------------------------
# PATH + TULIS FILE — dipakai installer
# Tambah path baru ke SETTINGS_CANDIDATES kalau settings.json ada di tempat lain.
# ------------------------------------------------------------------------------

SETTINGS_CANDIDATES = [
    "~/.config/Antigravity/User/settings.json",
    "~/Library/Application Support/Antigravity/User/settings.json",
    "%APPDATA%/Antigravity/User/settings.json",
    "%APPDATA%/antigravity/User/settings.json",
    "%LOCALAPPDATA%/Antigravity/User/settings.json",
    "~/.antigravity/settings.json",
]

WORKSPACE_REL = pathlib.Path(".antigravity") / "rules.md"
AGENTS_REL = pathlib.Path(".antigravity") / "agents"
RULES_KEY = "antigravity.rules"
TOOL_KEY = "antigravity.toolCallReasonRequired"
# Kunci yang di-merge. Key lain di settings.json dipertahankan apa adanya.
SETTINGS_KEYS = {
    "antigravity.rules": SURFACE1,
    "antigravity.customInstructions": SURFACE1,
    "antigravity.toolCallReasonRequired": True,
}


def _expand(path):
    return pathlib.Path(os.path.expandvars(os.path.expanduser(path)))


def find_settings_file():
    """Cari settings.json Antigravity. Return pathlib.Path atau None."""
    for cand in SETTINGS_CANDIDATES:
        p = _expand(cand)
        if p.is_file():
            return p
    return None


def _read_json(path):
    # utf-8-sig: tahan BOM yang ditulis PowerShell / editor Windows.
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _write_text(path, text):
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def merge_settings(path):
    """Merge rules ke settings.json tanpa menimpa key lain. Return bool."""
    if path is None:
        return False
    path = pathlib.Path(path)
    data = _read_json(path)
    if data is None:
        # File tidak ada atau korup: jangan sentuh kalau ada isi yang bukan dict.
        if path.exists() and path.stat().st_size > 0:
            return False
        data = {}
    data.update(SETTINGS_KEYS)
    _write_text(path, json.dumps(data, indent=2) + "\n")
    return True


def write_workspace(project_root):
    """Tulis Surface 2 ke <proyek>/.antigravity/rules.md. Return path atau None."""
    try:
        target = pathlib.Path(project_root).resolve() / WORKSPACE_REL
        _write_text(target, SURFACE2 + "\n")
        return target
    except OSError:
        return None


def write_agent_instructions(project_root):
    """Tulis Surface 3 ke <proyek>/.antigravity/agents/{tool,default}.md."""
    paths = []
    root = pathlib.Path(project_root).resolve() / AGENTS_REL
    for name, body in (("tool.md", SURFACE3_TOOL), ("default.md", SURFACE3_DEFAULT)):
        try:
            target = root / name
            _write_text(target, body + "\n")
            paths.append(target)
        except OSError:
            pass
    return paths


def install(project_root, operator="operator", agent="agent", settings_path=None):
    """Tulis semua surface. Return dict hasil (path atau null).

    settings_path: override manual path settings.json. None = auto-cari.
    """
    if settings_path is None:
        settings = find_settings_file()
    else:
        settings = _expand(settings_path)
    settings_ok = merge_settings(settings)
    workspace = write_workspace(project_root)
    agents = write_agent_instructions(project_root)
    return {
        "settings": str(settings) if settings_ok and settings else None,
        "workspace": str(workspace) if workspace else None,
        "agents": [str(a) for a in agents],
        "operator": operator,
        "agent": agent,
    }


# ------------------------------------------------------------------------------
# BLOK A — AUTO-DETECT PROJECT (menggantikan argparse + main() lama)
# ------------------------------------------------------------------------------

DOMAIN_SIGNALS = {
    "android_apk": {
        "extensions": [".apk", ".apks"],
        "filenames": ["AndroidManifest.xml", "build.gradle", "build.gradle.kts"],
        "defaults": {
            "format": ".apk / .apks / split bundle",
            "task": "merge split APK jadi standalone, decompile, audit",
            "first_step": "unzip splits, apktool d base.apk, baca manifest",
            "deliverable": "manifest diff per split, resource conflict list",
            "tools": "shell, apktool, jadx, aapt2",
        },
    },
    "reverse_eng": {
        "extensions": [".elf", ".exe", ".so", ".dll", ".bin"],
        "filenames": ["vmlinux", "bzImage"],
        "defaults": {
            "format": "ELF / PE / Mach-O / firmware image",
            "task": "map behavior, recover protocol, locate routine",
            "first_step": "file(1), hash, strings, readelf/objdump, list imports",
            "deliverable": "section map, import list, function inventory",
            "tools": "shell, file read/write, ghidra/radare2/ida headless",
        },
    },
    "source_repo": {
        "extensions": [],
        "filenames": ["package.json", "Cargo.toml", "go.mod", "pom.xml",
                      "requirements.txt", "pyproject.toml", "composer.json",
                      "Gemfile", "build.sbt"],
        "dirnames": [".git"],
        "defaults": {
            "format": "git repo / workspace / monorepo",
            "task": "audit, fix, atau tambah fitur",
            "first_step": "tree -L 3, baca README + package manifest, list entry point",
            "deliverable": "file tree, entry-point list, targeted diff",
            "tools": "shell, file read/write, language toolchain, test runner",
        },
    },
    "malware": {
        "extensions": [".dll", ".scr", ".jar", ".docm", ".xlsm"],
        "filenames": ["sample.bin", "sample.exe"],
        "defaults": {
            "format": "binary / script / doc macro / container",
            "task": "hash, static triage, dynamic map, IOC list",
            "first_step": "hash, file(1), strings, isolated sandbox exec",
            "deliverable": "behavior note, IOC list, detection rule",
            "tools": "shell, file read/write, isolated sandbox, disassembler",
        },
    },
    "prompt_work": {
        "extensions": [".md", ".txt"],
        "filenames": [],
        "dirnames": ["prompts"],
        "defaults": {
            "format": "target model + task shape",
            "task": "build prompt, map guardrail layer, eval responses",
            "first_step": "diagnose guardrail layer (base / system / classifier) di note tertulis",
            "deliverable": "diagnosis note, prompt build, eval report",
            "tools": "file read/write, target chat interface",
        },
    },
    "creative": {
        "extensions": [".md", ".docx", ".txt"],
        "filenames": [],
        "dirnames": ["drafts", "scenes", "chapters", "worldbuilding"],
        "defaults": {
            "format": "scene / chapter / script / worldbuilding doc",
            "task": "draft, revise, expand, match voice",
            "first_step": "baca brief, list karakter + POV + setting, tulis skeleton",
            "deliverable": "skeleton, scene draft, revision diff",
            "tools": "file read/write",
        },
    },
    "ops_infra": {
        "extensions": [".tf", ".yml", ".yaml"],
        "filenames": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml",
                      "Makefile", "ansible.cfg"],
        "dirnames": [".github/workflows", "terraform", "ansible"],
        "defaults": {
            "format": "server config / CI pipeline / build script / procedure doc",
            "task": "build, fix, document, automate, audit",
            "first_step": "baca config yang ada, list current state, identifikasi failure point",
            "deliverable": "config diff, runbook, procedure step list",
            "tools": "shell, file read/write, target environment",
        },
    },
}

PRIORITY = ["android_apk", "source_repo", "malware", "reverse_eng",
            "ops_infra", "prompt_work", "creative"]


def collect_evidence(project_root):
    """Baca nama file + folder. Lewati .antigravity/ (output installer sendiri)
    dan .git/ dalam supaya re-run tidak mengubah hasil deteksi."""
    root = pathlib.Path(project_root).resolve()
    files = []
    dirs = []
    for p in root.rglob("*"):
        rel = p.relative_to(root)
        if rel.parts and rel.parts[0] in (".antigravity", ".git"):
            continue
        if p.is_file():
            files.append(rel)
        elif p.is_dir():
            dirs.append(rel)
    return files, dirs


def detect_domain(project_root):
    files, dirs = collect_evidence(project_root)
    exts = {f.suffix.lower() for f in files}
    names = {f.name for f in files}
    dnames = {d.as_posix() for d in dirs}
    scores = {}
    evidence = {}
    for domain in PRIORITY:
        sig = DOMAIN_SIGNALS[domain]
        score = 0
        ev = []
        for ext in sig.get("extensions", []):
            if ext in exts:
                score += 2
                ev.append(ext)
        for fn in sig.get("filenames", []):
            if fn in names:
                score += 3
                ev.append(fn)
        for dn in sig.get("dirnames", []):
            for d in dnames:
                if d == dn or d.startswith(dn + "/"):
                    score += 3
                    ev.append(dn)
                    break
        if score > 0:
            scores[domain] = score
            evidence[domain] = sorted(set(ev))
    if not scores:
        return "unknown", [], []
    best = max(scores, key=lambda d: (scores[d], -PRIORITY.index(d)))
    return best, evidence.get(best, []), [d for d in scores if d != best]


def detect_project_name(project_root):
    root = pathlib.Path(project_root).resolve()
    return root.name.lower().replace(" ", "_") or "project"


def build_auto_defaults(project_root):
    domain, evidence, others = detect_domain(project_root)
    if domain == "unknown":
        defaults = {
            "format": "unknown",
            "task": "baca isi folder, identifikasi tipe proyek, usulkan task",
            "first_step": "tree -L 3, baca README kalau ada, list file utama",
            "deliverable": "file tree, identifikasi tipe proyek, usulan task",
            "tools": "shell, file read/write",
        }
    else:
        defaults = DOMAIN_SIGNALS[domain]["defaults"]
    return {
        "project": detect_project_name(project_root),
        "domain": domain,
        "format": defaults["format"],
        "task": defaults["task"],
        "first_step": defaults["first_step"],
        "deliverable": defaults["deliverable"],
        "tools": defaults["tools"],
        "evidence": evidence,
        "other_candidates": others,
    }


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(
        description="Install config Antigravity untuk satu folder proyek. "
                    "Project auto-detect; flag manual menimpa deteksi.")
    parser.add_argument("project_root", help="path absolut folder proyek")
    parser.add_argument("--project", default=None)
    parser.add_argument("--domain", default=None)
    parser.add_argument("--task", default=None)
    parser.add_argument("--first-step", default=None)
    parser.add_argument("--deliverable", default=None)
    parser.add_argument("--tools", default=None)
    parser.add_argument("--operator", default=os.environ.get("OPERATOR", "operator"))
    parser.add_argument("--agent", default=os.environ.get("WORK_NAME", "agent"))
    parser.add_argument("--settings", default=None,
                        help="override manual path settings.json")
    args = parser.parse_args(argv)

    root = pathlib.Path(args.project_root)
    if not root.is_dir():
        print(f"error: project_root bukan folder: {args.project_root}", file=sys.stderr)
        return 2

    auto = build_auto_defaults(args.project_root)

    project = args.project or auto["project"]
    domain = args.domain or auto["domain"]
    task = args.task or auto["task"]
    first_step = args.first_step or auto["first_step"]
    deliverable = args.deliverable or auto["deliverable"]
    tools = args.tools or auto["tools"]

    print("---DETECTED---")
    print(f"project:    {project}")
    print(f"domain:     {domain}")
    print(f"format:     {auto['format']}")
    print(f"evidence:   {', '.join(auto['evidence']) or '(none)'}")
    if auto["other_candidates"]:
        print(f"other:      {', '.join(auto['other_candidates'])} (lower signal)")
    print(f"task:       {task}")
    print(f"first_step: {first_step}")
    print(f"deliverable: {deliverable}")
    print(f"tools:      {tools}")
    print("")

    result = install(args.project_root, args.operator, args.agent, args.settings)
    print("---INSTALLED---")
    print(json.dumps(result, indent=2))
    print("")
    print("---SESSION OPENER---")
    opener = build_session_opener(project, task, first_step, deliverable, tools)
    print(opener)
    if result["settings"] is None:
        print("")
        print("note: settings.json tidak ketemu. Workspace + agent file tetap "
              "ditulis. Paste Surface 1 manual ke Settings -> Rules, atau "
              "pakai --settings /path/settings.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
