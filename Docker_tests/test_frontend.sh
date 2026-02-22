#!/bin/bash
set -e

echo "Testing frontend..."

sleep 3

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/)

if [ "$HTTP_CODE" -eq 200 ]; then
  echo "✅ Frontend responded with $HTTP_CODE"
else
  echo "❌ Frontend returned HTTP $HTTP_CODE"
  exit 1
fi

# Optional: check for a known string in the page
if curl -s http://localhost/ | grep -q "Police Case Management"; then
  echo "✅ Frontend contains expected text."
else
  echo "❌ Frontend missing expected text."
  exit 1
fi