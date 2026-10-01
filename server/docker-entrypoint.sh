#!/bin/sh
set -e

echo "Застосовуємо міграції Alembic…"
alembic upgrade head

exec "$@"
