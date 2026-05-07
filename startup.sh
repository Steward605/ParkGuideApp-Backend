#!/bin/sh
set -e

apt-get update
apt-get install -y libgl1 libglib2.0-0 libsm6 libxext6 ffmpeg

python -m pip uninstall -y opencv-python opencv-contrib-python || true
python -m pip install --no-cache-dir "opencv-python-headless>=4.8.0"

python manage.py migrate --no-input
gunicorn park_guide.wsgi:application --bind=0.0.0.0:${PORT:-8000} --timeout 600
