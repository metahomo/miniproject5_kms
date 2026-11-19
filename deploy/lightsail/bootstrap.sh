#!/bin/bash
# 서버 준비 — Lightsail 브라우저 SSH(ec2-user)에서 한 번 실행한다.
#   curl -fsSL https://raw.githubusercontent.com/metahomo/miniproject5_kms/main/deploy/lightsail/bootstrap.sh -o bootstrap.sh
#   bash bootstrap.sh            # 러너 등록 토큰을 물으면 붙여 넣는다 (화면에 안 보임)
# 하는 일: ① /srv/paperclf 폴더 ② eta 를 127.0.0.1:8090 으로 ③ Caddy(80/443) ④ 이 저장소 전용 self-hosted 러너
set -euo pipefail
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
curl -fsSL "$RAW/caddy/Caddyfile" -o /srv/caddy/Caddyfile
curl -fsSL "$RAW/caddy/compose.yml" -o /srv/caddy/compose.yml

echo "② eta 를 Caddy 뒤로 (127.0.0.1:8090)"
if [ -f /srv/eta/compose.yml ]; then
  curl -fsSL "$RAW/eta-compose.override.yml" -o /srv/eta/compose.override.yml
  (cd /srv/eta && docker compose up -d)
fi

echo "③ Caddy"
(cd /srv/caddy && docker compose up -d)
for i in $(seq 1 30); do curl -fsS localhost/health >/dev/null 2>&1 && break; sleep 1; done
curl -fsS localhost/health && echo " ← eta 가 Caddy 뒤에서 응답"

echo "④ 러너 (이 저장소 전용, 이름표 lightsail·paperclf)"
if [ ! -d ~/actions-runner-paperclf ]; then
  mkdir ~/actions-runner-paperclf && cd ~/actions-runner-paperclf
  curl -fsSL -o runner.tar.gz "https://github.com/actions/runner/releases/download/v$RUNNER_VERSION/actions-runner-linux-x64-$RUNNER_VERSION.tar.gz"
  echo "$RUNNER_SHA256  runner.tar.gz" | sha256sum -c -
  tar xzf runner.tar.gz && rm runner.tar.gz
  read -rsp "러너 등록 토큰: " TOKEN; echo
  ./config.sh --url "https://github.com/$REPO" --token "$TOKEN" --name paperclf --labels lightsail,paperclf --unattended
  sudo ./svc.sh install ec2-user
  sudo ./svc.sh start
fi
echo "끝. GitHub → Settings → Actions → Runners 에 paperclf 가 Idle 이면 성공"
