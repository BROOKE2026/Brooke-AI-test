#!/bin/bash
# Start the Brooke API. Ollama must already be running.
cd "$(dirname "$0")"
export BROOKE_MODEL="${BROOKE_MODEL:-qwen3:14b}"
exec ./.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8080
