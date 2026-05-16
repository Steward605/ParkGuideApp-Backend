"""
WSGI config for park_guide project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import sys
from pathlib import Path

# Allow running from a self-contained deployment package when App Service skips Oryx install.
BASE_DIR = Path(__file__).resolve().parent.parent
VENDORED_SITE_PACKAGES_CANDIDATES = [
    BASE_DIR / 'python_packages' / 'lib' / 'site-packages',
    BASE_DIR / '.python_packages' / 'lib' / 'site-packages',
]
for vendored_path in VENDORED_SITE_PACKAGES_CANDIDATES:
    if vendored_path.exists():
        sys.path.insert(0, str(vendored_path))

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'park_guide.settings')

application = get_wsgi_application()
