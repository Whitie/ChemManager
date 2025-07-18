#!/bin/bash

GUNI=$(which gunicorn)
PY=$(which python)

echo "Migrating database tables"
$PY manage.py migrate

echo "Starting cluster service for background tasks..."
$PY manage.py qcluster &
QCLUSTER_PID=$!
echo "Started with PID $QCLUSTER_PID"

trap "kill -INT -${QCLUSTER_PID}" EXIT

echo "Starting Gunicorn WSGI server..."
$GUNI \
    --reload \
    --workers 4 \
    --access-logfile - \
    --bind 0.0.0.0:8000 \
    --env DJANGO_SETTINGS_MODULE=chemman.settings \
    chemman.wsgi:application
