---
title: 자원 정리
description: 비용이 나가는 Lightsail·GitHub·IAM 자원을 순서대로 지우는 절차 — 작업용 서버(54.252.22.31)는 ③으로 전부 지우기, 교수님 서버는 ①(paperclf 만 걷어내기), 인스턴스 전체 삭제 ②는 참고
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

- **2026-11-19 작업 분리**: R1~R5 는 연구자의 작업용 서버 `Amazon_Linux_2026_kms`(고정 IP `54.252.22.31`)에서 한다 → 지울 때는 **③ 작업용 서버·AWS 계정 정리**. 아래 ①·②는 교수님 서버 `13.237.237.56`(eta 공용)에 올렸을 때의 절차다 — [R1](../requirements/R1-lightsail.md).
- 서버 `13.237.237.56`(시드니 `ap-southeast-2`)은 강의 앱 eta 와 **공용**이다. 결정 [ADR-007](../decisions/ADR-007-region-instance.md): 인스턴스·고정 IP 는 지우지 않고 **paperclf 자원만** 지운다.
- 그래서 두 갈래다. **① 기본 — paperclf 만 걷어내기**를 쓴다. **② 참고 — 인스턴스 전체 삭제**는 eta 운영자와 합의했을 때만 쓴다.
- 순서는 강의 03 › 6 지우기(러너 → 인스턴스 → 고정 IP → 버킷 → 키 페어·저장소 변수, 만든 순서의 거꾸로)를 따른다 — [강의 자료 색인](../sources/lecture-index.md). ①은 인스턴스·고정 IP 대신 [`bootstrap.sh`](../deploy/lightsail/bootstrap.sh) ①~④를 거꾸로 되돌린다.
- 이름은 `bootstrap.sh` 의 실제 값이다: 러너 폴더 `~/actions-runner-paperclf`, 러너 이름 `paperclf`(이름표 `lightsail,paperclf`), 앱 폴더 `/srv/paperclf`, Caddy 폴더 `/srv/caddy`, eta 덮어쓰기 파일 `/srv/eta/compose.override.yml`. 버킷 이름 `paperclf-models-apse2` 는 제안값이다 — 실제 값은 `gh variable get MODEL_BUCKET -R metahomo/miniproject5_kms` 로 먼저 확인하고 다르면 바꿔 친다.
- "PC" 는 `gh` 에 로그인된 내 컴퓨터, "SSH" 는 Lightsail 콘솔의 브라우저 SSH(`ec2-user`)다.
- GHCR 이미지와 저장소는 지우지 않는다(강의 03 › 6 과 같음).

## 절차 ① 기본 — paperclf 만 걷어내기

| # | 단계 | 어디서 | 명령·화면 | 기대 결과 |
|---|---|---|---|---|
| 1 | 배포 멈추기 | PC (gh CLI) | `gh variable set DEPLOY_ENABLED --body false -R metahomo/miniproject5_kms` — 이후 deploy·promote·rollback 잡이 서버 러너로 가지 않는다 | `gh variable get DEPLOY_ENABLED -R metahomo/miniproject5_kms` → `false`. `gh run list -R metahomo/miniproject5_kms --status in_progress` → 빈 목록 |
| 2 | 러너 제거 토큰 받기 | PC (gh CLI) | `gh api -X POST repos/metahomo/miniproject5_kms/actions/runners/remove-token -q .token` — 출력된 토큰을 복사(약 1시간 유효) | 토큰 한 줄이 나온다 |
| 3 | 러너 지우기 | SSH | `cd ~/actions-runner-paperclf && sudo ./svc.sh stop && sudo ./svc.sh uninstall`<br>`./config.sh remove --token <제거 토큰>`<br>`cd ~ && rm -rf ~/actions-runner-paperclf` — 다른 러너 폴더(eta 것)는 건드리지 않는다 | PC: `gh api repos/metahomo/miniproject5_kms/actions/runners -q .total_count` → `0`. SSH: `systemctl list-units 'actions.runner.*' --no-legend \| grep -c paperclf` → `0` |
| 4 | 장부 DB 마지막 덤프 → 버킷 ([ADR-008](../decisions/ADR-008-ledger-db-ops.md)) | 장부 DB 가 도는 곳(PC 의 `miniproject5-db` 컨테이너) + Lightsail 콘솔 | `docker exec miniproject5-db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > ledger-$(date +%Y%m%d).dump`<br>콘솔 → 스토리지 → `paperclf-models-apse2` → 객체 → 업로드 → `ledger/` 아래에 이 파일. 버킷은 9단계에서 사라지므로 **PC 의 파일은 남겨 둔다** | `pg_restore --list ledger-$(date +%Y%m%d).dump \| head` 가 목차(테이블 4·뷰 2)를 보인다. 콘솔 객체 목록에 `ledger/ledger-<날짜>.dump` |
| 5 | paperclf 앱 내리기 | SSH | `cd /srv/paperclf && docker compose down`<br>`docker images --format '{{.Repository}}:{{.Tag}}' \| grep '/paperclf-api:' \| xargs -r docker rmi` | `curl -sS -m 3 localhost:8080/health` → 연결 거부. `docker ps --format '{{.Names}}' \| grep -c paperclf` → `0` |
| 6 | Caddy 내리기 (`bootstrap.sh` ③의 반대) | SSH | `cd /srv/caddy && docker compose down -v` — 80/443 이 비고, 인증서 볼륨도 지운다. 이 순간부터 7단계까지 eta 가 잠깐 끊긴다 | `docker ps --format '{{.Names}}' \| grep -c caddy` → `0`. `docker volume ls -q \| grep -c '^caddy_'` → `0` |
| 7 | eta 를 원래대로 80 직접 (`bootstrap.sh` ②의 반대) | SSH | `[ -f /srv/eta/compose.override.yml ] && rm /srv/eta/compose.override.yml`<br>`cd /srv/eta && docker compose up -d` — eta 의 `compose.yml` 포트로 다시 만든다 | SSH: `docker ps --format '{{.Names}} {{.Ports}}'` 에 eta 가 `0.0.0.0:80->8080/tcp`. PC: `curl -fsS http://13.237.237.56/health` → eta 의 응답. `curl -sSI http://13.237.237.56/health \| grep -ic caddy` → `0` |
| 8 | 폴더 지우기 (`bootstrap.sh` ①의 반대) | SSH | `sudo rm -rf /srv/paperclf /srv/caddy` | `ls -d /srv/paperclf /srv/caddy` → 둘 다 `No such file or directory`. `ls /srv` 에 `eta` 는 남아 있다 |
| 9 | 버킷 | Lightsail 콘솔 | 스토리지 → `paperclf-models-apse2` → 삭제 → 「이 버킷 삭제의 영향을 이해합니다」 체크 → **강제 삭제**(객체째). 인스턴스에 붙인 버킷 접근 권한도 함께 사라진다 | 콘솔 스토리지에 이 버킷이 없다. SSH: `aws s3 ls s3://paperclf-models-apse2 --region ap-southeast-2` → `NoSuchBucket` |
| 10 | 키 페어 | — (지우지 않음) | 인스턴스의 SSH 키(`eta-deploy`)는 eta 와 같이 쓰므로 둔다. paperclf 는 self-hosted 러너라 따로 만든 SSH 키·GitHub 비밀값이 없다 | PC: `gh secret list -R metahomo/miniproject5_kms` → 빈 목록 |
| 11 | 저장소 변수 | PC (gh CLI) 또는 GitHub → Settings → Secrets and variables → Actions → Variables | `for v in DEPLOY_ENABLED MODEL_BUCKET AWS_REGION; do gh variable delete $v -R metahomo/miniproject5_kms; done` | `gh variable list -R metahomo/miniproject5_kms` → 빈 목록 |

인스턴스와 고정 IP 는 그대로이므로 고정 IP 는 계속 인스턴스에 붙어 있다(붙어 있는 동안 요금 0).

## 절차 ② 참고 — 인스턴스 전체 삭제

> ⚠️ **경고 — eta 운영자와 합의했을 때만.** 인스턴스를 지우면 같은 서버의 강의 앱 eta 도 함께 사라지고 되돌릴 수 없다. 고정 IP `13.237.237.56` 을 지우면 같은 주소는 다시 받을 수 없어 도메인 `nlpwizard.eta.pyhub.kr` 의 A 레코드도 쓸모가 없어진다. 합의가 없으면 ①만 한다.

| # | 단계 | 어디서 | 명령·화면 | 기대 결과 |
|---|---|---|---|---|
| 1 | 배포 멈추기·러너 지우기·장부 덤프 | PC·SSH·콘솔 | ①의 1~4단계를 그대로 한다(러너는 서버보다 먼저 풀어야 GitHub 에 죽은 러너가 남지 않는다). 버킷이 지워지므로 덤프는 PC 에 둔다 | ①의 1~4단계 기대 결과와 같다 |
| 2 | 인스턴스 | Lightsail 콘솔 (시드니) | 인스턴스 → 고정 IP `13.237.237.56` 이 붙은 인스턴스 → 삭제 → 「…내 계정에 유지된다는 점을 이해합니다」 체크 → 확인 칸에 `확인` → **인스턴스 삭제** | 콘솔 인스턴스 화면이 빈 안내. PC: `curl -sS -m 5 http://13.237.237.56/health` → 시간 초과 |
| 3 | 고정 IP | Lightsail 콘솔 | 네트워킹 → `13.237.237.56` 의 고정 IP → 삭제 탭 → **고정 IP 삭제** → 「예, 삭제」. 떼어 둔 채 두면 1시간 뒤부터 시간당 0.005 USD | 콘솔 네트워킹에 고정 IP 가 없다 |
| 4 | 버킷 | Lightsail 콘솔 | ①의 9단계와 같다(강제 삭제) | 콘솔 스토리지가 빈 안내 |
| 5 | 키 페어 | Lightsail 콘솔 + PC | 오른쪽 위 계정 → SSH 키 → `eta-deploy` 휴지통. PC: `rm eta-deploy.pem` (Windows: `Remove-Item .\eta-deploy.pem`) | 콘솔 SSH 키 목록에 `eta-deploy` 가 없다. `ls eta-deploy.pem` → 없음 |
| 6 | 저장소 변수 | PC (gh CLI) | ①의 11단계와 같다 | `gh variable list -R metahomo/miniproject5_kms` → 빈 목록 |

## 절차 ③ 작업용 서버·AWS 계정 정리 (54.252.22.31)

작업용 서버는 연구자 혼자 쓰므로 인스턴스째 지운다. 리전은 모두 시드니 `ap-southeast-2`. 서버 설정은 [작업용 서버 런북](./work-server.md) 참고.

| # | 단계 | 어디서 | 명령·화면 | 기대 결과 |
|---|---|---|---|---|
| 1 | 배포 멈추기·러너 지우기 | PC·SSH | ①의 1~3단계를 그대로 한다. SSH 는 작업용 서버(`54.252.22.31`)로 | ①의 1~3단계 기대 결과와 같다 |
| 1-1 | 장부 마지막 백업 → PC (2026-11-19 부터 장부는 서버 `/srv/ledger`) | SSH·PC | SSH: `python3 /srv/ledger/ledger.py backup` · `sudo systemctl disable --now paperclf-ledger-backup.timer`<br>SSH: `aws s3 cp --recursive s3://paperclf-models-apse2/ledger/ /tmp/ledger/`<br>PC: `scp -r ec2-user@54.252.22.31:/tmp/ledger ./ledger-backup` — 버킷은 3단계에서 사라지므로 **PC 에 남긴다** | PC `ledger-backup/` 에 `ledger-<시각>.sql.gz` 가 있고 `gunzip -c … \| head` 에 `CREATE TABLE` |
| 1-2 | 장부 DB 내리기 | SSH | `cd /srv/ledger && docker compose down -v` | `docker ps --format '{{.Names}}' \| grep -c paperclf-ledger` → `0` |
| 2 | Tailscale 기기 제거·인증 키 폐기 (설치했을 때만) | SSH + Tailscale 관리 화면 | SSH: `sudo tailscale logout`<br>관리 화면 → Machines → 작업용 서버 기기 → … → **Remove**. Settings → Keys → 서버 등록에 쓴 auth key → **Revoke** | 관리 화면 Machines 에 이 기기가 없고, Keys 에 살아 있는 키가 없다 |
| 3 | 프로젝트 버킷 | Lightsail 콘솔 | 스토리지 → 프로젝트 버킷(`gh variable get MODEL_BUCKET -R metahomo/miniproject5_kms` 로 이름 확인) → 삭제 → **강제 삭제**(객체째) | 콘솔 스토리지가 빈 안내 |
| 4 | 인스턴스 | Lightsail 콘솔 | 인스턴스 → `Amazon_Linux_2026_kms` → 삭제 → 확인 → **인스턴스 삭제** | 콘솔 인스턴스 화면이 빈 안내. PC: `curl -sS -m 5 http://54.252.22.31/` → 시간 초과 |
| 5 | 고정 IP `StaticIp-1` | Lightsail 콘솔 | 네트워킹 → `StaticIp-1`(`54.252.22.31`) → 삭제 탭 → **고정 IP 삭제**. 인스턴스가 지워져 떼어진 채 두면 1시간 뒤부터 시간당 0.005 USD | 콘솔 네트워킹에 고정 IP 가 없다 |
| 6 | 키 페어 `miniproject5` | Lightsail 콘솔 + PC | 오른쪽 위 계정 → SSH 키 → `miniproject5` 휴지통. PC 의 개인 키 파일(`.pem`)도 지운다. `LightsailDefaultKeyPair` 는 Lightsail 기본 키라 둔다 | 콘솔 SSH 키 목록에 `miniproject5` 가 없다 |
| 7 | 저장소 변수 | PC (gh CLI) | ①의 11단계와 같다 | `gh variable list -R metahomo/miniproject5_kms` → 빈 목록 |
| 8 | IAM 접근 키 | IAM 콘솔 | 사용자 → `paperclf-commander` → 보안 자격 증명 → 액세스 키 → 비활성화 → **삭제**. Mac 의 `~/.aws/credentials` 에서 이 키 항목도 지운다. 이 단계부터 Mac 의 AWS CLI 는 쓸 수 없으므로 **1~7단계를 먼저** 끝낸다 | 사용자의 액세스 키 목록이 빈 안내 |
| 9 | IAM 사용자 | IAM 콘솔 | 사용자 → `paperclf-commander` → **삭제** → 이름 입력 → 삭제 | 사용자 목록에 `paperclf-commander` 가 없다 |
| 10 | IAM 정책 | IAM 콘솔 | 정책 → 필터 "고객 관리형" → `paperclf-lightsail` → **삭제** → 이름 입력 → 삭제. 사용자를 먼저 지워야 연결이 풀려 지워진다 | 고객 관리형 정책 목록에 `paperclf-lightsail` 이 없다 |

조직 SCP 가 `ap-southeast-2`·`us-east-1` 외 리전을 막으므로, 확인할 리전은 이 둘뿐이다.

저장소 쪽 덤으로 정리할 것(선택): 쓰지 않는 `gh-pages` 브랜치와 GitHub Pages(`gh api -X DELETE repos/metahomo/miniproject5_kms/pages`, `git push origin --delete gh-pages`), 연구자 PC 의 예약 작업 `birdseye-pull`(`schtasks /Delete /TN birdseye-pull /F`).

## 확인

PC 에서 한 번에:

```sh
R=metahomo/miniproject5_kms
gh api repos/$R/actions/runners -q .total_count   # 0
gh variable list -R $R                             # 빈 목록
gh secret list -R $R                               # 빈 목록
curl -fsS http://13.237.237.56/health              # ① eta 응답 / ② 시간 초과
curl -sSI http://13.237.237.56/health | grep -ic caddy   # ① 0
```

Lightsail 콘솔(시드니)에서 스토리지에 `paperclf-models-apse2` 가 없고, ②·③을 했다면 인스턴스·네트워킹·스토리지·스냅샷 네 화면이 모두 빈 안내인지 본다. 다른 리전에 만든 자원이 없는지도 리전 메뉴로 확인한다. ③을 했다면 IAM 콘솔에 `paperclf-commander` 사용자와 `paperclf-lightsail` 정책이 없는지 본다.
