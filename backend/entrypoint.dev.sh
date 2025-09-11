#!/bin/sh

echo "Running migrations..."
python manage.py makemigrations
python manage.py migrate

echo "Starting server..."
exec uvicorn main.asgi:application --host 0.0.0.0 --port 8000 --reload
