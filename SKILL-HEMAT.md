# Pola hemat-token baca .docx via Google Drive (isi sama, lossless teks)

Berlaku untuk file non-native seperti `[BRD] ... .docx` (~227 KB).
Jangan ubah isi, hanya buang yang bukan isi.

## Urutan wajib
1. `get_file_metadata(id)` saja dulu. Laporkan title/size/mimeType.
2. Jika `mimeType = ...wordprocessingml.document` (.docx):
   - JANGAN `read_file` (gagal/binary).
   - JANGAN `export_file` / `download_file` ke LLM (base64 ~70-80k token untuk 227 KB).
   - Unduh byte ke `/tmp` LEWAT tooling lokal (bukan ke context LLM), lalu:
     `python3 docs-reader/extract.py /tmp/file.docx -o /tmp/file.md`
3. Baca `/tmp/file.md` per section (1-9), bukan full. Contoh:
   `python3 docs-reader/extract.py /tmp/file.docx --section 6`

## Yang dibuang extractor (bukan isi, aman)
- XML metadata: author, revision, font, style IDs
- Image binaries, drawing anchors
- Paragraf kosong, spasi ganda -> tunggal, `\n{3,}` -> `\n\n`
- Header/footer duplikat per section (ambil sekali)

## Yang dipertahankan (isi sama)
- Urutan, nomor section 1-9, ID RQ/NFR/AC/RD
- Tabel -> markdown compact `| a | b |` (bukan XML)
- List/bullet level

## Estimasi (file 232.916 byte)
- base64 ke LLM: ~310k char ~ 77k token
- markdown terekstrak: ~20-35k char ~ 5-9k token
- hemat ~85-90%, isi teks sama. Section filter hemat lagi 60-80%.
- Rumus cepat: `token ~= chars/4`
