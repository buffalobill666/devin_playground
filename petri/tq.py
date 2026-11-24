"""tq.py — запросы повторно torn-потока телеметрии.

Поток пишется один раз, читается много. Полный scan для
«дай все записи семьи 12» — расточительство: поток аппенд-онли,
значит оффсеты бессмертны — можно один раз построить индекс
{fam: [offsets]} и дальше читать только нужные кадры.

API:
    build_index(path)            # один линейный проход -> path.famidx
    query(path, fam=None,
          t0=None, t1=None)      # генератор записей (dict по KEYS)
    read_at(path, off)           # одиночный кадр по оффсету

Демо: индекс по runs/family-torn/families.torn, запрос по
одной семье — читает только её кадры, не весь поток.
"""

import json
import os
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'protocol'))
import torn                                                     # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from telemetry import KEYS                                      # noqa: E402


def _frame_at(buf, off):
    """Кадр из байтового буфера по оффсету (HDR включает magic)."""
    if buf[off:off + 2] != torn.MAGIC:
        return None
    _, ver, rtype, ln = torn.HDR.unpack_from(buf, off)
    end = off + torn.HDR.size + ln + 4
    if end > len(buf) or ver != torn.VER:
        return None
    crc_want, = torn.struct.unpack_from('<I', buf, end - 4)
    if crc_want != zlib.crc32(buf[off + 2:end - 4]):
        return None
    pl = buf[off + torn.HDR.size:end - 4]
    return json.loads(pl) if rtype == torn.T_JSON else pl


def read_at(path, off):
    """Одиночный кадр по оффсету: magic+hdr+payload+crc."""
    with open(path, 'rb') as f:
        return _frame_at(f.read(), off)


def idx_path(path):
    return str(path) + '.famidx'


def build_index(path):
    """Один проход: {fam: [offsets]}. Индекс — производная:
    его можно перестроить из потока в любой момент."""
    ix = {}
    for rtype, payload, off in torn.scan(path):
        if rtype != torn.T_JSON:
            continue
        try:
            pl = json.loads(payload)
        except Exception:
            continue
        if isinstance(pl, dict) and 'r' in pl:
            ix.setdefault(str(pl['r'][1]), []).append(off)
    with open(idx_path(path), 'w') as f:
        json.dump(ix, f)
    return ix


def query(path, fam=None, t0=None, t1=None, cols=None):
    """Записи-дикты. fam -> seek по индексу (строится при
    отсутствии); диапазон тиков и выбор колонок — постфильтр."""
    ip = idx_path(path)
    if fam is not None:
        ix = (json.load(open(ip)) if os.path.exists(ip)
              else build_index(path))
        offs = ix.get(str(fam), [])
        # F: — медленный диск на random seek (~1s): буфер целиком
        with open(path, 'rb') as fh:
            buf = fh.read()
        records = (_frame_at(buf, o) for o in offs)
    else:
        records = (pl for _, pl in torn.read(path))
    for pl in records:
        if not (isinstance(pl, dict) and 'r' in pl):
            continue
        row = dict(zip(KEYS, pl['r']))
        if t0 is not None and row['tick'] < t0:
            continue
        if t1 is not None and row['tick'] > t1:
            continue
        yield ({k: row[k] for k in cols} if cols else row)


if __name__ == '__main__':
    tp = Path('runs/family-torn/families.torn')
    if not tp.exists():
        print('нет families.torn — прогони telemetry.py')
        sys.exit(0)
    ix = build_index(tp)
    print(f'индекс: {len(ix)} семей, '
          f'{sum(len(v) for v in ix.values())} записей')
    fam = max(ix, key=lambda k: len(ix[k]))
    rows = list(query(tp, fam=fam))
    print(f'самая густая семья {fam}: {len(rows)} записей, '
          f'тики {rows[0]["tick"]}..{rows[-1]["tick"]}')
    tail = list(query(tp, fam=fam, t0=rows[-1]['tick'] - 500,
                      cols=['tick', 'n']))
    print('хвост (t>{}): {}'.format(tail[0]['tick'] - 1, tail[:3]))
