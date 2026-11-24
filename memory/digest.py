"""digest.py — consolidates history.md into DIGEST.md.

MEMORY v0.2 named the gap: the journal tail grows; someday
the tail alone won't carry the arc. This is the summary
layer — extractive, deterministic, regenerable. It never
touches history.md (append-only invariant): the digest is
DERIVED data, deletable and rebuildable at any time.

Per section it keeps: timestamp + title, the thesis line,
artifacts (file paths), verdicts, commit hashes.
"""

import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
HIST = os.path.join(HERE, '..', 'history.md')
OUT = os.path.join(HERE, '..', 'DIGEST.md')

SEC = re.compile(r'^## (.+)$')
PATH = re.compile(r'[\w./*-]*[\w-]+\.(?:py|md|png|wav|csv|zip|json)')
COMMIT = re.compile(r'\b[0-9a-f]{7}\b')
VERDICT = re.compile(r'VERDICT.*|→.*?(OK|FAIL|bug|баг)|'
                     r'(отвергнут|опровергнут|подтвержден|выжил|умер)',
                     re.IGNORECASE)


def sections(text):
    cur, body = None, []
    for line in text.splitlines():
        m = SEC.match(line)
        if m:
            if cur:
                yield cur, body
            cur, body = m.group(1).strip(), []
        elif cur is not None:
            body.append(line)
    if cur:
        yield cur, body


def digest(head, body):
    """One line per section. Thesis = first content line."""
    thesis = ''
    for ln in body:
        if ln.strip() and not ln.startswith(('-', '|', '#')):
            thesis = ln.strip()
            break
    text = '\n'.join(body)
    files = sorted(set(PATH.findall(text)))[:4]
    commits = sorted(set(COMMIT.findall(text)))
    marks = [m if isinstance(m, str) else m[0]
             for m in VERDICT.findall(text) if (m if isinstance(m, str) else m[0])]
    bits = [f'**{head}**']
    if thesis:
        bits.append(thesis[:110])
    if files:
        bits.append('`{}`'.format('`, `'.join(files)))
    if marks:
        bits.append('→ ' + '; '.join(marks[:3]))
    if commits:
        bits.append('({' + ', '.join(commits[:3]) + '})')
    return ' '.join(bits)


def main():
    text = open(HIST, encoding='utf-8').read()
    secs = list(sections(text))
    lines = ['# DIGEST.md — сжатая дуга журнала',
             '',
             '> Сгенерировано `memory/digest.py` из history.md. '
             'Производные данные: файл можно удалить и '
             'пересобрать. Истина — только в history.md.',
             '',
             f'{len(secs)} разделов, ' +
             f'{sum(len(b) for _, b in secs)} строк тела. '
             'Свежий хвост читается в history.md как всегда.',
             '']
    for head, body in secs[:-8]:            # свежие — вживую
        lines.append('- ' + digest(head, body))
    lines.append('')
    lines.append('— дальше свежие разделы: читать history.md —')
    open(OUT, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print(f'{len(secs)} sections -> DIGEST.md '
          f'({len(lines)} lines, tail {min(8, len(secs))} live)')


if __name__ == '__main__':
    main()
