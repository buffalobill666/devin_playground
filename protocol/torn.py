"""torn.py — реализация протокола TORN v0.1 (SPEC.md).

Устойчивый append-only журнал: записи с magic+crc, читатель
пересинхронизируется после любой порчи. API:

    torn.append(path, {'a': 1})      # json-запись
    torn.append_raw(path, b'...')    # raw-запись
    torn.read(path)                  # генератор (type, payload)
    torn.scan(path)                  # то же + статистика порчи
"""

import json
import struct
import zlib

MAGIC = b'\xc7\x3f'
VER = 1
T_JSON, T_RAW = 1, 2
HDR = struct.Struct('<2sBBI')  # magic, ver, type, len


def _frame(payload, rtype):
    head = struct.pack('<BBI', VER, rtype, len(payload))
    crc = zlib.crc32(head + payload)
    return MAGIC + head + payload + struct.pack('<I', crc)


def append(path, obj):
    with open(path, 'ab') as f:
        f.write(_frame(json.dumps(obj, ensure_ascii=False).encode(), T_JSON))


def append_raw(path, data: bytes):
    with open(path, 'ab') as f:
        f.write(_frame(data, T_RAW))


def scan(path):
    """Генератор: (type, payload, offset). Метаданные порчи — в .stats."""
    with open(path, 'rb') as f:
        buf = f.read()
    stats = {'skipped': 0, 'torn_tail': 0, 'records': 0}
    pos, n = 0, len(buf)
    while True:
        i = buf.find(MAGIC, pos)
        if i < 0:
            break
        stats['skipped'] += i - pos
        if i + HDR.size > n:
            stats['torn_tail'] = n - i
            break
        _, ver, rtype, ln = HDR.unpack_from(buf, i)
        end = i + HDR.size + ln + 4
        if ver != VER:
            pos = i + 1  # случайное совпадение magic — скан дальше
            continue
        if end > n:
            stats['torn_tail'] = n - i
            break
        crc_want, = struct.unpack_from('<I', buf, end - 4)
        crc_got = zlib.crc32(buf[i + 2:end - 4])
        if crc_want == crc_got:
            stats['records'] += 1
            yield rtype, buf[i + HDR.size:i + HDR.size + ln], i
            pos = end
        else:
            pos = i + 1  # crc не сошёлся — ложный magic, скан дальше
    scan.stats = stats


def read(path):
    """Итератор (type, payload). После прохода статистика — read.stats."""
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
    p = 'protocol/demo.torn'
    if os.path.exists(p):
        os.remove(p)

    append(p, {'kind': 'exp', 'id': 1, 'ok': True})
    append(p, {'kind': 'exp', 'id': 2, 'score': 0.91})
    append_raw(p, b'\xde\xad\xbe\xef')
    append(p, {'kind': 'exp', 'id': 4, 'note': 'tail'})

    print('--- intact ---')
    list(read(p))
    print('records:', read.stats)

    # порча 1: битый байт в середине второй записи
    data = open(p, 'rb').read()
    mid = data.find(b'"score"') - 1
    open(p, 'r+b').write(data[:mid] + bytes([data[mid] ^ 0xFF]) + data[mid + 1:])
    print('--- corrupted byte ---')
    for t, pl in read(p):
        print(' ', t, pl if isinstance(pl, bytes) else str(pl)[:50])
    print('stats:', read.stats)

    # порча 2: обрыв хвоста посередине записи
    data = open(p, 'rb').read()
    open(p, 'r+b').truncate(len(data) - 7)
    print('--- torn tail ---')
    for t, pl in read(p):
        print(' ', t, pl if isinstance(pl, bytes) else str(pl)[:50])
    print('stats:', read.stats)
