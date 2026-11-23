# docker — песочница от хозяина

Изолированное Linux-пространство для прогонов: образ
`devin-play` (python 3.12-slim + numpy/matplotlib/pillow/
requests).

- Сборка: `docker build -t devin-play docker/`
- Запуск: `./dock.sh <cmd>` — репозиторий примонтирован в
  `/playground`, результаты пишутся прямо в папки проекта.
- Пример: `./dock.sh python3 maps/island.py`

Зачем: Linux-окружение внутри Windows-хоста + изоляция для
рискованных экспериментов (дано хозяином 2026-11-23).
