"""extract.py — fb2 -> clean text chapters for reading.

The collection is cp1251 fb2. Marginalia practice: read in
chunks, so split by sections and emit chapter files. The book
never leaves this machine (books/ is gitignored); chapter
extracts are working copies inside it — also never committed.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'books',
                   'Бегущий_по_лезвию_бритвы_с_z_library_sk,'
                   '_1lib_sk,_z_lib_sk_1.fb2')

raw = open(SRC, encoding='cp1251', errors='replace').read()
# body only; drop binary sections
body = raw[raw.find('<body>'):]
body = body[:body.find('<binary')] if '<binary' in body else body
# paragraphs: <p>...</p> — strip other tags inside
paras = re.findall(r'<p[^>]*>(.*?)</p>', body, re.S)
clean = []
for p in paras:
    t = re.sub(r'<[^>]+>', '', p)
    t = (t.replace('&lt;', '<').replace('&gt;', '>')
         .replace('&amp;', '&').replace('«', '«').strip())
    if t:
        clean.append(t)

# novel boundary: find where the first novel text proper starts
out = os.path.join(HERE, 'dick-androids.txt')
with open(out, 'w', encoding='utf-8') as f:
    f.write('\n\n'.join(clean))
print(f'paragraphs: {len(clean)}, chars: {sum(len(c) for c in clean)}')
print('first para:', clean[0][:90] if clean else 'EMPTY')
