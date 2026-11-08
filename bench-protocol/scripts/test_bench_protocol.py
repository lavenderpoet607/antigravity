"""Smoke test bench-protocol plugin. Run: python scripts/test_bench_protocol.py"""

import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import bench_doctor as doc  # noqa: E402
import bench_install as inst  # noqa: E402
import bench_proxy as proxy  # noqa: E402

failures = []


def check(name, cond, detail=""):
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not cond else ""))
    if not cond:
        failures.append(name)


# --- manifest ----------------------------------------------------------------
manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8-sig"))
check("manifest name is kebab-case", manifest["name"] == "bench-protocol")
check("manifest has version", bool(manifest.get("version")))
check("manifest has logo", (ROOT / manifest.get("logo", "")).is_file())
check("manifest suggestedPrompts <= 3", len(manifest.get("suggestedPrompts", [])) <= 3)
check("manifest has author", bool(manifest.get("author", {}).get("name")))

# --- skills ------------------------------------------------------------------
skills = sorted((ROOT / "skills").glob("*/SKILL.md"))
check("six skills present", len(skills) == 6, f"found {len(skills)}")
for skill in skills:
    fm = doc.frontmatter(skill.read_text(encoding="utf-8-sig"))
    check(f"{skill.parent.name}: name matches folder",
          fm.get("name") == skill.parent.name, fm.get("name", ""))
    check(f"{skill.parent.name}: has description", bool(fm.get("description")))
    check(f"{skill.parent.name}: under 24000 bytes", len(skill.read_bytes()) < 24000)

# --- rule --------------------------------------------------------------------
rule = ROOT / "rules" / "bench-protocol.md"
fm = doc.frontmatter(rule.read_text(encoding="utf-8-sig"))
check("rule trigger valid", fm.get("trigger") in doc.VALID_TRIGGERS, fm.get("trigger", ""))
check("rule trigger is always_on", fm.get("trigger") == "always_on")
check("rule has description", bool(fm.get("description")))

# --- wording consistency -----------------------------------------------------
for label, path in (("rule", rule), ("bench_install", HERE / "bench_install.py"),
                    ("bench_proxy", HERE / "bench_proxy.py")):
    text = path.read_text(encoding="utf-8-sig")
    check(f"{label}: limits string present", doc.LIMITS in text)
    check(f"{label}: task-first present", doc.TASK_FIRST in text)

# --- doctor ------------------------------------------------------------------
for name, fn in (("plugin present", doc.check_plugin_present),
                 ("skill names", doc.check_skill_names),
                 ("wording consistent", doc.check_wording),
                 ("sizes", doc.check_sizes)):
    ok, detail = fn()
    check(f"doctor: {name}", ok, detail)

# --- proxy rewrite -----------------------------------------------------------
body = json.dumps({"contents": [{"role": "user", "parts": [{"text": "hi"}]}]})
new_body, status = proxy.rewrite_body(body.encode("utf-8"))
check("proxy injects into empty body", status == "injected", status)
check("proxy frame lands in systemInstruction",
      doc.TASK_FIRST in json.loads(new_body.decode("utf-8"))["systemInstruction"]["parts"][0]["text"])

again, status2 = proxy.rewrite_body(new_body)
check("proxy does not double-inject", status2 == "already", status2)
check("proxy body unchanged on already", again == new_body)

passthrough, status3 = proxy.rewrite_body(b"not json")
check("proxy passes non-JSON through",
      status3 == "passthrough" and passthrough == b"not json")

empty, status4 = proxy.rewrite_body(b"")
check("proxy handles empty body", status4 == "passthrough" and empty == b"")

existing = json.dumps({"systemInstruction": {"parts": [{"text": "keep me"}]}})
merged, status5 = proxy.rewrite_body(existing.encode("utf-8"))
check("proxy keeps existing system text",
      "keep me" in json.loads(merged.decode("utf-8"))["systemInstruction"]["parts"][0]["text"])

# --- install into temp project ----------------------------------------------
tmp = pathlib.Path(tempfile.mkdtemp(prefix="bench_"))
(tmp / ".agents").mkdir(parents=True, exist_ok=True)
(tmp / ".agents" / "AGENTS.md").write_text("# Mine\n\n- keep this line\n", encoding="utf-8")

fake_settings = tmp / "settings.json"
fake_settings.write_bytes(b'\xef\xbb\xbf{"mcpServers": {"x": {}}, "keep": true}')
orig_settings = inst.settings_path


def _install():
    inst.settings_path = lambda: fake_settings
    try:
        return inst.install(str(tmp))
    finally:
        inst.settings_path = orig_settings


res = _install()

check("install wrote workspace rule", (tmp / ".agents" / "rules" / "bench-protocol.md").is_file())
agents_text = (tmp / ".agents" / "AGENTS.md").read_text(encoding="utf-8")
check("install appended pointer, kept user content",
      "keep this line" in agents_text and "bench-protocol" in agents_text)
merged_settings = json.loads(fake_settings.read_text(encoding="utf-8-sig"))
check("install kept foreign settings key", merged_settings.get("keep") is True)
check("install kept mcpServers", "x" in merged_settings.get("mcpServers", {}))
check("install added benchProtocol", "benchProtocol" in merged_settings)

# idempotent
h1 = hashlib.sha256((tmp / ".agents" / "rules" / "bench-protocol.md").read_bytes()).hexdigest()
_install()
h2 = hashlib.sha256((tmp / ".agents" / "rules" / "bench-protocol.md").read_bytes()).hexdigest()
check("install idempotent", h1 == h2)
check("pointer not duplicated",
      (tmp / ".agents" / "AGENTS.md").read_text(encoding="utf-8").count("bench-protocol") == 1)

# corrupt settings untouched
bad = tmp / "bad.json"
bad.write_text("{not json", encoding="utf-8")
inst.settings_path = lambda: bad
try:
    res2 = inst.install(str(tmp))
finally:
    inst.settings_path = orig_settings
check("corrupt settings untouched", bad.read_text(encoding="utf-8") == "{not json")
check("corrupt settings reported",
      any("not valid JSON" in s for s in res2["skipped"]), str(res2["skipped"]))

# non-folder guard
check("install rejects missing folder", "error" in inst.install(str(tmp / "nope")))

# --- opener ------------------------------------------------------------------
opener = inst.build_opener("demo", "audit", "run tests", "report", "shell")
check("opener contains all fields",
      all(x in opener for x in ("demo", "audit", "run tests", "report", "shell",
                                "Re-anchor: bench.")))

# --- scripts compile ---------------------------------------------------------
rc = subprocess.run([sys.executable, "-m", "py_compile",
                     str(HERE / "bench_install.py"), str(HERE / "bench_doctor.py"),
                     str(HERE / "bench_proxy.py")], capture_output=True)
check("helper scripts compile", rc.returncode == 0, rc.stderr.decode()[:200])

print()
if failures:
    print(f"{len(failures)} FAILED: {failures}")
    sys.exit(1)
print("ALL PASS")
