#!/bin/sh
set -e

echo "Starting ParkGuide backend startup script"

python manage.py migrate --no-input
gunicorn park_guide.wsgi:application --bind=0.0.0.0:${PORT:-8000} --timeout 600
