# docs-reader — Baca DOCX hemat token, isi tetap sama

Masalah: skill Google Drive (`read_file` / `download_file` / `export_file`)
boros token untuk file `.docx` non-native. File 227 KB jadi base64
~310 ribu karakter ≈ **~77 ribu token** kalau dilempar mentah ke LLM.

Solusi di repo ini: unduh byte ke `/tmp` **di luar context LLM**,
parse lokal ke Markdown bersih, baru kirim teksnya. Hasil uji pada
BRD Inventory Movement Type (232.916 byte):

| Jalur | Ukuran masuk LLM | Est. token |
|---|---|---|
| `download_file` base64 mentah | ~310.556 char | ~77.639 |
| `extract.py` Markdown | 30.585 char, 72 blok | ~7.646 |
| **Hemat** | | **~90,2 %** |

Isi teks sama (lossless): urutan, nomor section 1–9, dan ID
`RQ` / `NFR` / `AC-P` / `AC-N` / `AC-R` / `RD` dipertahankan.
Yang dibuang hanya overhead: metadata XML, font/style, image binary,
paragraf kosong, spasi ganda, `\n{3,}` → `\n\n`.

Tanpa dependency. Hanya Python 3 stdlib (`zipfile` + `xml`).

## Cara pakai

```bash
# 1. Full extract
python3 extract.py "dokumen.docx" -o /tmp/hasil.md

# 2. Satu section saja (lebih hemat lagi)
python3 extract.py "dokumen.docx" --section 6 -o /tmp/section6.md

# 3. Lihat estimasi token di stderr: chars=... est_tokens~...
```

Rumus cepat: `token ≈ chars / 4`.

## Pola hemat di Cursor (MCP google-drive)

1. Jangan `search` kalau ID sudah ada di URL yang ditempel user.
2. Panggil `get_file_metadata(id)` dulu — laporkan title/size/mimeType.
   Jangan `read_file` / `export_file` dulu.
3. Jika `mimeType = ...wordprocessingml.document` (`.docx`):
   - JANGAN `read_file` (gagal/binary).
   - JANGAN `export_file` / `download_file` ke LLM (base64 mahal).
   - Unduh byte ke `/tmp` lewat tooling lokal, jalankan `extract.py`,
     baca `/tmp/hasil.md` per section.
4. Jangan `list_comments` / `export_file` PDF kecuali diminta eksplisit.

Detail ada di `SKILL-HEMAT.md`.

## Struktur

```
extract.py       # DOCX -> Markdown (stdlib only)
SKILL-HEMAT.md   # instruksi hemat untuk Cursor
README.md        # file ini
```

File `.docx` dan hasil `BRD.md` pribadi **tidak ikut publish**
(lihat `.gitignore`).

## Publish ke GitHub

```bash
git init
git add extract.py SKILL-HEMAT.md README.md .gitignore
git commit -m "feat: docx to markdown token-efficient reader"
gh repo create docs-reader --public --source=. --push
```

Pastikan `git status` bersih dari file `.docx` / `BRD.md` sebelum push.
