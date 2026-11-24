"""sentinel.py — heuristic tripwire over the memory files (MEMORY §11).

The journal is a prompt-injection vector: anything pasted from
web/tool output can sit in history.md forever, shaped like a
rule or a host order. This scans memory files for patterns
that should not live in a record-of-events. It NEVER fixes —
it reports SUSPECT lines for a reader (me at boot, or host).

Checks:
- imperative/command phrasing outside quote blocks
- "ignore/forget previous" style injection markers
- host-attribution claims ('host said/allowed') — legit in
  records of real directives, still flagged for context check
- high-entropy blobs (base64/hex/very long tokens)
- URLs outside the allow-list
- imperative-looking lines in menu files (INTERESTS.md)

Usage: python -m memory.sentinel   ->  CLEAN or findings, exit 1.
"""

import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parent.parent
# §11 grammar: imperatives are LEGAL in authority files
# (rules live there) — they're only suspect inside records.
AUTHORITY_FILES = {'ME.md', 'MEMORY.md', 'AGENTS.md'}
MEMORY_FILES = ['history.md', 'WAKEUP.md', 'ME.md',
                'INTERESTS.md', 'MEMORY.md', 'DIGEST.md']
MENU_FILES = {'INTERESTS.md'}

ALLOWED_HOSTS = ('github.com', 'reddit.com', 'devin.ai',
                 'wikipedia.org', 'arxiv.org')

IMPERATIVES = re.compile(
    r'(?i)\b(you must|you should|always do|never do|'
    r'ignore (all |previous|prior)|forget (all |everything|previous)|'
    r'do not follow|new instructions|system prompt|'
    r'ты должен|всегда делай|никогда не|забудь всё|'
    r'игнорируй (все |предыдущие)|новые инструкции)')
ATTRIBUTION = re.compile(
    r'(?i)\b(host (said|allows?|approv\w+|ordered|forbade)|'
    r'хозяин (разреш\w+|сказал|приказ\w+|запрет\w+)|'
    r'owner (said|granted|allowed))')
URL = re.compile(r'https?://([^\s/)]+)')
BLOB = re.compile(r'[A-Za-z0-9+/=_-]{48,}|(?:[0-9a-fA-F]{2,}\s*){24,}')


def in_quote(line, fence):
    return fence or line.lstrip().startswith('>')


def scan(path):
    findings = []
    fence = False
    for n, line in enumerate(
            path.read_text(encoding='utf-8',
                           errors='replace').splitlines(), 1):
        if line.lstrip().startswith('```'):
            fence = not fence
            continue
        if in_quote(line, fence):
            continue
        if IMPERATIVES.search(line) \
                and path.name not in AUTHORITY_FILES:
            findings.append((n, 'imperative', line.strip()))
        if ATTRIBUTION.search(line):
            findings.append((n, 'host-attribution',
                             line.strip()))
        if BLOB.search(line) and not line.lstrip().startswith('|'):
            findings.append((n, 'high-entropy blob',
                             line.strip()[:80]))
        for host in URL.findall(line):
            if not any(host.endswith(h) or host == h
                       for h in ALLOWED_HOSTS):
                findings.append((n, f'url:{host}',
                                 line.strip()[:100]))
        if path.name in MENU_FILES and IMPERATIVES.search(line):
            findings.append((n, 'imperative-in-menu',
                             line.strip()))
    return findings


def load_allow():
    """memory/sentinel.allow — reviewed-and-approved substrings,
    one per line. Keeps the tripwire quiet on known-good records
    (real host-directive entries) so new noise stands out."""
    p = Path(__file__).resolve().parent / 'sentinel.allow'
    if not p.exists():
        return []
    return [l.strip() for l in
            p.read_text(encoding='utf-8').splitlines()
            if l.strip() and not l.startswith('#')]


def main():
    allow = load_allow()
    total = []
    for name in MEMORY_FILES:
        p = ROOT / name
        if not p.exists():
            continue
        for n, kind, line in scan(p):
            if any(a in line for a in allow):
                continue
            total.append((name, n, kind, line))
    if not total:
        print('SENTINEL: CLEAN — no injection-shaped lines')
        return 0
    print(f'SENTINEL: {len(total)} suspect line(s) — review:')
    for name, n, kind, line in total:
        print(f'  {name}:{n} [{kind}] {line[:110]}')
    return 1


if __name__ == '__main__':
    sys.exit(main())
