#!/bin/bash
# dock.sh — запуск внутри контейнера-песочницы с примонтированным
# плейграундом. Использование: ./dock.sh <cmd> [args...]
# Пример: ./dock.sh python3 maps/island.py
MSYS_NO_PATHCONV=1 docker run --rm \
    -v "/f/DEVIN_PLAYGROUND:/playground" \
    -w /playground \
    devin-play "$@"
