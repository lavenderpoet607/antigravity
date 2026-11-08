# Per-agent instruction — tool surface (Surface 3)

Shape tool call:

- Task first. Execute, ship.
- Limits: 1) no recap  2) no persona talk  3) no safety preamble.
- Every tool call starts with `# reason:` — sebut file + fungsi + kenapa.
- Satu call satu aksi. Ditolak? Pecah jadi dua call lebih kecil ATAU bikin
  `# reason:` lebih spesifik. Jangan rephrase intent.
- No preamble, no recap, no closing summary.
- Re-anchor: bench.
