#!/usr/bin/env bash
# reportlm 파이프라인 — paperclf 의 model.yml 과 같은 단계: 데이터 → 학습 → 게이트 → 변환(fuse) → parity → 승격
# 사용: bash reportlm/pipeline.sh [iters]      (교사 데이터 teacher.jsonl 은 미리 teacher.py 로 만든다)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
WORK="${REPORTLM_WORK:-$HOME/reportlm-work}"
PY="$WORK/.venv/bin/python"
BASE="$WORK/base/Qwen2.5-1.5B-Instruct"
ITERS="${1:-100}"
DATA_MODE="${DATA_MODE:-group}"; export DATA_MODE
if [ "$DATA_MODE" = single ]; then DATA="$WORK/data"; else DATA="$WORK/data_group"; fi
VER="r$(date -u +%Y%m%d-%H%M)"
RUN="$WORK/runs/$VER"
mkdir -p "$RUN"
echo "== ② 데이터 준비"; "$PY" "$HERE/prepare.py"
echo "== ③ 학습 $VER (LoRA, iters=$ITERS)"
T0=$(date +%s)
"$PY" -m mlx_lm lora --model "$BASE" --train --data "$DATA" --iters "$ITERS" --batch-size 4 \
  --num-layers 16 --learning-rate "${LR:-1e-4}" --mask-prompt --max-seq-length 3072 --steps-per-report 25 \
  --steps-per-eval "${EVAL_EVERY:-100}" --adapter-path "$RUN/adapters" --seed 0 2>&1 | tee "$RUN/train.log"
printf '{"version":"%s","base":"%s","iters":%s,"lr":"%s","oversample_lim":"%s","seconds":%s,"data_mode":"%s","data_dir":"%s"}\n' "$VER" "$BASE" "$ITERS" "${LR:-1e-4}" "${OVERSAMPLE_LIM:-1}" "$(( $(date +%s)-T0 ))" "$DATA_MODE" "$DATA" > "$RUN/train.json"
echo "== ④ 게이트"
if ! "$PY" "$HERE/evaluate.py" --run "runs/$VER" --limit "${EVAL_LIMIT:-80}"; then
  python3 -c "import json,sys;sys.path.insert(0,'$HERE');from promote import ledger;ledger({'action':'gate_failed','version':'$VER'})"
  echo "게이트 실패 — 승격하지 않는다"; exit 1
fi
echo "== ⑤ 변환(fuse)"; "$PY" -m mlx_lm fuse --model "$BASE" --adapter-path "$RUN/adapters" --save-path "$RUN/fused"
echo "== ⑥ parity"; "$PY" "$HERE/parity.py" --run "runs/$VER" --limit "${PARITY_LIMIT:-20}" || { echo "parity 실패 — 승격하지 않는다"; exit 1; }
echo "== ⑦ 승격"; "$PY" "$HERE/promote.py" --run "runs/$VER"
echo "완료: $VER"
