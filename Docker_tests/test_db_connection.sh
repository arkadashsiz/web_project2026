#!/bin/bash
set -e

echo "Testing database connection from backend..."

# Run a simple Django command that touches the DB
docker exec police_backend python manage.py migrate --plan > /dev/null 2>&1

if [ $? -eq 0 ]; then
  echo "✅ Backend can connect to the database."
else
  echo "❌ Database connection failed."
  exit 1
fi