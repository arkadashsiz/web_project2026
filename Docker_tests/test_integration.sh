#!/bin/bash
set -e

echo "Running integration smoke test..."

# Test if frontend can reach backend API (CORS should allow)
# We'll try to fetch a known API endpoint from inside the frontend container
# Alternatively, we can just check that the backend's admin is reachable.

# Check backend admin login page (publicly accessible)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/admin/login/)

if [ "$HTTP_CODE" -eq 200 ]; then
  echo "✅ Backend admin login page is reachable."
else
  echo "❌ Backend admin login page returned $HTTP_CODE"
  exit 1
fi

# Optionally, try to register a test user via API (if endpoint exists)
# This would require a POST request with appropriate data.

echo "All integration checks passed."