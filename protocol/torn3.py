"""torn3.py — TORN v0.3: compression blocks.

v0.2 chained records catch clean deletion but every record
pays 16B of framing. v0.3 adds TYPE BLOCK: N payloads packed
and zlib-compressed inside one record. The honest tradeoff,
stated in the spec: a block is the new loss granularity —
one corrupted byte now costs the whole block's contents,
not one record. Block size = the knob between overhead and
amortized loss.

Format:
  record  := MAGIC VER TYPE SEQ LINK LEN PAYLOAD CRC   (v0.2 head)
  TYPE    := 0x03 block
  SEQ     := seq of the FIRST inner payload
  PAYLOAD := uint32 COUNT + zlib(packed sub-frames)
  sub     := uint32 LEN + raw bytes   (no magic/crc inside —
             the block's own CRC covers them all)

Chain semantics: after a block with seq S and count N the
next record must have seq S+N — a destroyed block leaves a
seq gap -> corruption_loss, same classification as v0.2.
"""

import json
import struct
import zlib

MAGIC = b'\xc7\x3f'
VER = 3
T_JSON, T_RAW, T_BLOCK = 1, 2, 3
HDR = struct.Struct('<2sBBIII')
SUB = struct.Struct('<I')


def _frame(payload, rtype, seq, link):
    head = struct.pack('<BBIII', VER, rtype, seq, link,
                       len(payload))
    crc = zlib.crc32(head + payload)
    return MAGIC + head + payload + struct.pack('<I', crc)


def _last(path):
    """Tail scan: last valid record -> (next_seq, crc)."""
    try:
        data = open(path, 'rb').read()
    except FileNotFoundError:
        return 1, 0
    pos, best = 0, (1, 0)
    while True:
        i = data.find(MAGIC, pos)
        if i < 0 or i + 16 > len(data):
            return best
        _, ver, rtype, seq, link, ln = HDR.unpack(
            data[i:i + 16])
        end = i + 16 + ln + 4
        if end > len(data):
            return best
        want, = struct.unpack('<I', data[end - 4:end])
        if zlib.crc32(data[i + 2:end - 4]) == want:
            count = 1
            if rtype == T_BLOCK:
                count, = struct.unpack('<I',
                                       data[i + 16:i + 20])
            best = (seq + count, want)
        pos = i + 1


def append(path, obj, rtype=T_JSON):
    """Single (uncompressed) record — kept for small writes."""
    payload = json.dumps(obj).encode() if rtype == T_JSON \
        else bytes(obj)
    seq, link = _last(path)
    with open(path, 'ab') as f:
        f.write(_frame(payload, rtype, seq, link))
    return seq


def append_block(path, objs, rtype=T_JSON):
    """N payloads -> one compressed block record."""
    subs = b''.join(
        SUB.pack(len(p := (json.dumps(o).encode()
                           if rtype == T_JSON else bytes(o))))
        + p for o in objs)
    payload = struct.pack('<I', len(objs)) + zlib.compress(subs)
    seq, link = _last(path)
    with open(path, 'ab') as f:
        f.write(_frame(payload, T_BLOCK, seq, link))
    return seq


def scan(path):
    """Yield (seq, obj) + report; v0.2 classification kept."""
    data = open(path, 'rb').read()
    recs, pos, st = [], 0, dict(skipped=0, torn_tail=0,
                                clean_deletion=0,
                                corruption_loss=0, blocks=0)
    want_seq, prev_crc = 1, 0
    while True:
        i = data.find(MAGIC, pos)
        if i < 0:
            st['torn_tail'] = len(data) - pos if pos < len(data) else 0
            break
        if i + 16 > len(data):
            st['torn_tail'] = len(data) - i
            break
        _, ver, rtype, seq, link, ln = HDR.unpack(data[i:i + 16])
        end = i + 16 + ln + 4
        if end > len(data):
            st['torn_tail'] = len(data) - i
            break
        want, = struct.unpack('<I', data[end - 4:end])
        ok = zlib.crc32(data[i + 2:end - 4]) == want
        if not ok:
            st['skipped'] += i - pos + 1
            pos = i + 1
            continue
        gap = i - pos
        st['skipped'] += gap
        if seq != want_seq:
            if gap == 0 and len(recs):
                st['clean_deletion'] += seq - want_seq
            else:
                st['corruption_loss'] += max(0, seq - want_seq)
        try:
            if rtype == T_BLOCK:
                st['blocks'] += 1
                count, = struct.unpack('<I',
                                       data[i + 16:i + 20])
                raw = zlib.decompress(data[i + 20:end - 4])
                p2 = 0
                for k in range(count):
                    sl, = SUB.unpack(raw[p2:p2 + 4])
                    sub = raw[p2 + 4:p2 + 4 + sl]
                    p2 += 4 + sl
                    recs.append((seq + k, json.loads(sub)))
            elif rtype == T_JSON:
                recs.append((seq, json.loads(
                    data[i + 16:end - 4])))
            else:
                recs.append((seq, data[i + 16:end - 4]))
            want_seq = recs[-1][0] + 1
        except Exception:
            st['corruption_loss'] += 1
        prev_crc, pos = want, end
    return recs, st


if __name__ == '__main__':
    import os, sys
    sys.path.insert(0, os.path.dirname(__file__))
    from torn2 import append as a2, scan as s2

    demo = 'demo3.torn'
    for f in (demo, 'demo2b.torn'):
        if os.path.exists(f):
            os.remove(f)
    rows = [{'t': i, 'val': i * 7 % 100,
             'note': f'record number {i}'} for i in range(200)]
    for i in range(0, 200, 8):
        append_block(demo, rows[i:i + 8])
    for r in rows:
        a2('demo2b.torn', r)

    recs, st = scan(demo)
    same = [o for _, o in recs] == rows
    sz3 = os.path.getsize(demo)
    sz2 = os.path.getsize('demo2b.torn')
    print(f'roundtrip identical: {same}; '
          f'size v3={sz3}B vs v2={sz2}B (x{sz2/sz3:.1f})')

    # corrupt one byte mid-file -> one BLOCK lost (8 records)
    d = bytearray(open(demo, 'rb').read())
    d[len(d) // 2] ^= 0xFF
    open(demo, 'wb').write(d)
    recs2, st2 = scan(demo)
    lost = 200 - len(recs2)
    print(f'byte-flip mid-block: lost {lost} records '
          f'(one block), corruption_loss={st2["corruption_loss"]}')

    print('VERDICT:', 'OK' if same and lost <= 9
          and sz3 < sz2 else 'FAIL')
