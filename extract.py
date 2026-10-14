#!/usr/bin/env python3
"""DOCX -> Markdown hemat-token, isi sama (lossless teks).
Hanya stdlib: zipfile + xml. Buang yang boros token tapi bukan isi:
- metadata (author, revision, font, style XML)
- image binaries, drawing anchors
- empty paragraph, spasi ganda, newline triple
- header/footer duplikat per section (ambil sekali)
Pertahankan: urutan, nomor 1-9, tabel sebagai markdown compact, list.
Pakai: python3 extract.py input.docx -o out.md [--section 6]
"""
import sys, zipfile, re, argparse
import xml.etree.ElementTree as ET

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def para_text(p):
    # gabung w:t dalam paragraf, jaga tab/line-break sebagai spasi/baris
    parts = []
    for el in p.iter():
        if el.tag == W + 't':
            parts.append(el.text or '')
        elif el.tag in (W + 'tab',):
            parts.append(' ')
        elif el.tag == W + 'br':
            parts.append('\n')
    # normalisasi spasi dalam paragraf (hemat token, isi sama)
    t = ''.join(parts)
    t = re.sub(r'[ \t]+', ' ', t).strip()
    return t

def is_heading(p):
    pPr = p.find('w:pPr', NS)
    if pPr is None:
        return 0
    st = pPr.find('w:pStyle', NS)
    if st is None:
        return 0
    v = st.get(W + 'val', '')
    m = re.match(r'Heading([1-6])', v, re.I)
    if m:
        return int(m.group(1))
    if v.lower().startswith('heading'):
        return 1
    return 0

def is_list(p):
    pPr = p.find('w:pPr', NS)
    if pPr is None:
        return None
    num = pPr.find('w:numPr', NS)
    if num is None:
        return None
    ilvl = num.find('w:ilvl', NS)
    return int(ilvl.get(W + 'val', 0)) if ilvl is not None else 0

def extract_docx(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml')
    root = ET.fromstring(xml)
    body = root.find('w:body', NS)
    out = []  # (kind, level, text) kind: h,p,li,table
    for child in body:
        if child.tag == W + 'p':
            t = para_text(child)
            if not t:
                continue  # buang paragraf kosong (hemat, isi sama)
            hl = is_heading(child)
            if hl:
                out.append(('h', hl, t))
                continue
            lv = is_list(child)
            if lv is not None:
                out.append(('li', lv, t))
            else:
                out.append(('p', 0, t))
        elif child.tag == W + 'tbl':
            rows = []
            for tr in child.findall('w:tr', NS):
                cells = []
                for tc in tr.findall('w:tc', NS):
                    ps = [' '.join(para_text(p) for p in tc.findall('w:p', NS) if para_text(p))]
                    cells.append(' '.join(ps).strip())
                # buang baris fully-empty
                if any(c for c in cells):
                    rows.append(cells)
            if rows:
                out.append(('table', 0, rows))
    return out

def to_markdown(blocks):
    lines = []
    for kind, lv, v in blocks:
        if kind == 'h':
            lines.append('#' * min(lv, 6) + ' ' + v)
            lines.append('')
        elif kind == 'li':
            lines.append('  ' * min(lv, 4) + '- ' + v)
        elif kind == 'p':
            lines.append(v)
            lines.append('')
        elif kind == 'table':
            rows = v
            w = max(len(r) for r in rows)
            rows = [r + [''] * (w - len(r)) for r in rows]
            lines.append('| ' + ' | '.join(rows[0]) + ' |')
            lines.append('|' + '|'.join(['---'] * w) + '|')
            for r in rows[1:]:
                lines.append('| ' + ' | '.join(r) + ' |')
            lines.append('')
    md = '\n'.join(lines)
    md = re.sub(r'\n{3,}', '\n\n', md).strip() + '\n'
    return md

def est_tokens(s):
    return len(s) // 4  # aturan cepat chars/4

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('docx')
    ap.add_argument('-o', '--out', default='')
    ap.add_argument('--section', default='', help='filter mis. "6" untuk section 6 saja')
    a = ap.parse_args()
    blocks = extract_docx(a.docx)
    if a.section:
        # filter sederhana: heading diawali nomor section
        keep, on = [], False
        for b in blocks:
            if b[0] == 'h' and re.match(r'^' + re.escape(a.section) + r'[\.\s]', b[2]):
                on = True
            elif b[0] == 'h' and re.match(r'^\d+[\.\s]', b[2]):
                on = False
            if on or not any(x[0] == 'h' for x in blocks):
                keep.append(b)
        # fallback: kalau tidak ketemu heading bernomor, kirim semua
        blocks = keep or blocks
    md = to_markdown(blocks)
    if a.out:
        open(a.out, 'w', encoding='utf-8').write(md)
    else:
        sys.stdout.write(md)
    print(f'-- chars={len(md)} est_tokens~{est_tokens(md)} blocks={len(blocks)}', file=sys.stderr)

if __name__ == '__main__':
    main()
