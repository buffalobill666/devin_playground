"""telemetry.py — живая телеметрия цензуса через TORN.

Старая схема: census копился в rows и сбрасывался в families.csv
В КОНЦЕ прогона — падение симуляции теряло всю историю.

Новая: каждая запись цензуса — TORN-кадр, дописываемый на диск
в момент замера. Падение теряет максимум последний (незакрытый)
кадр; families.csv выводится ИЗ torn-потока после прогона —
csv становится производной, а не единственной копией.

Демо: прогон 4000 тиков, потом симуляция краша — битый байт
в середине + обрыв хвоста. Torn теряет <=2 записей из ~350;
csv-схема при крахе теряла бы 100%.
"""

import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'protocol'))
import torn                                                     # noqa: E402

KEYS = ['tick', 'fam', 'n', 'speed', 'appetite', 'effic',
        'vigil', 'resist', 'n_inf']


class TornTelemetry:
    """Append-only стрим записей цензуса: кадр на строку."""

    def __init__(self, path, meta=None):
        self.path = str(path)
        if os.path.exists(self.path):
            os.remove(self.path)
        torn.append(self.path, {'kind': 'schema', 'cols': KEYS,
                                'meta': meta or {}})
        self.n = 0

    def emit(self, row: dict):
        torn.append(self.path, {'r': [row[k] for k in KEYS]})
        self.n += 1


def read_rows(path):
    """Все целые записи из torn-потока (битые кадры пропускаются)."""
    rows = []
    for rtype, pl in torn.read(path):
        if isinstance(pl, dict) and 'r' in pl:
            rows.append(pl['r'])
    return rows, torn.read.stats


def torn_to_csv(torn_path, csv_path):
    """CSV как производная torn-потока."""
    rows, stats = read_rows(torn_path)
    with open(csv_path, 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(KEYS)
        w.writerows(rows)
    return len(rows), stats


if __name__ == '__main__':
    from .family import run_family
    import sys as _s
    _s.path.insert(0, str(Path(__file__).resolve().parent.parent))
    out = Path('runs/family-torn')
    tp = out / 'families.torn'
    out.mkdir(parents=True, exist_ok=True)

    # прогон с живой телеметрией (через monkey-patch census-хука
    # нет — честнее: run_family принимает telemetry-объект)
    run_family(ticks=4000, seed=7, out=str(out), telemetry=TornTelemetry(tp))
    n, stats = torn_to_csv(tp, out / 'families.csv')
    print(f'записей в потоке: {n}, stats={stats}')

    # краш 1: битый байт в середине потока
    off = os.path.getsize(tp) // 2
    with open(tp, 'r+b') as f:
        f.seek(off)
        b = f.read(1)
        f.seek(off)
        f.write(bytes([b[0] ^ 0xFF]))
    rows2, st2 = read_rows(tp)
    print(f'краш/байт: живых записей {len(rows2)}/{n}, '
          f'skipped={st2["skipped"]}B')

    # краш 2: обрыв хвоста посередине кадра (симуляция kill -9)
    with open(tp, 'r+b') as f:
        f.truncate(os.path.getsize(tp) - 13)
    rows3, st3 = read_rows(tp)
    lost = n - len(rows3)
    print(f'краш/обрыв: живых записей {len(rows3)}/{n}, '
          f'потеряно {lost}, torn_tail={st3["torn_tail"]}B')
    print('VERDICT:', 'OK' if lost <= 2 and len(rows3) > n * 0.97
          else 'FAIL')
