#!/bin/bash
# 서버 준비 — Lightsail 브라우저 SSH(ec2-user)에서 한 번 실행한다.
#   curl -fsSL https://raw.githubusercontent.com/metahomo/miniproject5_kms/main/deploy/lightsail/bootstrap.sh -o bootstrap.sh
#   bash bootstrap.sh final      # 최종 서버(nlpwizard.eta.pyhub.kr) — 러너 paperclf-final, 이름표 final, Caddyfile
#   bash bootstrap.sh work       # 작업용 서버(54.252.22.31)를 새로 만들 때 — 러너 paperclf, 이름표 lightsail·paperclf, Caddyfile.work
#   러너 등록 토큰을 물으면 붙여 넣는다 (화면에 안 보임). 여러 번 돌려도 된다(있는 것은 건너뛴다)
# 하는 일: ① /srv/paperclf 폴더·.env(600) ② eta 를 127.0.0.1:8090 으로 ③ Caddy(80/443) ④ 이 저장소 전용 self-hosted 러너
set -euo pipefail
ROLE=${1:-}
case "$ROLE" in
  final) RUNNER_NAME=paperclf-final RUNNER_LABELS=final CADDYFILE=Caddyfile ;;
  work)  RUNNER_NAME=paperclf RUNNER_LABELS=lightsail,paperclf CADDYFILE=Caddyfile.work ;;
  *) echo "사용: bash bootstrap.sh final|work — 이름표가 섞이면 다른 서버의 잡을 받는다" >&2; exit 2 ;;
esac
REPO=metahomo/miniproject5_kms
RAW=https://raw.githubusercontent.com/$REPO/main/deploy/lightsail
RUNNER_VERSION=2.338.2
RUNNER_SHA256=baebf204307bac6193480852732f0aba2ae97b6c5597c244f4d5558390147c40
[ "$(uname -m)" = x86_64 ] || { echo "x86_64 전용 스크립트다: $(uname -m)" >&2; exit 1; }
docker compose version >/dev/null || { echo "docker compose 가 없다" >&2; exit 1; }
# compose.override.yml 의 `!override` 는 Compose 2.24.4 부터 된다
CV=$(docker compose version --short | sed 's/^v//')
[ "$(printf '%s\n' 2.24.4 "$CV" | sort -V | head -1)" = 2.24.4 ] || { echo "Compose $CV < 2.24.4 — 먼저 올린다" >&2; exit 1; }

echo "① 폴더"
sudo install -d -o ec2-user -g ec2-user /srv/paperclf /srv/paperclf/models /srv/caddy
curl -fsSL "$RAW/compose.yml" -o /srv/paperclf/compose.yml
curl -fsSL "$RAW/server.sh" -o /srv/paperclf/server.sh
# Caddyfile 이 바뀐 때만 덮어쓰고 ③에서 다시 시작한다(admin off 라 reload 가 없다). 손으로 넣은 블록(KMS 등)이 있으면 지워지니 runbooks/final-server.md 참고
CADDY_CHANGED=0
curl -fsSL "$RAW/caddy/$CADDYFILE" -o /tmp/Caddyfile.new
if ! cmp -s /tmp/Caddyfile.new /srv/caddy/Caddyfile; then
  [ -f /srv/caddy/Caddyfile ] && cp /srv/caddy/Caddyfile /srv/caddy/Caddyfile.bak
  cp /tmp/Caddyfile.new /srv/caddy/Caddyfile && CADDY_CHANGED=1 # cp: bind mount 한 파일을 그대로 두고 내용만 바꾼다
fi
rm -f /tmp/Caddyfile.new
curl -fsSL "$RAW/caddy/compose.yml" -o /srv/caddy/compose.yml

echo "①-2 API 설정: 장부 네트워크(compose 가 요구), /predict 토큰(이 서버 .env 에만)"
docker network inspect paperclf-ledger-net >/dev/null 2>&1 || docker network create paperclf-ledger-net >/dev/null
touch /srv/paperclf/.env && chmod 600 /srv/paperclf/.env
if ! grep -q "^API_TOKEN=." /srv/paperclf/.env; then
  T=$(openssl rand -hex 24) # 실패하면 set -e 로 멈춘다 — 빈 토큰(= 인증 꺼짐)을 쓰지 않는다
  [ ${#T} -eq 48 ] || { echo "토큰 생성 실패" >&2; exit 1; }
  sed -i '/^API_TOKEN=/d' /srv/paperclf/.env
  echo "API_TOKEN=$T" >> /srv/paperclf/.env; unset T
  echo "   API_TOKEN 을 만들었다(값은 화면에 내지 않는다 — 서버 .env 에만)"
fi
grep -q "^RATE_LIMIT_PER_MIN=" /srv/paperclf/.env || echo "RATE_LIMIT_PER_MIN=60" >> /srv/paperclf/.env

echo "② eta 를 Caddy 뒤로 (127.0.0.1:8090)"
if [ -f /srv/eta/compose.yml ]; then
  curl -fsSL "$RAW/eta-compose.override.yml" -o /srv/eta/compose.override.yml
  (cd /srv/eta && docker compose up -d)
fi

echo "③ Caddy"
(cd /srv/caddy && docker compose up -d && { [ "$CADDY_CHANGED" = 0 ] || docker compose restart caddy; })
if [ "$ROLE" = final ] && [ -f /srv/eta/compose.yml ]; then # 작업용 서버·새 서버(eta 없음)에는 건너뛴다
  for i in $(seq 1 30); do curl -fsS localhost/health >/dev/null 2>&1 && break; sleep 1; done
  curl -fsS localhost/health && echo " ← eta 가 Caddy 뒤에서 응답"
fi

echo "④ 러너 (이 저장소 전용, 이름 $RUNNER_NAME · 이름표 $RUNNER_LABELS — 다른 서버 러너와 잡이 섞이지 않게)"
if [ ! -f ~/actions-runner-paperclf/.runner ]; then # .runner = 등록까지 끝난 표시 (토큰이 틀려 멈췄으면 다시 돌릴 때 이어서)
  mkdir -p ~/actions-runner-paperclf && cd ~/actions-runner-paperclf
  [ -x ./config.sh ] || {
  curl -fsSL -o runner.tar.gz "https://github.com/actions/runner/releases/download/v$RUNNER_VERSION/actions-runner-linux-x64-$RUNNER_VERSION.tar.gz"
  echo "$RUNNER_SHA256  runner.tar.gz" | sha256sum -c -
  tar xzf runner.tar.gz && rm runner.tar.gz
  }
  read -rsp "러너 등록 토큰: " TOKEN; echo
  [ -n "$TOKEN" ] || { echo "토큰이 비었다" >&2; exit 1; }
  ./config.sh --url "https://github.com/$REPO" --token "$TOKEN" --name "$RUNNER_NAME" --labels "$RUNNER_LABELS" --unattended
  sudo ./svc.sh install ec2-user
  sudo ./svc.sh start
  unset TOKEN
else
  echo "   러너가 이미 등록돼 있다 — 건너뛴다 (이름표는 GitHub → Settings → Actions → Runners 에서 확인)"
fi
echo "끝. GitHub → Settings → Actions → Runners 에 $RUNNER_NAME 이 Idle 이면 성공"
[ "$ROLE" = final ] && echo "다음: PC 에서 gh variable set FINAL_ENABLED --body true"
exit 0
