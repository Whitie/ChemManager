#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

echo "Migrating database"
poetry run python manage.py migrate

echo "Collecting static files"
poetry run python manage.py collectstatic --no-input

echo "Starting cluster service for background tasks..."
poetry run python manage.py qcluster &
QCLUSTER_PID=$!
echo "Started with PID $QCLUSTER_PID"

trap "kill $QCLUSTER_PID" EXIT

echo "Starting Gunicorn with 4 workers"

poetry run gunicorn \
    --workers 4 \
    --access-logfile - \
    --bind 0.0.0.0:8800 \
    --env DJANGO_SETTINGS_MODULE=chemman.settings \
    --env SERVE_LAN=on \
    chemman.wsgi:application
