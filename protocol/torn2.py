"""torn2.py — TORN v0.2: chained records.

v0.1 resynchronizes after corruption but is blind to a CLEAN
DELETION: remove one intact record and every remaining CRC
still checks out — the loss is invisible.

v0.2 adds two fields per record:
  SEQ  — uint32 LE, monotonically increasing per file
  LINK — uint32 LE, CRC value of the PREVIOUS record (0 = head)

Now the reader classifies losses v0.1 can't see:
  seq gap + zero skipped bytes between records -> clean_deletion
  seq gap + corrupt bytes between           -> corruption_loss
  first found record has seq>0 / link!=0    -> head_loss
  link mismatch with intact neighbours      -> link_broken

Still a journal: no index, no dedup, append-only.

    torn2.append(path, {...})   # writer finds last record, links
    torn2.scan(path)            # + .stats['chain'] diagnostics
"""

import json
import struct
import zlib

MAGIC = b'\xc7\x3f'
VER = 2
T_JSON, T_RAW = 1, 2
HDR = struct.Struct('<2sBBIII')  # magic, ver, type, seq, link, len


def _frame(payload, rtype, seq, link):
    head = struct.pack('<BBIII', VER, rtype, seq, link, len(payload))
    crc = zlib.crc32(head + payload)
    return MAGIC + head + payload + struct.pack('<I', crc)


def _last_record(path):
    """Backward scan for the last valid record -> (seq, crc) or (0, 0)."""
    try:
        with open(path, 'rb') as f:
            f.seek(0, 2)
            n = f.tell()
            f.seek(max(0, n - 65536))
            tail = f.read()
    except FileNotFoundError:
        return 0, 0
    base = max(0, n - 65536)
    pos = 0
    while True:
        i = tail.rfind(MAGIC, 0, len(tail) if pos == 0 else pos)
        if i < 0:
            return 0, 0
        abs_i = base + i
        if abs_i + HDR.size <= n:
            _, ver, rtype, seq, link, ln = HDR.unpack_from(tail, i)
            end = i + HDR.size + ln + 4
            if ver == VER and end == len(tail):
                crc_want, = struct.unpack_from('<I', tail, end - 4)
                if crc_want == zlib.crc32(tail[i + 2:end - 4]):
                    return seq, crc_want
        pos = i
        if pos == 0:
            return 0, 0


def append(path, obj):
    seq, link = _last_record(path)
    with open(path, 'ab') as f:
        f.write(_frame(json.dumps(obj, ensure_ascii=False).encode(),
                       T_JSON, seq + 1, link))


def append_raw(path, data: bytes):
    seq, link = _last_record(path)
    with open(path, 'ab') as f:
        f.write(_frame(data, T_RAW, seq + 1, link))


def scan(path):
    """(type, payload, offset) generator. .stats: v0.1 fields +
    'gaps' — list of (expected_seq, found_seq, offset, kind)."""
    with open(path, 'rb') as f:
        buf = f.read()
    stats = {'skipped': 0, 'torn_tail': 0, 'records': 0, 'gaps': []}
    pos, n = 0, len(buf)
    prev = None  # (seq, crc, end_offset) of last valid record
    span_dirty = 0  # bytes skipped since prev valid record
    while True:
        i = buf.find(MAGIC, pos)
        if i < 0:
            break
        span_dirty += i - pos
        stats['skipped'] += i - pos
        if i + HDR.size > n:
            stats['torn_tail'] = n - i
            break
        _, ver, rtype, seq, link, ln = HDR.unpack_from(buf, i)
        end = i + HDR.size + ln + 4
        if ver != VER:
            pos = i + 1
            continue
        if end > n:
            stats['torn_tail'] = n - i
            break
        crc_want, = struct.unpack_from('<I', buf, end - 4)
        if crc_want == zlib.crc32(buf[i + 2:end - 4]):
            stats['records'] += 1
            if prev is None:
                if seq != 1 or link != 0:
                    stats['gaps'].append((1, seq, i, 'head_loss'))
            else:
                pseq, pcrc, _ = prev
                if seq != pseq + 1:
                    kind = 'clean_deletion' if span_dirty == 0 else 'corruption_loss'
                    stats['gaps'].append((pseq + 1, seq, i, kind))
                if link != pcrc:
                    stats['gaps'].append(('link', pseq, i, 'link_broken'))
            prev = (seq, crc_want, end)
            span_dirty = 0
            yield rtype, buf[i + HDR.size:i + HDR.size + ln], i
            pos = end
        else:
            pos = i + 1
            span_dirty += 1
    scan.stats = stats


def read(path):
    for rtype, payload, _ in scan(path):
        if rtype == T_JSON:
            try:
                yield rtype, json.loads(payload)
            except Exception:
                yield rtype, payload
        else:
            yield rtype, payload
    read.stats = scan.stats


if __name__ == '__main__':
    import os
    p = 'protocol/demo2.torn'
    if os.path.exists(p):
        os.remove(p)

    for i in range(1, 7):
        append(p, {'kind': 'tick', 'seq_human': i})

    print('--- intact ---')
    list(read(p))
    print('stats:', read.stats)

    # CLEAN DELETION: cut record #3 out byte-perfectly.
    # v0.1 semantics = "all CRCs valid, 0 skipped" = BLIND.
    offs = [off for _, pl, off in scan(p)]
    o3, o4 = offs[2], offs[3]
    data = open(p, 'rb').read()
    open(p, 'wb').write(data[:o3] + data[o4:])
    print('--- clean deletion of record 3 ---')
    list(read(p))
    s = read.stats
    print('v0.1-style view: %d records, %d skipped — looks fine'
          % (s['records'], s['skipped']))
    print('v0.2 gaps:', s['gaps'])

    # CORRUPTION LOSS: flip a byte inside record 5.
    offs = [off for _, pl, off in scan(p)]
    o5 = offs[3]
    data = bytearray(open(p, 'rb').read())
    data[o5 + 20] ^= 0xFF
    open(p, 'wb').write(bytes(data))
    print('--- corrupt byte in record 5 ---')
    list(read(p))
    print('v0.2 sees:', read.stats)
