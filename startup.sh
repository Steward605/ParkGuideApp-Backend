#!/bin/sh
set -e

echo "Starting ParkGuide backend startup script"

python - <<'PY'
import cv2
from ultralytics import YOLO
print("Startup OpenCV:", cv2.__version__, cv2.__file__)
print("Startup Ultralytics YOLO import OK:", YOLO)
PY

python manage.py migrate --no-input
gunicorn park_guide.wsgi:application --bind=0.0.0.0:${PORT:-8000} --timeout 600
