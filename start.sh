#!/bin/bash
# Start the whole Brooke test stack and print the public URLs.
# Quick tunnels get a NEW random URL every run, so the web build is
# regenerated each time with the current API URL baked in.
set -e
cd "$(dirname "$0")"
CF="$HOME/.local/bin/cloudflared"
[ -x "$CF" ] || { echo "cloudflared not found at $CF"; exit 1; }

echo "Stopping anything already running..."
pkill -f "uvicorn server:app" 2>/dev/null || true
pkill -f "cloudflared tunnel" 2>/dev/null || true
pkill -f "http.server 4173" 2>/dev/null || true
sleep 1

echo "Starting API on :8080..."
(cd api && nohup ./.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8080 > /tmp/brooke-api.log 2>&1 &)
sleep 3

echo "Opening API tunnel..."
nohup "$CF" tunnel --url http://localhost:8080 > /tmp/brooke-tunnel.log 2>&1 &
for i in $(seq 1 30); do
  API=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/brooke-tunnel.log 2>/dev/null | head -1)
  [ -n "$API" ] && break; sleep 1
done
[ -n "$API" ] || { echo "API tunnel failed, see /tmp/brooke-tunnel.log"; exit 1; }

echo "Building web against $API ..."
(cd web && VITE_API_BASE="$API" npm run build > /tmp/brooke-build.log 2>&1)

echo "Serving web on :4173..."
(cd web/dist && nohup python3 -m http.server 4173 --bind 0.0.0.0 > /tmp/brooke-web.log 2>&1 &)
sleep 2

echo "Opening web tunnel..."
nohup "$CF" tunnel --url http://localhost:4173 > /tmp/brooke-webtunnel.log 2>&1 &
for i in $(seq 1 30); do
  WEB=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/brooke-webtunnel.log 2>/dev/null | head -1)
  [ -n "$WEB" ] && break; sleep 1
done

echo
echo "======================================================"
echo "  OPEN THIS:  $WEB"
echo "  API:        $API"
echo "  Logins:     sarah-2026 / marcus-2026 / elena-2026"
echo "======================================================"
echo "  Stop everything:  ./stop.sh"
