#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
pip uninstall -y opencv-python opencv-contrib-python || true
pip install --no-cache-dir "opencv-python-headless>=4.8.0"
python3 manage.py collectstatic --no-input
python3 manage.py migrate
