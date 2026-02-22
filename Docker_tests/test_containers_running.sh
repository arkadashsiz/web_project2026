#!/bin/bash
set -e

echo "Checking container status..."

# List of expected container names (as defined in docker-compose)
CONTAINERS=("police_db" "police_backend" "police_frontend")

for name in "${CONTAINERS[@]}"; do
  if [ "$(docker ps -q -f name=$name)" ]; then
    echo "✅ $name is running."
  else
    echo "❌ $name is NOT running."
    exit 1
  fi
done

echo "All containers are up."