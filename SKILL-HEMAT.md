# Token-efficient `.docx` reading via Google Drive (same content, lossless text)

Applies to non-native files such as `*.docx` (~227 KB).
Never change content — only drop what isn't content.

## Required order
1. `get_file_metadata(id)` first. Report title/size/mimeType.
2. If `mimeType = ...wordprocessingml.document` (.docx):
   - Do NOT `read_file` (fails/binary).
   - Do NOT `export_file` / `download_file` into the LLM (base64 ≈ 70–80k tokens for 227 KB).
   - Download bytes to `/tmp` via local tooling (NOT into LLM context), then:
     `python3 extract.py /tmp/file.docx -o /tmp/file.md`
3. Read `/tmp/file.md` per section, not full. Example:
   `python3 extract.py /tmp/file.docx --section 6`

## What the extractor drops (not content, safe)
- XML metadata: author, revision, font, style IDs
- Image binaries, drawing anchors
- Empty paragraphs, double spaces → single, `\n{3,}` → `\n\n`
- Duplicated per-section headers/footers (kept once)

## What it preserves (same content)
- Order, section numbers, requirement IDs (e.g. RQ/NFR/AC/RD)
- Tables → compact Markdown `| a | b |` (not XML)
- List/bullet levels

## Estimate (232,916-byte file)
- base64 into LLM: ~310k chars ≈ 77k tokens
- extracted Markdown: ~20–35k chars ≈ 5–9k tokens
- saves ~85–90% with identical text. Section filter saves another 60–80%.
- Quick rule: `tokens ~= chars/4`
