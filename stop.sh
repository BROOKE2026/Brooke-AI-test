#!/bin/bash
pkill -f "uvicorn server:app" 2>/dev/null && echo "api stopped"
pkill -f "cloudflared tunnel" 2>/dev/null && echo "tunnels stopped"
pkill -f "http.server 4173" 2>/dev/null && echo "web stopped"
exit 0
