#!/bin/bash
# 서버에서 도는 배포 스크립트 (강의 03 §5.3 을 이 프로젝트에 맞춘 것).
#   server.sh image <태그> <이미지 경로>   stdin 으로 GHCR 토큰 한 줄
#   server.sh model <모델 판>   /srv/paperclf/models/<판>/ 에 놓인 모델로 바꾼다 (승격·되돌리기 공통)
#   server.sh status
set -euo pipefail
cd /srv/paperclf
touch .env
setenv() { grep -v "^$1=" .env > .env.new || true; echo "$1=$2" >> .env.new; mv .env.new .env; }
health() {
  for i in $(seq 1 30); do
    H=$(curl -fsS localhost:8080/health 2>/dev/null) && { [ -z "${1:-}" ] || echo "$H" | grep -q "\"model_version\":\"$1\""; } \
      && echo "$H" && return 0
    sleep 1
  done
  echo "health 실패" >&2; return 1
}
case "${1:-}" in
  image)
    TAG=$2 IMAGE=$3
    [[ $TAG =~ ^v[0-9]+(\.[0-9]+)*$ ]] || { echo "태그 형식이 아니다: $TAG" >&2; exit 1; }
    [[ $IMAGE =~ ^ghcr\.io/[a-z0-9._/-]+$ ]] || { echo "이미지 경로 형식이 아니다: $IMAGE" >&2; exit 1; }
    read -r TOKEN
    export DOCKER_CONFIG=$(mktemp -d)
    trap 'rm -rf "$DOCKER_CONFIG"' EXIT
    printf %s "$TOKEN" | docker login ghcr.io -u token --password-stdin >/dev/null
    PREV=$(grep '^TAG=' .env | cut -d= -f2 || true)
    docker pull -q "$IMAGE/paperclf-api:$TAG"
    setenv IMAGE "$IMAGE"; setenv TAG "$TAG"
    docker compose up -d
    if ! health; then
      [ -n "$PREV" ] && { setenv TAG "$PREV"; docker compose up -d; }
      exit 1
    fi
    ;;
  model)
    VER=$2
    [[ $VER =~ ^m[0-9]{8}-[0-9]+$ ]] || { echo "모델 판 형식이 아니다: $VER" >&2; exit 1; }
    [ -f "models/$VER/model.onnx" ] && [ -f "models/$VER/model.json" ] || { echo "models/$VER 가 없다" >&2; exit 1; }
    PREV=$(grep '^MODEL_VERSION=' .env | cut -d= -f2 || true)
    setenv MODEL_VERSION "$VER"; setenv MODEL_DIR "/models/$VER"
    docker compose up -d
    if ! health "$VER"; then
      if [ -n "$PREV" ]; then setenv MODEL_VERSION "$PREV"; setenv MODEL_DIR "/models/$PREV"
      else sed -i '/^MODEL_VERSION=/d; /^MODEL_DIR=/d' .env; fi
      docker compose up -d; exit 1
    fi
    ;;
  status)
    sed -E -e 's#^(LEDGER_DSN=[^:]+://[^:]+:)[^@]*@#\1***@#' -e 's#^(API_TOKEN=).*#\1***#' .env; docker compose ps --format '{{.Service}} {{.Image}} {{.Status}}'; health ;;
  *) echo "사용: server.sh image|model|status" >&2; exit 2 ;;
esac
