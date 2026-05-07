요청하신 **시스템 관제 및 자동화 스크립트 개발** 미션 내용을 가독성 있게 정리한 Markdown 문서입니다.

---

# 🚀 미션: 시스템 관제 자동화 스크립트 개발

## 1. 미션 소개
서버 장애 발생 시 로그가 없다면 원인 분석은 '감'에 의존하게 됩니다. 이는 복구 시간을 지연시키고 동일한 장애를 반복하게 만듭니다. 본 미션은 **권한 관리, 네트워크 보안, 로그 자동화**를 통해 실제 엔지니어처럼 서버 운영 환경을 설계하고 구축하는 것을 목표로 합니다.

단순 암기가 아닌, 개발 커리어 내내 활용 가능한 **안정적인 서버 운영 및 리소스 관제 역량**을 확보하는 실무형 미션입니다.

---

## 2. 최종 결과물 (제출 산출물)
1.  **요구사항 수행 내역서 (문서 1개)**
    * 설정/명령어 기록 (SSH, 방화벽, 계정/권한, cron 등)
    * **필수 증거 자료 체크리스트:**
        * SSH 포트 변경(20022) 및 Root 접속 차단 확인
        * 방화벽(UFW/firewalld) 활성화 및 허용 포트(20022, 15034) 확인
        * 계정 및 그룹 생성 내역
        * 디렉토리 구조 및 ACL 권한 확인
        * 앱 Boot Sequence 5단계 [OK] 및 "Agent READY" 출력 화면
        * `monitor.sh` 실행 결과 및 `/var/log/agent-app/monitor.log` 누적 기록
        * crontab 매분 실행 등록 확인
2.  **자동화 스크립트 소스코드**
    * `monitor.sh`: 시스템 상태 수집 및 로깅 스크립트

---

## 3. 과제 목표
* SSH 보안 설정(포트 변경, Root 차단)의 중요성 이해
* 방화벽 정책(필요 포트 최소 허용) 구성 및 검증
* 역할 기반 권한 관리(RBAC) 및 ACL을 활용한 디렉토리 보안
* 환경 변수를 통한 실행 환경 고정 및 관리
* Bash 쉘 스크립트를 활용한 시스템 리소스 모니터링 및 로깅 자동화

---

## 4. 기능 요구 사항

### 🛡️ 기본 보안 및 네트워크 설정
* **SSH 설정:** 접속 포트 **20022**로 변경, Root 원격 로그인 차단
* **방화벽 설정:** UFW 또는 firewalld 활성화
    * 인바운드 허용: **TCP 20022(SSH)**, **TCP 15034(APP)**만 허용

### 👥 계정/그룹 및 권한 체계
* **계정 생성:** `agent-admin`(운영), `agent-dev`(개발), `agent-test`(QA)
* **그룹 구성:**
    * `agent-common`: 모든 계정 포함
    * `agent-core`: `admin`, `dev` 포함
* **디렉토리 및 권한:**
    * `upload_files`: `agent-common` 그룹 R/W 가능
    * `api_keys` & `/var/log/agent-app`: `agent-core` 그룹만 R/W 가능

### ⚙️ 애플리케이션 실행 환경
* **환경 변수:** `AGENT_HOME`, `AGENT_PORT(15034)`, `AGENT_LOG_DIR` 등 설정
* **키 파일:** `$AGENT_HOME/api_keys/t_secret.key` (내용: `agent_api_key_test`)
* **실행 기준:** 일반 계정 실행 필수, Boot Sequence 5단계 통과 및 LISTEN 상태 확인

### 📊 시스템 관제 스크립트 (`monitor.sh`)
* **위치/권한:** `$AGENT_HOME/bin/monitor.sh`, 소유자 `agent-dev`, 권한 `750`
* **Health Check:** 프로세스 생존 및 포트(15034) 상태 확인 (실패 시 `exit 1`)
* **자원 수집:** CPU, Memory, Disk 사용률 측정
* **임계값 경고:**
    * `CPU > 20%`, `MEM > 10%`, `DISK > 80%` 시 **[WARNING]** 출력
* **로그 관리:**
    * 형식: `[YYYY-MM-DD HH:MM:SS] PID:... CPU:..% MEM:..% DISK_USED:..%`
    * 로테이션: 최대 10MB, 파일 10개 유지

---

## 5. 보너스 과제 (선택)
1.  **`report.sh` 개발:** 로그를 분석하여 자원 사용량의 평균/최대/최소 및 샘플 수 출력
2.  **로그 보존 정책:**
    * 7일 경과 로그: 자동 압축 및 아카이브 이동
    * 30일 경과 아카이브: 자동 삭제

---

## 6. 개발 환경 및 제약 사항
* **OS:** Ubuntu 22.04 LTS (또는 동등 환경)
* **언어:** 자동화 스크립트는 **오직 Bash**로만 작성 (Python 사용 금지)
* **권한:** 필요한 경우에만 `sudo` 사용, 가급적 일반 계정으로 수행

---

## 7. 결과 예시

### [앱 실행 화면]
```text
Starting Agent Boot Sequence...
[1/5] Checking User Account               [OK]
... Running as service user 'agent-admin' (uid=1001)
[2/5] Verifying Environment Variables     [OK]
[3/5] Checking Required Files             [OK]
[4/5] Checking Port Availability          [OK]
[5/5] Verifying Log Permission            [OK]
All Boot Checks Passed!
Agent READY
```

### [monitor.sh 실행 및 로그]
```text
====== SYSTEM MONITOR RESULT ======
[HEALTH CHECK]
Checking process 'agent_app.py'... [OK] (PID: 48291)
Checking port 15034... [OK]

[RESOURCE MONITORING]
CPU Usage : 25.3% [WARNING]
MEM Usage : 5.2%
DISK Used  : 23%

[INFO] Log appended: /var/log/agent-app/monitor.log
```