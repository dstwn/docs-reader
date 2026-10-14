# docs-reader

[![Python 3](https://img.shields.io/badge/python-3.x-blue)](https://www.python.org/)
[![Zero dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen)](#)
[![Saves ~90% tokens](https://img.shields.io/badge/tokens_-90%25-orange)](#benchmark)
[![License: MIT](https://img.shields.io/github/license/dstwn/docs-reader)](LICENSE)

**Read `.docx` files with ~90% fewer LLM tokens. Same text, zero dependencies.**

Google Drive agent skills (`read_file` / `download_file` / `export_file`)
are token-expensive for non-native `.docx` files: a 227 KB document becomes
~310K chars of base64 ≈ **~77K tokens** when passed raw to an LLM.
`docs-reader` downloads the bytes *outside* the LLM context, parses them
locally into clean Markdown, and feeds only the text in — about **~7.6K
tokens** for the same document.

## Quickstart

No install. Python 3 only, stdlib only (`zipfile` + `xml`).

```bash
git clone https://github.com/dstwn/docs-reader.git
cd docs-reader

# Full extract
python3 extract.py "document.docx" -o /tmp/out.md

# One section only (saves even more)
python3 extract.py "document.docx" --section 6 -o /tmp/section6.md
```

Token estimate is printed to stderr on every run:

```
-- chars=30585 est_tokens~7646 blocks=72
```

Quick rule of thumb: `tokens ≈ chars / 4`.

## Usage

```
python3 extract.py [-h] [-o OUT] [--section SECTION] docx
```

| Flag | Effect |
|---|---|
| `-o / --out` | Write Markdown file (default: stdout) |
| `--section N` | Keep only the numbered heading starting with `N` (e.g. `--section 6`) |

## How it works

Lossless text — only overhead is removed:

**Stripped (not content, safe to drop):**
- XML metadata: author, revisions, fonts, style IDs
- Image binaries and drawing anchors
- Empty paragraphs, double spaces → single, `\n{3,}` → `\n\n`
- Duplicated per-section headers/footers (kept once)

**Preserved (content stays identical):**
- Order, numbered sections, requirement IDs
- Tables → compact Markdown (`| a | b |` instead of verbose XML)
- List / bullet nesting levels

## Use with AI agents (Cursor + Google Drive MCP)

`read_file` fails on `.docx` (binary, not a native Google Doc) and
`download_file` / `export_file` burn tens of thousands of tokens on base64.
Use this pattern instead:

1. Skip `search` when the file ID is already in the user's pasted URL.
2. Call `get_file_metadata(id)` first — report title/size/mimeType only.
   Do not call `read_file` / `export_file` yet.
3. If `mimeType = ...wordprocessingml.document` (`.docx`):
   - Do NOT `read_file` (fails/binary).
   - Do NOT send `export_file` / `download_file` output to the LLM.
   - Download bytes to `/tmp` via local tooling and run:
     `python3 extract.py /tmp/file.docx -o /tmp/file.md`
4. Read `/tmp/file.md` per section, not the whole file.
5. Don't `list_comments` / export PDF unless explicitly asked.

## Benchmark

Real run on a 232,916-byte BRD document:

| Path | Into the LLM | Est. tokens |
|---|---|---|
| `download_file` raw base64 | ~310,556 chars | ~77,639 |
| `extract.py` Markdown (72 blocks) | 30,585 chars | ~7,646 |
| **Saved** | | **~90.2%** |

Section filtering (`--section 9` → 2,040 chars ≈ 510 tokens) saves another
60–80% on top when only one part is needed.

## Contributing

Issues and PRs welcome. Keep it stdlib-only so the tool stays
copy-paste usable anywhere.

## License

[MIT](LICENSE)
