---
title: 자원 정리
description: 비용이 나가는 Lightsail·GitHub·IAM 자원을 순서대로 지우는 절차 — 최종 서버(54.253.32.153)는 ①, 작업용 서버(54.252.22.31)는 ③
tags:
  - runbook
  - aws
requirement: R1
---
# 자원 정리

요구사항: [R1 Lightsail](../requirements/R1-lightsail.md)

## 언제 쓰나

과제 제출·시연이 끝난 뒤.

## 먼저 알 것

- 처음 계획한 `13.237.237.56`(교수님/강의 eta 서버)은 쓰지 않았다 — [ADR-003](../decisions/ADR-003-domain-server.md) 갱신 절.
- 서버는 둘이다. **최종 서버** = Lightsail `Amazon_Linux_2023-1`(시드니 `ap-southeast-2`, 고정 IP `paperclf-final-ip` = `54.253.32.153`, 연구자 프로젝트 계정) → **절차 ①**. **작업용 서버** = `Amazon_Linux_2026_kms`(고정 IP `54.252.22.31`, 작업용 서버 계정) → **절차 ③**. 두 서버는 AWS 계정이 다르다. 설정은 [최종 서버 런북](./final-server.md)·[작업용 서버 런북](./work-server.md).
- 최종 서버에는 eta 가 없고 버킷·장부 DB 도 없다(통과 판 폴더의 `validated.json` 만). 그래서 ①에는 버킷·덤프 단계가 없다.
- 순서는 강의 03 › 6 지우기(러너 → 인스턴스 → 고정 IP → 버킷 → 키 페어·저장소 변수, 만든 순서의 거꾸로)를 따른다 — [강의 자료 색인](../sources/lecture-index.md). 서버 안은 [`bootstrap.sh`](../deploy/lightsail/bootstrap.sh) ①~④ 를 거꾸로 되돌린다.
- 이름은 `bootstrap.sh` 의 실제 값이다. 최종 서버: 러너 폴더 `~/actions-runner-paperclf`, 러너 `paperclf-final`(이름표 `final`, 서비스 `actions.runner.metahomo-miniproject5_kms.paperclf-final`), 앱 `/srv/paperclf`, Caddy `/srv/caddy`(`/srv/caddy/kms.hash` = KMS 접속 암호 해시). 작업용 서버: 러너 `paperclf`(이름표 `lightsail,paperclf`). 버킷 이름은 `gh variable get MODEL_BUCKET -R metahomo/miniproject5_kms` 로 먼저 확인한다.
- 저장소 변수: `FINAL_ENABLED=true` 가 `*-final` 잡(deploy-final·promote-final·rollback-final)을 켠다. 작업용은 `DEPLOY_ENABLED`·`MODEL_BUCKET`·`AWS_REGION`.
- KMS 웹은 Mac 서버에서 돌고, Mac 의 루프 스크립트가 역방향 SSH 터널(`ssh … -R 127.0.0.1:10011:127.0.0.1:10001`)을 연다. 최종 서버용 `~/.claude/autonomy/kms-tunnel-final-loop.sh`(pid `~/.claude/autonomy/kms-tunnel-final.pid`), 작업용 서버용 `~/.claude/autonomy/kms-tunnel-loop.sh`(pid `~/.claude/autonomy/kms-tunnel.pid`).
- SSH 22번은 2026-11-20 부터 Mac/연구자 공인 IP 하나와 Lightsail 브라우저 SSH 에만 열려 있다(두 서버 모두). 이미 좁혀져 있으니 정리할 때 Lightsail 콘솔 → 네트워킹 → 방화벽에서 확인만 한다.
- "PC" 는 `gh` 에 로그인된 내 컴퓨터, "SSH" 는 Lightsail 콘솔의 브라우저 SSH(`ec2-user`), "Mac" 은 KMS 웹이 도는 Mac 서버다.
- GHCR 이미지와 저장소는 지우지 않는다(강의 03 › 6 과 같음).
- **고정 IP `paperclf-final-ip` 는 발표 끝까지 지우지 않는다**(연구자 결정). 도메인 `nlpwizard.eta.pyhub.kr` 이 이 IP 를 가리킨다.

## 절차 ① 최종 서버(54.253.32.153) 정리

만든 순서의 거꾸로. 1~6단계는 서버 안의 paperclf·Caddy 를 걷어내는 일이고, 7~8단계(인스턴스·고정 IP 삭제)는 **발표가 끝난 뒤 연구자가 정할 때만** 한다. 리전은 시드니 `ap-southeast-2`, 계정은 연구자 프로젝트 계정이다.

| # | 단계 | 어디서 | 명령·화면 | 기대 결과 |
|---|---|---|---|---|
| 1 | 최종 배포 끄기 | PC (gh CLI) | `gh variable set FINAL_ENABLED --body false -R metahomo/miniproject5_kms` — 이후 `*-final` 잡이 건너뛰어진다 | `gh variable get FINAL_ENABLED -R metahomo/miniproject5_kms` → `false`. `gh run list -R metahomo/miniproject5_kms --status in_progress` → 빈 목록 |
| 2 | Mac KMS 터널 끄기 (최종 서버용) | Mac | `kill "$(cat ~/.claude/autonomy/kms-tunnel-final.pid)"` — 루프 스크립트를 먼저 끈다(안 그러면 ssh 만 지워도 다시 열린다)<br>`pkill -f 'ssh .*ec2-user@54.253.32.153 .*-R 127.0.0.1:10011'` — 최종 서버로 가는 ssh 프로세스만. 작업용 서버용 터널은 건드리지 않는다 | Mac: `pgrep -fl kms-tunnel-final-loop` → 출력 없음. `pgrep -fl '54.253.32.153'` → 출력 없음 |
| 3 | 러너 `paperclf-final` 지우기 | PC → SSH | PC: `gh api -X POST repos/metahomo/miniproject5_kms/actions/runners/remove-token -q .token` — 토큰 한 줄 복사(약 1시간 유효, 채팅·파일에 붙이지 않는다)<br>SSH: `cd ~/actions-runner-paperclf && sudo ./svc.sh stop && sudo ./svc.sh uninstall`<br>SSH: `./config.sh remove --token <제거 토큰>`<br>SSH: `cd ~ && rm -rf ~/actions-runner-paperclf` | PC: `gh api repos/metahomo/miniproject5_kms/actions/runners -q '.runners[].name'` 에 `paperclf-final` 없음. SSH: `systemctl list-units 'actions.runner.*' --no-legend \| grep -c paperclf-final` → `0` |
| 4 | paperclf 앱 내리기 | SSH | `cd /srv/paperclf && docker compose down`<br>`docker images --format '{{.Repository}}:{{.Tag}}' \| grep '/paperclf-api:' \| xargs -r docker rmi` | SSH: `curl -sS -m 3 localhost:8080/health` → 연결 거부. `docker ps --format '{{.Names}}' \| grep -c paperclf` → `0` |
| 5 | Caddy 내리기 (`bootstrap.sh` ③의 반대) | SSH | `cd /srv/caddy && docker compose down -v` — 80/443 이 비고 인증서 볼륨도 지운다. 이 순간부터 도메인이 응답하지 않는다 | SSH: `docker ps --format '{{.Names}}' \| grep -c caddy` → `0`. `docker volume ls -q \| grep -c '^caddy_'` → `0`. PC: `curl -sS -m 5 https://nlpwizard.eta.pyhub.kr/health` → 시간 초과 또는 연결 거부 |
| 6 | 폴더 지우기 (`bootstrap.sh` ①의 반대) | SSH | `sudo rm -rf /srv/paperclf /srv/caddy` — `/srv/caddy/kms.hash`(KMS 접속 암호 해시)와 `.env` 도 함께 사라진다 | SSH: `ls -d /srv/paperclf /srv/caddy` → 둘 다 `No such file or directory` |
| 7 | (발표 뒤, 연구자 결정 시) 인스턴스 삭제 | Lightsail 콘솔 (시드니, 연구자 프로젝트 계정) | 인스턴스 → `Amazon_Linux_2023-1` → 삭제 → 확인 → **인스턴스 삭제**. 1~6단계를 먼저 끝낸다(러너를 서버보다 먼저 풀어야 GitHub 에 죽은 러너가 남지 않는다) | 콘솔 인스턴스 화면에 이 인스턴스가 없다. PC: `curl -sS -m 5 http://54.253.32.153/health` → 시간 초과 |
| 8 | 고정 IP `paperclf-final-ip` 삭제 | Lightsail 콘솔 | 네트워킹 → `paperclf-final-ip`(`54.253.32.153`) → 삭제 탭 → **고정 IP 삭제** → 「예, 삭제」. 떼어 둔 채 두면 1시간 뒤부터 시간당 0.005 USD | 콘솔 네트워킹에 `paperclf-final-ip` 가 없다 |
| 9 | 키 페어 | Lightsail 콘솔 (확인만) | 오른쪽 위 계정 → SSH 키 목록을 본다. paperclf 는 self-hosted 러너라 따로 만든 SSH 키·GitHub 비밀값이 없다. Mac 사령관 공개키는 인스턴스의 `~/.ssh/authorized_keys` 에만 있어 인스턴스와 함께 사라진다. 키 페어는 지우지 않는다 | PC: `gh secret list -R metahomo/miniproject5_kms` → 빈 목록 |

> ⚠️ **7·8단계 전에 연구자가 도메인 A 레코드를 어떻게 할지 먼저 정한다.** 고정 IP `54.253.32.153` 을 지우면 같은 주소는 다시 받을 수 없고, 도메인 `nlpwizard.eta.pyhub.kr` 의 A 레코드(연구자가 DNS 관리)가 없는 주소를 가리키게 된다. 고정 IP 는 발표 끝까지 지우지 않는다. 새 주소로 바꿀지·레코드를 지울지 정한 뒤에 8단계를 한다.

저장소 변수(`FINAL_ENABLED` 포함)는 두 서버 정리를 마친 뒤 ③의 7단계에서 한꺼번에 지운다.

## 절차 ③ 작업용 서버·AWS 계정 정리 (54.252.22.31)

작업용 서버는 연구자 혼자 쓰므로 인스턴스째 지운다. 리전은 모두 시드니 `ap-southeast-2`. 서버 설정은 [작업용 서버 런북](./work-server.md) 참고. 최종 서버(①)와는 다른 AWS 계정이다.

| # | 단계 | 어디서 | 명령·화면 | 기대 결과 |
|---|---|---|---|---|
| 1 | 배포 멈추기·러너 지우기·Mac KMS 터널 끄기 | PC·Mac·SSH | PC: `gh variable set DEPLOY_ENABLED --body false -R metahomo/miniproject5_kms`<br>Mac: `kill "$(cat ~/.claude/autonomy/kms-tunnel.pid)"` 로 작업용 서버용 루프를 끄고 `pkill -f 'ssh .*ec2-user@54.252.22.31 .*-R 127.0.0.1:10011'` — 최종 서버용 터널은 건드리지 않는다<br>PC: `gh api -X POST repos/metahomo/miniproject5_kms/actions/runners/remove-token -q .token`<br>SSH(작업용 서버 `54.252.22.31`): `cd ~/actions-runner-paperclf && sudo ./svc.sh stop && sudo ./svc.sh uninstall`, `./config.sh remove --token <제거 토큰>`, `cd ~ && rm -rf ~/actions-runner-paperclf` | `gh variable get DEPLOY_ENABLED -R metahomo/miniproject5_kms` → `false`. Mac: `pgrep -fl 'autonomy/kms-tunnel-loop.sh'` → 출력 없음, `pgrep -fl 'ec2-user@54.252.22.31 .*-R'` → 출력 없음. PC: `gh api repos/metahomo/miniproject5_kms/actions/runners -q '.runners[].name'` 에 `paperclf` 없음. SSH: `systemctl list-units 'actions.runner.*' --no-legend \| grep -c paperclf` → `0` |

## 절차 ③ 작업용 서버·AWS 계정 정리 (54.252.22.31)

작업용 서버는 연구자 혼자 쓰므로 인스턴스째 지운다. 리전은 모두 시드니 `ap-southeast-2`. 서버 설정은 [작업용 서버 런북](./work-server.md) 참고.

| # | 단계 | 어디서 | 명령·화면 | 기대 결과 |
|---|---|---|---|---|
| 1-1 | 장부 마지막 백업 → PC (2026-11-19 부터 장부는 서버 `/srv/ledger`) | SSH·PC | SSH: `python3 /srv/ledger/ledger.py backup` · `sudo systemctl disable --now paperclf-ledger-backup.timer`<br>SSH: `aws s3 cp --recursive s3://paperclf-models-apse2/ledger/ /tmp/ledger/`<br>PC: `scp -r ec2-user@54.252.22.31:/tmp/ledger ./ledger-backup` — 버킷은 3단계에서 사라지므로 **PC 에 남긴다** | PC `ledger-backup/` 에 `ledger-<시각>.sql.gz` 가 있고 `gunzip -c … \| head` 에 `CREATE TABLE` |
| 1-2 | 장부 DB 내리기 | SSH | `cd /srv/ledger && docker compose down -v` | `docker ps --format '{{.Names}}' \| grep -c paperclf-ledger` → `0` |
| 2 | Tailscale 기기 제거·인증 키 폐기 (설치했을 때만) | SSH + Tailscale 관리 화면 | SSH: `sudo tailscale logout`<br>관리 화면 → Machines → 작업용 서버 기기 → … → **Remove**. Settings → Keys → 서버 등록에 쓴 auth key → **Revoke** | 관리 화면 Machines 에 이 기기가 없고, Keys 에 살아 있는 키가 없다 |
| 3 | 프로젝트 버킷 | Lightsail 콘솔 | 스토리지 → 프로젝트 버킷(`gh variable get MODEL_BUCKET -R metahomo/miniproject5_kms` 로 이름 확인) → 삭제 → **강제 삭제**(객체째) | 콘솔 스토리지가 빈 안내 |
| 4 | 인스턴스 | Lightsail 콘솔 | 인스턴스 → `Amazon_Linux_2026_kms` → 삭제 → 확인 → **인스턴스 삭제** | 콘솔 인스턴스 화면이 빈 안내. PC: `curl -sS -m 5 http://54.252.22.31/` → 시간 초과 |
| 5 | 고정 IP `StaticIp-1` | Lightsail 콘솔 | 네트워킹 → `StaticIp-1`(`54.252.22.31`) → 삭제 탭 → **고정 IP 삭제**. 인스턴스가 지워져 떼어진 채 두면 1시간 뒤부터 시간당 0.005 USD | 콘솔 네트워킹에 고정 IP 가 없다 |
| 6 | 키 페어 `miniproject5` | Lightsail 콘솔 + PC | 오른쪽 위 계정 → SSH 키 → `miniproject5` 휴지통. PC 의 개인 키 파일(`.pem`)도 지운다. `LightsailDefaultKeyPair` 는 Lightsail 기본 키라 둔다 | 콘솔 SSH 키 목록에 `miniproject5` 가 없다 |
| 7 | 저장소 변수 | PC (gh CLI) 또는 GitHub → Settings → Secrets and variables → Actions → Variables | `for v in DEPLOY_ENABLED MODEL_BUCKET AWS_REGION FINAL_ENABLED; do gh variable delete $v -R metahomo/miniproject5_kms; done` — ①을 하지 않았어도 `FINAL_ENABLED` 가 없다는 오류는 무시한다 | `gh variable list -R metahomo/miniproject5_kms` → 빈 목록 |
| 8 | IAM 접근 키 | IAM 콘솔 | 사용자 → `paperclf-commander` → 보안 자격 증명 → 액세스 키 → 비활성화 → **삭제**. Mac 의 `~/.aws/credentials` 에서 이 키 항목도 지운다. 이 단계부터 Mac 의 AWS CLI 는 쓸 수 없으므로 **1~7단계를 먼저** 끝낸다 | 사용자의 액세스 키 목록이 빈 안내 |
| 9 | IAM 사용자 | IAM 콘솔 | 사용자 → `paperclf-commander` → **삭제** → 이름 입력 → 삭제 | 사용자 목록에 `paperclf-commander` 가 없다 |
| 10 | IAM 정책 | IAM 콘솔 | 정책 → 필터 "고객 관리형" → `paperclf-lightsail` → **삭제** → 이름 입력 → 삭제. 사용자를 먼저 지워야 연결이 풀려 지워진다 | 고객 관리형 정책 목록에 `paperclf-lightsail` 이 없다 |

조직 SCP 가 `ap-southeast-2`·`us-east-1` 외 리전을 막으므로, 확인할 리전은 이 둘뿐이다.

저장소 쪽 덤으로 정리할 것(선택): 쓰지 않는 `gh-pages` 브랜치와 GitHub Pages(`gh api -X DELETE repos/metahomo/miniproject5_kms/pages`, `git push origin --delete gh-pages`), 연구자 PC 의 예약 작업 `birdseye-pull`(`schtasks /Delete /TN birdseye-pull /F`).

## 확인

PC 에서 한 번에:

```sh
R=metahomo/miniproject5_kms
gh api repos/$R/actions/runners -q '.runners[].name'   # ①·③ 뒤: paperclf-final·paperclf 없음
gh variable list -R $R                                  # ③ 뒤: 빈 목록
gh secret list -R $R                                    # 빈 목록
curl -sS -m 5 https://nlpwizard.eta.pyhub.kr/health     # ① 5단계 뒤: 시간 초과 / 연결 거부
curl -sS -m 5 http://54.253.32.153/health               # ① 7단계 뒤: 시간 초과
curl -sS -m 5 http://54.252.22.31/                      # ③ 4단계 뒤: 시간 초과
```

Mac 에서: `pgrep -fl 'kms-tunnel'` → 출력 없음(두 터널 모두 끈 뒤).

Lightsail 콘솔(시드니)에서, 연구자 프로젝트 계정은 ①의 7~8단계를 했다면 인스턴스·네트워킹이 빈 안내인지, 작업용 서버 계정은 ③을 했다면 인스턴스·네트워킹·스토리지·스냅샷 네 화면이 빈 안내이고 스토리지에 `paperclf-models-apse2` 가 없는지 본다. 두 계정 모두 방화벽의 SSH 22번이 이미 좁혀져 있는지 네트워킹 → 방화벽에서 확인한다. 다른 리전에 만든 자원이 없는지도 리전 메뉴로 확인한다. ③을 했다면 IAM 콘솔에 `paperclf-commander` 사용자와 `paperclf-lightsail` 정책이 없는지 본다.
