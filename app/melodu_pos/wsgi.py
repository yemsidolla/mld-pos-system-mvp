"""WSGI config for Melodu POS."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "melodu_pos.settings")

application = get_wsgi_application()
