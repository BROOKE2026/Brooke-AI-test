#!/bin/bash
# A dedicated inference instance for Brooke, on its own port.
#
# WHY NOT SHARE the Ollama the rest of the box uses:
#   1. OLLAMA_NUM_PARALLEL is server-wide. Setting it for Brooke changes it for
#      inbound-docs, HARP, and every other pipeline.
#   2. The desktop app respawns its own `ollama serve`, so env tuning on 11434
#      never sticks anyway.
#   3. Batch work and interactive chat want opposite things. A long batch job
#      would park Brooke's clients behind it in the same queue.
#
# The default Ollama on :11434 is left completely alone. Models are read from the
# same store, so nothing is re-downloaded.
#
# On the Mac Studios this becomes the whole job of the box: one instance, many
# slots, nothing else competing.
set -e
PORT="${BROOKE_OLLAMA_PORT:-11435}"
PAR="${BROOKE_PAR:-4}"
CTX="${BROOKE_CTX:-16384}"        # total, split across slots -> 4k each at PAR=4
MODEL="${BROOKE_MODEL:-qwen3:8b}"
BIN="/Applications/Ollama.app/Contents/Resources/ollama"

pkill -f "OLLAMA_HOST=127.0.0.1:$PORT" 2>/dev/null || true
lsof -ti :$PORT 2>/dev/null | xargs kill 2>/dev/null || true
sleep 2

echo "Starting Brooke inference on :$PORT  (parallel=$PAR ctx=$CTX model=$MODEL)"
OLLAMA_HOST="127.0.0.1:$PORT" \
OLLAMA_NUM_PARALLEL="$PAR" \
OLLAMA_CONTEXT_LENGTH="$CTX" \
OLLAMA_MAX_LOADED_MODELS=1 \
OLLAMA_FLASH_ATTENTION=1 \
nohup "$BIN" serve > /tmp/brooke-ollama.log 2>&1 &

for i in $(seq 1 40); do
  curl -s -m 2 "http://127.0.0.1:$PORT/api/version" >/dev/null 2>&1 && break
  sleep 1
done
curl -s -m 2 "http://127.0.0.1:$PORT/api/version" >/dev/null || { echo "FAILED, see /tmp/brooke-ollama.log"; exit 1; }

echo "Warming $MODEL..."
curl -s -m 300 "http://127.0.0.1:$PORT/api/chat" \
  -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"stream\":false,\"think\":false}" >/dev/null
sleep 2
echo "llama-server flags:"
ps aux | grep "[l]lama-server" | sed 's/.*llama-server/llama-server/' | tr ' ' '\n' \
  | grep -E '^-(c|np)$' -A1 | paste -d' ' - - | grep -v '^--' | sed 's/^/  /'
echo
echo "Run the API against it:  OLLAMA_HOST=http://127.0.0.1:$PORT BROOKE_MODEL=$MODEL ./api/run.sh"
