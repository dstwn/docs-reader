---
name: drive-docx-reader
description: Read .docx files from Google Drive with ~90% fewer tokens. Use when reading Word documents via Google Drive MCP tools, when read_file fails on binary .docx, or when download/export output is too large for context. Parses locally to clean Markdown instead of base64.
---

# Read `.docx` without burning tokens

`read_file` fails on `.docx` (binary, not a native Google Doc).
`download_file` / `export_file` into the LLM costs ~70–80k tokens for a
227 KB file (base64). Never send those outputs to the LLM.

## Required order

1. Skip `search` when the file ID is already in the user's pasted URL.
   Otherwise search with `exact_name` + `mime_type_filter`.
2. Call `get_file_metadata(id)` first — report title/size/mimeType only.
   Do not call `read_file` / `export_file` yet.
3. If `mimeType = ...wordprocessingml.document` (`.docx`):
   - Do NOT `read_file` (fails/binary).
   - Do NOT send `export_file` / `download_file` output to the LLM.
   - Download bytes to `/tmp` via local tooling (NOT into LLM context),
     then run the bundled extractor (stdlib only, no install):
     `python3 ../../extract.py /tmp/file.docx -o /tmp/file.md`
4. Read `/tmp/file.md` per section, not the whole file:
   `python3 ../../extract.py /tmp/file.docx --section 6`
5. Don't `list_comments` / export PDF unless explicitly asked.

## What the extractor drops (not content, safe)

- XML metadata: author, revision, font, style IDs
- Image binaries, drawing anchors
- Empty paragraphs, double spaces → single, `\n{3,}` → `\n\n`
- Duplicated per-section headers/footers (kept once)

## What it preserves (same content, lossless text)

- Order, section numbers, requirement IDs
- Tables → compact Markdown `| a | b |` (not XML)
- List/bullet levels

## Token math

- base64 into LLM: ~310k chars ≈ 77k tokens (232,916-byte file)
- extracted Markdown: ~30k chars ≈ 7.6k tokens → saves ~90%
- section filter saves another 60–80%. Quick rule: `tokens ~= chars/4`
