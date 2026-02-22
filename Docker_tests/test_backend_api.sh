#!/bin/bash
set -e

echo "Testing backend API..."

# Wait a few seconds for the server to be ready
sleep 5

# Try to fetch the root endpoint (or /api/health if you have one)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/)

if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 302 ]; then
  echo "✅ Backend responded with $HTTP_CODE"
else
  echo "❌ Backend returned HTTP $HTTP_CODE"
  exit 1
fi