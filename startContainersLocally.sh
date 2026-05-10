#!/bin/bash

ANGULAR_CONTAINER="pokeapp_angular"
FLASK_CONTAINER="pokeapp_flask"
ORACLE_CONTAINER="pokeapp_oracle"
NETWORK="pokeapp_network"

# ── Preflight checks ──────────────────────────────────────────────────────────

if [ ! -f .env ]; then
  echo "ERROR: .env file not found in $(pwd)"
  echo "Create it first — see README for required variables."
  exit 1
fi

# Windows-compatible port 1521 kill
PORT_1521=$(netstat -ano 2>/dev/null | findstr ":1521 " | awk '{print $5}' | head -1)
if [ -n "$PORT_1521" ]; then
  echo "Port 1521 in use by PID $PORT_1521 — killing..."
  taskkill //PID $PORT_1521 //F
  sleep 2
fi

# Clean up any leftover containers from a previous run
for NAME in $ANGULAR_CONTAINER $FLASK_CONTAINER $ORACLE_CONTAINER; do
  if docker ps -a --format '{{.Names}}' | grep -q "^${NAME}$"; then
    echo "Removing leftover container: $NAME"
    docker stop $NAME 2>/dev/null
    docker rm   $NAME 2>/dev/null
  fi
done

# ─────────────────────────────────────────────────────────────────────────────

docker network create $NETWORK 2>/dev/null || true

docker build --pull --rm -f 'Dockerfile.angular' -t 'pokeapp_frontend:latest' '.' --build-arg ENV=test
docker build --pull --rm -f 'Dockerfile.flask'   -t 'pokeapp_backend:latest'  '.'

docker run -d \
  --name $ORACLE_CONTAINER \
  --network $NETWORK \
  -p 1521:1521 \
  -v oracle-data:/opt/oracle/oradata \
  container-registry.oracle.com/database/free:latest-lite

docker run -d \
  --name $ANGULAR_CONTAINER \
  --network $NETWORK \
  -p 80:80 \
  pokeapp_frontend:latest

docker run -d \
  --name $FLASK_CONTAINER \
  --network $NETWORK \
  -p 5000:5000 \
  --env-file .env \
  pokeapp_backend:latest

# Confirm all 3 actually started
echo ""
echo "=== Container status ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "pokeapp|NAMES"

# Warn if Oracle didn't start
if ! docker ps --format '{{.Names}}' | grep -q "^${ORACLE_CONTAINER}$"; then
  echo ""
  echo "WARNING: Oracle container did not start. Check: docker logs $ORACLE_CONTAINER"
fi

echo ""
echo "Watch Oracle: docker logs -f $ORACLE_CONTAINER"
echo "Press Ctrl+C to stop all containers."

cleanup() {
    echo ""
    echo "Stopping containers..."
    docker stop $ANGULAR_CONTAINER $FLASK_CONTAINER $ORACLE_CONTAINER 2>/dev/null
    docker rm   $ANGULAR_CONTAINER $FLASK_CONTAINER $ORACLE_CONTAINER 2>/dev/null
    docker network rm $NETWORK 2>/dev/null
}
trap cleanup EXIT

while true; do sleep 1; done