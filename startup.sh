#!/bin/sh
set -e

echo "Starting ParkGuide backend startup script"

apt-get update
apt-get install -y libgl1 libglib2.0-0 libsm6 libxext6 ffmpeg
ldconfig -p | grep libGL.so.1 || true

python -m pip uninstall -y opencv-python opencv-contrib-python || true
python -m pip install --no-cache-dir "opencv-python-headless>=4.8.0"
python - <<'PY'
import cv2
from ultralytics import YOLO
print("Startup OpenCV:", cv2.__version__, cv2.__file__)
print("Startup Ultralytics YOLO import OK:", YOLO)
PY

python manage.py migrate --no-input
gunicorn park_guide.wsgi:application --bind=0.0.0.0:${PORT:-8000} --timeout 600
