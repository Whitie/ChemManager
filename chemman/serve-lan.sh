#!/bin/bash

GUNI=$(which gunicorn)
WORKERS=$(python -c 'import multiprocessing as mp;print(mp.cpu_count()*2,end="")')

echo "Starting Gunicorn with $WORKERS workers"

$GUNI \
    --workers $WORKERS \
    --access-logfile - \
    --bind 0.0.0.0:8800 \
    --env DJANGO_SETTINGS_MODULE=chemman.settings \
    --env SERVE_LAN=on \
    chemman.wsgi:application
