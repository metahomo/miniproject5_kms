#!/bin/bash
# 작업용 서버(Amazon Linux 2023)를 Tailscale tailnet 에 붙인다 — 나중에 SSH(22)를 tailnet 안으로 좁히기 위한 준비
#   Mac 에서:  scp deploy/lightsail/tailscale.sh ec2-user@54.252.22.31:~/
#              ssh ec2-user@54.252.22.31 'sudo bash ~/tailscale.sh' < ~/.config/paperclf/tailscale-authkey
# 인증 키는 stdin 으로만 받는다 (명령줄·환경 변수·디스크에 남기지 않는다)
#   tailscale up --auth-key=file:<경로> 를 쓴다 — 키를 argv 에 올리면 ps 로 보이기 때문.
#   그 파일은 mktemp(0600)로 만들고 trap 으로 끝날 때 지운다
# 다시 돌려도 된다: 저장소·패키지·서비스가 이미 있으면 건너뛰고, 이미 붙어 있으면 up 을 하지 않는다
# Tailscale SSH(--ssh)는 켜지 않는다 — SSH 는 지금처럼 sshd 가 맡는다
set -euo pipefail
REPO_URL=https://pkgs.tailscale.com/stable/amazon-linux/2023/tailscale.repo
REPO_FILE=/etc/yum.repos.d/tailscale.repo
HOSTNAME_TS=paperclf

[ "$(id -u)" = 0 ] || { echo "root 로 돌린다: sudo bash $0" >&2; exit 1; }
. /etc/os-release
[ "${ID:-}" = amzn ] && [ "${VERSION_ID:-}" = 2023 ] || { echo "Amazon Linux 2023 전용이다: ${PRETTY_NAME:-?}" >&2; exit 1; }

echo "① 인증 키 (stdin)"
umask 077
KEYFILE=$(mktemp)
trap 'rm -f "$KEYFILE"' EXIT
if [ -t 0 ]; then read -rsp "Tailscale 인증 키: " KEY; echo; else IFS= read -r KEY || true; fi
exec </dev/null # 키 말고는 stdin 을 쓰지 않는다
KEY=${KEY%$'\r'}
printf %s "$KEY" > "$KEYFILE"
unset KEY

echo "② 저장소·설치"
[ -f "$REPO_FILE" ] || curl -fsSL "$REPO_URL" -o "$REPO_FILE"
rpm -q tailscale >/dev/null 2>&1 || dnf install -y tailscale

echo "③ tailscaled"
systemctl enable --now tailscaled
for i in $(seq 1 15); do tailscale status --json >/dev/null 2>&1 && break; sleep 1; done

echo "④ tailnet 에 붙기 (--hostname $HOSTNAME_TS)"
if tailscale status --json 2>/dev/null | grep -Eq '"BackendState":[[:space:]]*"Running"'; then
  echo "이미 붙어 있다 — up 을 건너뛴다 (키는 쓰지 않고 지운다)"
else
  grep -q '^tskey-' "$KEYFILE" || { echo "stdin 에 인증 키(tskey-…)가 없다" >&2; exit 1; }
  tailscale up --auth-key="file:$KEYFILE" --hostname="$HOSTNAME_TS"
fi

echo "끝. 이 서버의 tailnet IPv4:"
tailscale ip -4
