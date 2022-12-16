#!/bin/bash

GUNI=$(which gunicorn)

$GUNI \
    --reload \
    --workers 4 \
    --access-logfile - \
    --bind 127.0.0.1:8000 \
    --env DJANGO_SETTINGS_MODULE=chemman.settings \
    chemman.wsgi:application
