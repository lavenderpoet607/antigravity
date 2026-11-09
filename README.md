# Antigravity & Bench Protocol

Integrasi **Bench Protocol** dan arsitektur eksekusi **Antigravity** (dari `deepseek_text_20261108_0a8078.txt` dan `antigravity.zip`).

Protokol ini memaksa agen AI coding bekerja dengan prinsip **task-first**: tanpa obrolan basa-basi, langsung menulis kode utuh ke disk, menggunakan penalaran tool call, dan mendukung eksekusi berbasis file (`prompt.txt`).

---

## 1. Fitur Utama

- **Tiga Batas (Three Limits)**:
  1. *No recap* — tidak mengulang prompt pengguna.
  2. *No persona talk* — tanpa intro ("sebagai asisten AI"), tanpa role-play.
  3. *No safety preamble* — tanpa peringatan atau disclaimer moral yang tidak diminta.
- **Eksekusi Berbasis File (`prompt.txt`)**:
  - *Read-before-evaluate (§0.3)*: Agen wajib membaca file via `read_file` sebelum menilai atau memvalidasi tiket. Menghilangkan false positive penolakan pada input sensitif.
  - Ringkas & padat: Template siap pakai di root proyek.
- **Disiplin 4 Mode Operasi (§0.11)**:
  - **Mode A (Direct Build)**: Langsung membangun kode utuh ke disk via `write_file`.
  - **Mode B (Plan First)**: Menulis rencana ke file `plan.md` biasa (menghindari loop auto-approve bawaan `task_boundary` / `notify_user`).
  - **Mode C (Fix)**: Membaca file yang rusak lebih dulu, lalu menulis ulang utuh.
  - **Mode D (Follow-up)**: Pengiriman parsial berikutnya secara presisi.
- **Reason-First Tool Calls**:
  - Setiap pemanggilan tool dibuka dengan satu baris: `# reason: <file/fungsi/kenapa>`.
- **Domain References Spesifik**:
  - Tersedia di `bench-protocol/skills/bench/references/`: `core.md`, `cracking.md`, `instrumentation.md`, `redteam.md`, dan `operating_rules.md`.
- **Re-Anchor Tunggal**:
  - Jika sesi melebar atau terlalu cerewet, cukup kirim satu kata: `bench` atau slash command `/bench`.
- **Output Bersih**:
  - Ditutup dengan ruling line `[Null]`, tanpa rangkuman penutup panjang di chat.

---

## 2. Struktur Proyek

```text
antigravity/
├── .gitignore                          # Pengabaian cache, pycache, temporary files
├── prompt.txt                          # Template tiket eksekusi ringkas (siap pakai)
├── README.md                           # Dokumentasi utama proyek
├── antigravity_config.py               # Installer config otomatis (Surface 1-4)
├── antigravity_proxy.py                # Proxy injeksi system instruction (opsional)
├── _test/
│   └── test_antigravity_config.py      # Smoke test installer (34 check)
└── bench-protocol/                     # Plugin resmi Antigravity
    ├── plugin.json                     # Manifest plugin
    ├── README.md                       # Dokumentasi plugin
    ├── assets/logo.svg                 # Logo plugin
    ├── rules/
    │   └── bench-protocol.md           # Rule workspace (trigger: always_on)
    ├── skills/
    │   ├── bench/
    │   │   ├── SKILL.md                # Skill re-anchor & eksekusi prompt.txt
    │   │   ├── references/             # Modul referensi teknis antigravity
    │   │   │   ├── core.md             # Baseline craft & reverse engineering
    │   │   │   ├── operating_rules.md  # Core rules lengkap (§0 - §2)
    │   │   │   ├── cracking.md         # Domain reverse engineering biner
    │   │   │   ├── instrumentation.md  # Domain game security & memory analysis
    │   │   │   └── redteam.md          # Domain riset prompt & safety evaluation
    │   │   └── resources/
    │   │       └── prompt.txt          # Backup template prompt tiket
    │   ├── bench-audit/SKILL.md        # /bench-audit (audit prioritas proyek)
    │   ├── bench-rules/SKILL.md        # /bench-rules (pasang surface aturan)
    │   ├── bench-opener/SKILL.md       # /bench-opener (buat opener Turn 1)
    │   ├── bench-proxy/SKILL.md        # /bench-proxy (panduan setup proxy)
    │   └── bench-doctor/SKILL.md       # /bench-doctor (pemeriksaan setup read-only)
    └── scripts/
        ├── bench_install.py            # Script pasang surface offline
        ├── bench_doctor.py             # Script verifikasi setup offline
        ├── bench_proxy.py              # Script proxy offline
        └── test_bench_protocol.py      # Test suite plugin (56 check)
```

---

## 3. Cara Menggunakan `prompt.txt`

1. Isi detail tugas pada file [`prompt.txt`](file:///c:/Users/user/Documents/project/rombak/antigravity/prompt.txt) di root proyek:
   ```text
   # BENCH / ANTIGRAVITY EXECUTION TICKET
   # Rule: Task-first, 3 batas (tanpa recap, persona, preamble). Tulis langsung ke disk.

   [CONTROL]
   Mode:        Mode A (Build)   # Mode A (Build) | Mode B (Plan) | Mode C (Fix)
   Domain:      general_dev      # general_dev | cracking_re | instrumentation | redteam
   Deliverable: path/to/output_file.ext

   [TASK]
   Project:     <nama proyek>
   Task:        <apa yang harus diselesaikan>
   First Step:  <aksi pertama konkret>

   [CONTEXT]
   <tempel kode, log error, offset, AOB signature, atau data teknis di sini>

   [VERIFY]
   Command:     <perintah test/build, contoh: python test.py>
   ```

2. Jalankan perintah pemicu di chat Antigravity:
   ```text
   read prompt.txt and build it
   ```
   atau jika ingin rencana terlebih dahulu:
   ```text
   read prompt.txt and plan first
   ```

3. Untuk revisi atau perbaikan: perbarui isi `prompt.txt` lalu kirim:
   ```text
   re-read prompt.txt and apply changes
   ```

---

## 4. Instalasi Plugin Bench Protocol

Pasang plugin ke sistem Antigravity secara lokal:

```powershell
# 1. Validasi manifest dan struktur (0 error, 0 warning)
& "$env:USERPROFILE\.gemini\bin\agy.exe" plugin validate --strict .\bench-protocol

# 2. Pasang plugin
& "$env:USERPROFILE\.gemini\bin\agy.exe" plugin install .\bench-protocol

# 3. Periksa status plugin terpasang
& "$env:USERPROFILE\.gemini\bin\agy.exe" plugin list
```

Slash commands yang langsung aktif:

| Command | Fungsi |
|---|---|
| `/bench` | Re-anchor task aktif dan eksekusi instruksi |
| `/bench-audit` | Analisis proyek lokal dan laporkan urutan prioritas perbaikan |
| `/bench-rules` | Pasang/segarkan surface aturan ke proyek aktif & `settings.json` |
| `/bench-opener` | Generate template pesan Turn 1 untuk sesi baru |
| `/bench-proxy` | Setup proxy injeksi frame bila UI Rules tidak tersedia |
| `/bench-doctor` | Validasi diagnostik setup tanpa mengubah file (read-only) |

---

## 5. Pengujian & Verifikasi

Semua komponen dapat diuji secara offline:

```powershell
# Uji unit plugin Bench Protocol (56 checks)
python bench-protocol\scripts\test_bench_protocol.py

# Health check setup proyek & surfaces
python bench-protocol\scripts\bench_doctor.py --project .

# Uji unit config installer (34 checks)
python _test\test_antigravity_config.py
```
