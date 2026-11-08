"""Smoke test antigravity_config.py — jalankan: python _test/test_antigravity_config.py"""

import json
import pathlib
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import antigravity_config as ac  # noqa: E402

failures = []


def check(name, cond, detail=""):
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        failures.append(name)


def make_project(files):
    root = pathlib.Path(tempfile.mkdtemp(prefix="agtest_"))
    for f in files:
        p = root / f
        p.parent.mkdir(parents=True, exist_ok=True)
        if f.endswith("/"):
            p.mkdir(exist_ok=True)
        else:
            p.write_text("x", encoding="utf-8")
    return root


# --- deteksi domain -----------------------------------------------------------
cases = {
    "android_apk": ["app.apk", "base.apk"],
    "source_repo": ["package.json"],
    "reverse_eng": ["firmware.elf"],
    "malware": ["evil.dll"],
    "ops_infra": ["Dockerfile"],
    "creative": ["drafts/scene1.md"],
}
for expected, files in cases.items():
    r = ac.build_auto_defaults(str(make_project(files)))
    check(f"detect {expected}", r["domain"] == expected, f"got {r['domain']}")

# source_repo menang atas extension lain (priority)
r = ac.build_auto_defaults(str(make_project(["package.json", "lib.so"])))
check("priority source_repo over reverse_eng", r["domain"] == "source_repo", r["domain"])

# folder kosong -> domain "unknown" dengan default generik yang terisi penuh
r = ac.build_auto_defaults(str(make_project([])))
check("empty dir -> unknown", r["domain"] == "unknown", r["domain"])
check("empty dir evidence empty", r["evidence"] == [], str(r["evidence"]))
check("unknown domain has non-empty defaults",
      all(r[k] for k in ("format", "task", "first_step", "deliverable", "tools")), str(r))

# output dir sendiri tidak boleh memicu prompt_work
r = ac.build_auto_defaults(str(make_project([".antigravity/rules.md"])))
check("own output dir ignored", r["evidence"] == [], str(r["evidence"]))

# --- installer ----------------------------------------------------------------
proj = make_project(["package.json"])
settings = proj / "_cfg" / "settings.json"
settings.parent.mkdir(parents=True, exist_ok=True)
settings.write_bytes(b'\xef\xbb\xbf{"editor.fontSize": 15, "keep.me": [1, 2]}')

res = ac.install(str(proj), "Kade", "Wren", str(settings))
check("install returns settings path", res["settings"] is not None, str(res["settings"]))
check("workspace rules.md written", (proj / ".antigravity" / "rules.md").is_file())
check("tool.md written", (proj / ".antigravity" / "agents" / "tool.md").is_file())
check("default.md written", (proj / ".antigravity" / "agents" / "default.md").is_file())

data = json.loads(settings.read_text(encoding="utf-8-sig"))
check("BOM settings merged (no data loss)", data.get("editor.fontSize") == 15)
check("foreign key preserved", data.get("keep.me") == [1, 2])
check("rules == SURFACE1", data.get("antigravity.rules") == ac.SURFACE1)
check("customInstructions == SURFACE1", data.get("antigravity.customInstructions") == ac.SURFACE1)
check("toolCallReasonRequired True", data.get("antigravity.toolCallReasonRequired") is True)

# tiga batas + task-first wajib muncul di setiap surface
for label, text in (("SURFACE1", ac.SURFACE1), ("SURFACE2", ac.SURFACE2),
                    ("SURFACE3_TOOL", ac.SURFACE3_TOOL),
                    ("SURFACE3_DEFAULT", ac.SURFACE3_DEFAULT)):
    check(f"{label} has 3 limits", "1) no recap" in text and "3) no safety preamble" in text)
    check(f"{label} task-first", "Task first. Execute, ship." in text)

# idempotensi
before = (proj / ".antigravity" / "rules.md").read_bytes()
ac.install(str(proj), "Kade", "Wren", str(settings))
check("idempotent re-run", (proj / ".antigravity" / "rules.md").read_bytes() == before)

# settings baru (belum ada) dibuat
fresh = proj / "_cfg" / "new.json"
res2 = ac.install(str(proj), "Kade", "Wren", str(fresh))
check("new settings file created", res2["settings"] is not None and fresh.is_file())

# tanpa settings di sistem -> settings null, file lain tetap ditulis
proj3 = make_project([])
saved = ac.SETTINGS_CANDIDATES[:]
ac.SETTINGS_CANDIDATES = ["~/definitely/not/here/settings.json"]
try:
    res3 = ac.install(str(proj3))
    check("missing settings -> null", res3["settings"] is None, str(res3["settings"]))
    check("missing settings still writes workspace", (proj3 / ".antigravity" / "rules.md").is_file())
finally:
    ac.SETTINGS_CANDIDATES = saved

# korup settings tidak ditimpa
proj4 = make_project([])
bad = proj4 / "bad.json"
bad.write_text("{not json", encoding="utf-8")
res4 = ac.install(str(proj4), settings_path=str(bad))
check("corrupt settings untouched", bad.read_text(encoding="utf-8") == "{not json")
check("corrupt settings reported null", res4["settings"] is None)

# session opener
opener = ac.build_session_opener("Demo", "audit", "tree", "diff", "shell")
check("opener has all parts",
      all(x in opener for x in ("Demo", "audit", "tree", "diff", "shell", "Re-anchor: bench.")))

print()
if failures:
    print(f"{len(failures)} FAILED: {failures}")
    sys.exit(1)
print("ALL PASS")
