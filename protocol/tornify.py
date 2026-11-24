"""tornify.py — применение TORN к реальным данным runs/.

csv -> torn: первый кадр — схема {'kind':'schema','cols':[...]},
дальше кадр на строку (значения списком, компактно).
torn -> verify: сверка построчно с исходником.

Демо на runs/family/families.csv: конверсия, roundtrip,
битый байт в середине -> потеряна ровно одна запись.
"""

import csv
import os

import torn


def csv_to_torn(csv_path, torn_path):
    if os.path.exists(torn_path):
        os.remove(torn_path)
    n = 0
    with open(csv_path, newline='') as fh:
        rd = csv.reader(fh)
        cols = next(rd)
        torn.append(torn_path, {'kind': 'schema', 'cols': cols})
        for row in rd:
            torn.append(torn_path, {'r': row})
            n += 1
    return n


def torn_to_rows(torn_path):
    rows, schema = [], None
    for rtype, pl in torn.read(torn_path):
        if isinstance(pl, dict) and pl.get('kind') == 'schema':
            schema = pl['cols']
        elif isinstance(pl, dict) and 'r' in pl:
            rows.append(pl['r'])
    return schema, rows


def corrupt(path, offset):
    with open(path, 'r+b') as f:
        f.seek(offset)
        b = f.read(1)
        f.seek(offset)
        f.write(bytes([b[0] ^ 0xFF]))


if __name__ == '__main__':
    src = 'runs/family/families.csv'
    dst = 'runs/family/families.torn'
    n = csv_to_torn(src, dst)
    print(f'записей: {n}, csv {os.path.getsize(src)}B -> '
          f'torn {os.path.getsize(dst)}B '
          f'(x{os.path.getsize(dst)/os.path.getsize(src):.2f})')

    schema, rows = torn_to_rows(dst)
    with open(src, newline='') as fh:
        rd = csv.reader(fh)
        cols = next(rd)
        src_rows = list(rd)
    ok = (schema == cols and len(rows) == len(src_rows)
          and all(a == b for a, b in zip(rows, src_rows)))
    print('roundtrip:', 'OK — построчно идентично' if ok else 'FAIL')

    # порча: один байт в середине файла
    off = os.path.getsize(dst) // 2
    corrupt(dst, off)
    schema2, rows2 = torn_to_rows(dst)
    lost = len(rows) - len(rows2)
    st = torn.read.stats
    print(f'после порчи: потеряно {lost} записей, '
          f'skipped={st["skipped"]}B, stats={st}')
    print('VERDICT:', 'OK' if ok and lost == 1 else 'FAIL')
