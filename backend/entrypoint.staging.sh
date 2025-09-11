#!/bin/sh

echo "Running migrations..."
python manage.py migrate

echo "Starting server..."
# Ensure PORT is set in the environment or default to 8000
# This allows the server to run on the specified port
exec gunicorn main.asgi:application --bind 0.0.0.0:${PORT:-8000}
