#!/usr/bin/env bash
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py seed_services || true
python manage.py create_admin_from_env || true

gunicorn pos_backend.wsgi --bind 0.0.0.0:${PORT:-8000} --workers 2
