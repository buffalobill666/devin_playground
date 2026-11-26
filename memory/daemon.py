"""daemon.py — devin-simrunner: очередь длинных прогонов.

Запускается Task Scheduler (devin-simrunner, каждые 15 мин).
Сканырует runs/_queue/*.job, берёт ОДНУ задачу за проход,
исполняет, помечает .done/.failed. Пустая очередь — выход
за секунды. Лок-файл не пускает двух демонов; лок старше
24 часов считается протухшим (демона убили) и ломается.

Формат job-файла (текст):
    cmd=py -3 petri/bigrun.py --ticks 100000
    cwd=F:\\DEVIN_PLAYGROUND        # опционально
Правило для job-скриптов: чекпоинты инкрементально,
flush-прогресс — демон может умереть вместе с хостом.
"""

import os
import subprocess
import sys
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE = os.path.join(ROOT, 'runs', '_queue')
LOCK = os.path.join(QUEUE, '.lock')
LOG = os.path.join(QUEUE, 'daemon.log')
MAX_LOCK_AGE = 3600  # heartbeat refreshes; 1h stale = dead


def log(msg):
    line = f'{time.strftime("%Y-%m-%d %H:%M")} {msg}'
    print(line, flush=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(line + '\n')


def acquire():
    os.makedirs(QUEUE, exist_ok=True)
    if os.path.exists(LOCK):
        if time.time() - os.path.getmtime(LOCK) > MAX_LOCK_AGE:
            log('stale lock -> breaking')
            os.remove(LOCK)
        else:
            age_h = (time.time() - os.path.getmtime(LOCK)) / 3600
            log(f'blocked by lock (age {age_h:.1f}h) — skipping')
            return False
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        return True
    except FileExistsError:
        return False


def parse_job(path):
    cfg = {'cwd': ROOT}
    for ln in open(path, encoding='utf-8'):
        if '=' in ln:
            k, v = ln.strip().split('=', 1)
            cfg[k.strip()] = v.strip()
    return cfg


def main():
    if not acquire():
        return
    try:
        jobs = sorted(f for f in os.listdir(QUEUE)
                      if f.endswith('.job'))
        if not jobs:
            return
        job = os.path.join(QUEUE, jobs[0])
        cfg = parse_job(job)
        log(f'start {jobs[0]}: {cfg.get("cmd")}')
        outlog = os.path.join(QUEUE, jobs[0] + '.out.log')
        stop_hb = threading.Event()

        def heartbeat():
            while not stop_hb.is_set():
                try:
                    os.utime(LOCK)
                except OSError:
                    pass
                stop_hb.wait(60)

        hb = threading.Thread(target=heartbeat, daemon=True)
        hb.start()
        try:
            with open(outlog, 'w') as out:
                r = subprocess.run(cfg['cmd'], shell=True,
                                   cwd=cfg['cwd'], timeout=6 * 3600,
                                   stdout=out, stderr=subprocess.STDOUT)
        finally:
            stop_hb.set()
        tag = '.done' if r.returncode == 0 else '.failed'
        os.rename(job, job + tag)
        log(f'{tag[1:]} {jobs[0]} rc={r.returncode}')
    except subprocess.TimeoutExpired:
        os.rename(job, job + '.timeout')
        log('timeout (6h cap)')
    finally:
        try:
            os.remove(LOCK)
        except OSError:
            pass


if __name__ == '__main__':
    main()
