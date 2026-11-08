# Antigravity Config Installer

Implementasi dari `deepseek_text_20261108_0a8078.txt` (Part 2 + blok A).
Menanam config "task-first + 3 batas" ke Antigravity lewat file workspace,
file per-agent, dan merge `settings.json`.

## File

| File | Isi |
|---|---|
| `antigravity_config.py` | Installer + auto-detect proyek (Part 2 + blok A). **Ini yang dipakai.** |
| `antigravity_proxy.py` | Proxy injeksi system instruction (Part 3) — **opsional**. |
| `_test/test_antigravity_config.py` | Smoke test (34 check). |

Surface 1–4 ditanam di `antigravity_config.py` karena file gabungan hanya
memuat Part 2/3 + blok A, bukan Part 1 sebagai source terpisah.

## Pemakaian (PowerShell)

```powershell
cd 'c:\Users\user\Documents\project\rombak\antigravity'

# 1. auto-detect semua (paling sering dipakai)
python antigravity_config.py 'C:\path\ke\proyek'

# 2. timpa manual kalau deteksi salah
python antigravity_config.py 'C:\path\ke\proyek' --domain android_apk `
  --task "merge split APK jadi standalone" `
  --first-step "unzip splits, apktool d base.apk" `
  --deliverable "manifest diff per split" `
  --tools "shell, apktool, jadx"

# 3. settings.json di path non-standar / belum ada (akan dibuat)
python antigravity_config.py 'C:\path\ke\proyek' `
  --settings "$env:APPDATA\Antigravity\User\settings.json"

# 4. nama operator + agent (Windows: pakai $env:, bukan VAR=x)
$env:OPERATOR='Kade'; $env:WORK_NAME='Wren'
python antigravity_config.py 'C:\path\ke\proyek'
```

Argumen pertama **wajib path absolut folder proyek**. Flag manual menimpa hasil
deteksi; yang tidak di-flag tetap dari deteksi.

## Apa yang ditulis

- `<proyek>\.antigravity\rules.md` — Surface 2 (workspace rules)
- `<proyek>\.antigravity\agents\tool.md` — Surface 3 (tool surface)
- `<proyek>\.antigravity\agents\default.md` — Surface 3 (default surface)
- `settings.json` — merge key `antigravity.rules`,
  `antigravity.customInstructions`, `antigravity.toolCallReasonRequired`.
  Key lain dipertahankan. File korup **tidak** ditimpa.

`settings.json` dicari di: `~/.config/Antigravity/User/`, `~/Library/Application
Support/Antigravity/User/`, `%APPDATA%/Antigravity/User/`,
`%APPDATA%/antigravity/User/`, `%LOCALAPPDATA%/Antigravity/User/`,
`~/.antigravity/`. Kalau tidak ketemu, installer tetap jalan dan menulis file
lain; tempel Surface 1 manual ke **Settings → Rules**.

## Proxy (opsional)

Hanya perlu kalau build tidak punya Settings → Rules, atau masih ada request yang
lolos tanpa frame.

```powershell
# cek frame + hasil rewrite tanpa network
python antigravity_proxy.py --dry-run

# jalankan (isi TARGET_HOST dulu lewat --endpoint, atau edit konstanta di file)
python antigravity_proxy.py --endpoint https://host-asli --port 8787
```

`INJECT_SYSTEM` di proxy wajib sama dengan `SURFACE1` di installer — kalau beda,
target baca dua set aturan dan drift. Ubah keduanya bersamaan.

## Plugin dengan slash command (`bench-protocol/`)

Installer di atas menulis file config. Kalau Anda ingin perintah slash asli di
Antigravity, pakai plugin ini — sudah tervalidasi dan ter-install di mesin ini.

```powershell
# validasi (0 error, 0 warning)
& "$env:USERPROFILE\.gemini\bin\agy.exe" plugin validate --strict .\bench-protocol

# install
& "$env:USERPROFILE\.gemini\bin\agy.exe" plugin install .\bench-protocol

# cek
& "$env:USERPROFILE\.gemini\bin\agy.exe" plugin list
```

Slash command yang tersedia setelah install:

| Command | Fungsi |
|---|---|
| `/bench` | re-anchor ke task aktif dan lanjut |
| `/bench-audit` | baca proyek, laporkan apa yang harus diperbaiki dulu |
| `/bench-rules` | pasang/refresh surface protokol |
| `/bench-opener` | bikin teks pembuka sesi baru |
| `/bench-proxy` | setup proxy injeksi (opsional, last resort) |
| `/bench-doctor` | cek setup masih utuh (read-only) |

Plugin ter-install ke `~/.gemini/config/plugins/bench-protocol`. Detail lengkap
di `bench-protocol/README.md`.

## Test

```powershell
python _test\test_antigravity_config.py        # installer: 34 check
python bench-protocol\scripts\test_bench_protocol.py   # plugin: 56 check
```

## Batasan yang perlu diketahui

- Installer **tidak** tahu bentuk JSON request API target. `rewrite_body` di proxy
  pakai shape Gemini (`systemInstruction.parts[].text`). Kalau capture menunjukkan
  key lain, sesuaikan fungsi itu (Langkah 5a).
- `TARGET_HOST` default `https://example.invalid` — proxy menolak jalan sampai diisi.
- Tidak ada network call dari installer; tidak menjalankan apa pun dari proyek.
