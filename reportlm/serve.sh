#!/usr/bin/env bash
# ⑧ 서빙: 승격된 판(models/current.json)만 띄운다 — 127.0.0.1 전용, OpenAI 호환 API (/v1/chat/completions)
# 사용: bash reportlm/serve.sh [포트=10013]
set -euo pipefail
WORK="${REPORTLM_WORK:-$HOME/reportlm-work}"
PORT="${1:-10013}"
MODEL=$(python3 -c "import json;print(json.load(open('$WORK/models/current.json'))['path'])")
VER=$(python3 -c "import json;print(json.load(open('$WORK/models/current.json'))['version'])")
echo "serve $VER ($MODEL) → http://127.0.0.1:$PORT"
exec "$WORK/.venv/bin/python" -m mlx_lm server --model "$MODEL" --host 127.0.0.1 --port "$PORT"
