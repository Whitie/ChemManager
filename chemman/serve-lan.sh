#!/bin/bash

PY=$(which python)
GUNICORN=$(which gunicorn)
WORKERS=$(python -c 'import multiprocessing as mp;print(mp.cpu_count()*2,end="")')

echo "Starting cluster service for background tasks..."
$PY manage.py qcluster &
QCLUSTER_PID=$!
echo "Started with PID $QCLUSTER_PID"

echo "Starting Gunicorn with $WORKERS workers"

$GUNICORN \
    --workers $WORKERS \
    --access-logfile - \
    --bind 0.0.0.0:8800 \
    --env DJANGO_SETTINGS_MODULE=chemman.settings \
    --env SERVE_LAN=on \
    chemman.wsgi:application

echo "Trying to terminate cluster service..."
kill $QCLUSTER_PID
wait $QCLUSTER_PID
