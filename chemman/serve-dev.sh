#!/bin/bash

GUNI=$(which gunicorn)
PY=$(which python)

echo "Starting cluster service for background tasks..."
$PY manage.py qcluster &
QCLUSTER_PID=$!
echo "Started with PID $QCLUSTER_PID"

echo "Starting Gunicorn WSGI server..."
$GUNI \
    --reload \
    --workers 4 \
    --access-logfile - \
    --bind 127.0.0.1:8000 \
    --env DJANGO_SETTINGS_MODULE=chemman.settings \
    chemman.wsgi:application

echo "Trying to terminate cluster service..."
kill $QCLUSTER_PID
wait $QCLUSTER_PID
