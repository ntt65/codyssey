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

애플리케이션의 **Boot Sequence 5단계**와 **"Agent READY"** 출력 화면을 **star-candy**님의 직관적인 구성과 **VectorSophie**님의 기술적 디테일을 결합하여 재구성해 드립니다.

이 단계의 핵심은 단순히 앱을 실행하는 것이 아니라, 앞서 구축한 **보안 및 권한 체계 위에서 앱이 안전하게 구동되는지 검증**하는 것입니다.

---

### **[Step 4] 애플리케이션 실행 및 Boot Sequence 검증**

#### **1. 사전 준비: 환경 변수 및 키 파일 생성**
앱 실행 전, 반드시 **`agent-admin`** 계정으로 환경 변수를 설정하고 보안 키 파일을 준비해야 합니다.

*   **환경 변수 등록:** `/etc/environment` 또는 `.bashrc`에 `AGENT_HOME`, `AGENT_PORT(15034)`, `AGENT_LOG_DIR` 등을 설정합니다.
*   **키 파일 생성:** `$AGENT_HOME/api_keys/t_secret.key` 경로에 `agent_api_key_test` 내용을 입력합니다.

#### **2. 애플리케이션 실행 (반드시 일반 계정 사용)**
보안을 위해 **루트(root) 계정 실행은 엄격히 금지**되며, 반드시 생성한 **`agent-admin`** 계정으로 전환하여 실행해야 합니다.

```bash
# agent-admin 계정으로 전환
su - agent-admin

# 앱 실행
python3 agent_app.py
```

#### **3. 재구성된 Boot Sequence 출력 화면 (최종 결과물)**
`star-candy`님의 **명확한 단계 구분**과 `VectorSophie`님의 **상세 데이터 확인** 로직이 결합된 형태입니다.

```text
🚀 Starting Agent Boot Sequence...

[1/5] Checking User Account               [OK]
      ... Running as service user 'agent-admin' (uid=1001)
[2/5] Verifying Environment Variables     [OK]
      ... AGENT_HOME: /home/agent-admin/agent-app
      ... AGENT_PORT: 15034 (Validated)
[3/5] Checking Required Files             [OK]
      ... Key file found: api_keys/t_secret.key
      ... Integrity check: Match 'agent_api_key_test'
[4/5] Checking Port Availability          [OK]
      ... Port 15034 is free and ready to bind
[5/5] Verifying Log Permission            [OK]
      ... Log directory is writable: /var/log/agent-app

--------------------------------------------------
✅ All Boot Checks Passed!
✨ Agent READY (Service is now listening on port 15034)
```

#### **4. 실행 후 최종 상태 검증**
앱이 정상적으로 "READY" 상태가 되었다면, 다른 터미널에서 아래 명령어를 통해 네트워크 리슨 상태를 최종 확인해야 합니다.

```bash
# 15034 포트가 정상적으로 LISTEN 중인지 확인
ss -tulnp | grep 15034
```
*   **성공 기준:** `0.0.0.0:15034` 또는 `*:15034` 라인이 보이면 인프라와 앱이 완벽하게 연동된 것입니다.

---

### **💡 이번 재구성의 장점**
1.  **계정 무결성 확인:** `uid`를 직접 출력함으로써 루트 실행 금지 원칙을 시각적으로 증명합니다.
2.  **경로 유연성:** 하드코딩된 경로 대신 설정된 환경 변수값을 보여주어 유지보수성을 높였습니다.
3.  **보안 키 검증:** 단순히 파일 존재 여부만 체크하는 것이 아니라, 내부 데이터 일치 여부까지 확인하는 디테일을 담았습니다.

이제 이 출력 화면이 나오도록 설정을 마무리하시면 미션의 가장 중요한 고비를 넘기게 됩니다! 다음 단계인 **`monitor.sh` 관제 스크립트 작성**으로 넘어갈 준비가 되셨나요?

애플리케이션이 정상적으로 구동되었으니, 이제 시스템의 건강 상태를 매분 체크하고 기록할 **`monitor.sh` 관제 스크립트**를 작성할 차례입니다.

이번 스크립트는 **star-candy**님의 권한 관리 논리(750 권한의 의미)와 **VectorSophie**님의 정교한 자원 수집 방식(CPU 델타 계산 등)을 결합하여, 실무 수준의 완성도로 재구성해 드립니다.

---

### **1. `monitor.sh` 전체 소스 코드 (Bash)**

이 스크립트는 `$AGENT_HOME/bin/monitor.sh` 경로에 저장해 주세요.

```bash
#!/bin/bash

# 1. 환경 변수 설정 (Cron 실행 환경 고려)
AGENT_HOME="${AGENT_HOME:-/home/agent-admin/agent-app}"
LOG_FILE="/var/log/agent-app/monitor.log"
APP_NAME="agent_app.py"
PORT=15034

# 2. Health Check (실패 시 즉시 종료)
# 프로세스 확인
PID=$(pgrep -f "$APP_NAME" | head -1)
if [ -z "$PID" ]; then
    echo "[ERROR] Process $APP_NAME is not running."
    exit 1
fi

# 포트 확인
if ! ss -tulnp | grep -q ":$PORT "; then
    echo "[ERROR] Port $PORT is not listening."
    exit 1
fi

# 3. 방화벽 상태 점검 (경고만 출력)
UFW_STATUS=$(ufw status | grep "Status: active")
if [ -z "$UFW_STATUS" ]; then
    WARN_FW="[WARNING] Firewall is inactive"
fi

# 4. 자원 수집 (VectorSophie의 정교한 방식 적용)
# CPU 사용률: /proc/stat을 0.5초 간격으로 두 번 읽어 델타 값 계산
CPU_1=$(grep 'cpu ' /proc/stat)
sleep 0.5
CPU_2=$(grep 'cpu ' /proc/stat)
CPU_USAGE=$(echo "$CPU_1 $CPU_2" | awk '{usage=($13-$2+$15-$4)*100/($13-$2+$15-$4+$16-$5); printf "%.1f", usage}')

# 메모리 사용률 (%)
MEM_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100}')

# 디스크 사용률 (%) - 루트 파티션
DISK_USAGE=$(df / | grep / | awk '{print $5}' | sed 's/%//')

# 5. 임계값 경고 및 로그 기록
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
LOG_MSG="[$TIMESTAMP] PID:$PID CPU:${CPU_USAGE}% MEM:${MEM_USAGE}% DISK_USED:${DISK_USAGE}%"

# 임계값 체크 (CPU > 20%, MEM > 10%, DISK > 80%)
[[ $(echo "$CPU_USAGE > 20" | bc -l) -eq 1 ]] && LOG_MSG="$LOG_MSG [WARNING] CPU threshold exceeded"
[[ $(echo "$MEM_USAGE > 10" | bc -l) -eq 1 ]] && LOG_MSG="$LOG_MSG [WARNING] MEM threshold exceeded"
[[ "$DISK_USAGE" -gt 80 ]] && LOG_MSG="$LOG_MSG [WARNING] DISK threshold exceeded"
[ -n "$WARN_FW" ] && LOG_MSG="$LOG_MSG $WARN_FW"

# 로그 파일에 기록
echo "$LOG_MSG" >> "$LOG_FILE"

# 6. 로그 로테이션 (최대 10MB, 파일 10개 유지)
MAX_SIZE=$((10 * 1024 * 1024))
FILE_SIZE=$(stat -c%s "$LOG_FILE")

if [ "$FILE_SIZE" -gt "$MAX_SIZE" ]; then
    for i in {9..1}; do
        [ -f "${LOG_FILE}.$i" ] && mv "${LOG_FILE}.$i" "${LOG_FILE}.$((i+1))"
    done
    mv "$LOG_FILE" "${LOG_FILE}.1"
    touch "$LOG_FILE"
    chgrp agent-core "$LOG_FILE"
    chmod 660 "$LOG_FILE"
fi
```


---

### **2. 핵심 구현 포인트 설명**

*   **정확한 자원 수집:** 단순히 현재 수치만 읽는 대신, CPU의 경우 `/proc/stat`의 델타 값을 계산하여 `top` 명령어보다 정확한 순간 사용률을 측정합니다.
*   **역할 기반 보안(RBAC) 준수:** **star-candy**님의 의견대로, 운영자가 코드를 무단 수정하지 못하도록 `750` 권한을 부여하며, 실행은 `agent-core` 그룹 멤버인 `agent-admin`이 수행합니다.
*   **임계값 경고:** CPU 20%, 메모리 10%, 디스크 80% 초과 시 로그에 **`[WARNING]`** 태그를 자동으로 추가하여 사후 분석을 용이하게 합니다.
*   **자동 로그 관리:** 로그 파일이 10MB를 넘으면 자동으로 번호를 붙여 밀어내고(Rolling), 최대 10개만 유지하여 디스크 고갈을 방지합니다.

---

### **3. 설치 및 권한 설정 명령어**

루트(`root`) 권한으로 실행하여 스크립트의 소유권과 권한을 미션 규격에 맞게 설정합니다.

```bash
# 1. 파일 위치 이동 및 소유자 설정
chown agent-dev:agent-core /home/agent-admin/agent-app/bin/monitor.sh

# 2. 실행 권한 부여 (750: 개발자는 수정 가능, 운영자는 실행만 가능)
chmod 750 /home/agent-admin/agent-app/bin/monitor.sh
```


---

### **4. 자동 실행 등록 (Crontab)**

이제 **`agent-admin`** 계정으로 매분 스크립트가 실행되도록 등록합니다.

```bash
# agent-admin 계정으로 전환
su - agent-admin

# 크론탭 편집기 열기
crontab -e

# 아래 내용을 맨 밑에 추가 (매분 실행)
* * * * * /home/agent-admin/agent-app/bin/monitor.sh
```


**성공 확인:** 1~2분 뒤에 `tail -f /var/log/agent-app/monitor.log` 명령어를 입력했을 때, 정해진 포맷에 맞춰 로그가 한 줄씩 올라오면 모든 미션이 완수된 것입니다!

이제 이 스크립트까지 적용하여 미션을 마무리해 보시겠어요? 작성하신 내용이나 스크립트 동작에 대해 더 궁금한 점이 있으시면 말씀해 주세요.

보너스 미션인 **통계 리포트 생성(`report.sh`)**과 **로그 보존 정책(`logretain.sh`)** 스크립트 구성을 도와드리겠습니다. 이 스크립트들은 VectorSophie님의 기술적 정교함과 미션의 요구사항을 결합하여, 수집된 데이터를 분석하고 서버의 저장 공간을 효율적으로 관리할 수 있도록 설계되었습니다.

---

### **1. 보너스 미션 1: `report.sh` (통계 리포트 생성)**

이 스크립트는 `monitor.log`에 기록된 데이터를 분석하여 CPU, 메모리, 디스크 사용량의 **평균, 최대, 최소값**과 데이터 샘플 수를 출력합니다.

#### **스크립트 소스코드 (`$AGENT_HOME/bin/report.sh`)**

```bash
#!/bin/bash

# 환경 변수 및 로그 경로 설정
AGENT_LOG_DIR="${AGENT_LOG_DIR:-/var/log/agent-app}"
LOG_FILE="$AGENT_LOG_DIR/monitor.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "[ERROR] 로그 파일을 찾을 수 없습니다: $LOG_FILE"
    exit 1
fi

echo "====== STATISTICS REPORT (Source: $LOG_FILE) ======"

# 통계 계산을 위한 awk 스크립트
# $4: CPU(%), $5: MEM(%), $6: DISK(%) 위치를 파싱하여 계산
awk -F'[:% ]+' '
{
    # 데이터 추출 (로그 포맷에 맞춰 인덱스 조정)
    # [2026-02-25 13:58:01] PID:48291 CPU:10.2% MEM:3.2% DISK_USED:23%
    cpu=$7; mem=$9; disk=$11;
    time=$1 " " $2;

    # CPU 통계
    cpu_sum += cpu;
    if (NR == 1 || cpu > cpu_max) { cpu_max = cpu; cpu_max_t = time; }
    if (NR == 1 || cpu < cpu_min) { cpu_min = cpu; cpu_min_t = time; }

    # 메모리 통계
    mem_sum += mem;
    if (NR == 1 || mem > mem_max) { mem_max = mem; mem_max_t = time; }
    if (NR == 1 || mem < mem_min) { mem_min = mem; mem_min_t = time; }

    count++;
}
END {
    printf "[CPU]     Average : %.1f%%\n", cpu_sum/count;
    printf "          Maximum : %.1f%% at %s\n", cpu_max, cpu_max_t;
    printf "          Minimum : %.1f%% at %s\n", cpu_min, cpu_min_t;
    printf "[Memory]  Average : %.1f%%\n", mem_sum/count;
    printf "          Maximum : %.1f%% at %s\n", mem_max, mem_max_t;
    printf "          Minimum : %.1f%% at %s\n", mem_min, mem_min_t;
    printf "[Samples] Data Points: %d samples\n", count;
}' "$LOG_FILE"
```

*   **핵심 로직**: `awk`를 사용하여 로그 파일의 각 행에서 수치를 추출하고, 전체 데이터의 합계와 최댓값/최솟값이 발생한 시점을 실시간으로 추적합니다.

---

### **2. 보너스 미션 2: `logretain.sh` (로그 보존 정책)**

로그가 무한정 쌓여 디스크가 가득 차는 것을 방지하기 위해 **시간 기반의 자동 관리 정책**을 수행합니다.

#### **보존 정책 내용**:
*   **7일 경과 로그**: 압축 후 아카이브 디렉토리로 이동.
*   **30일 경과 아카이브**: 시스템에서 영구 삭제.

#### **스크립트 소스코드 (`$AGENT_HOME/bin/logretain.sh`)**

```bash
#!/bin/bash

# 경로 설정
LOG_DIR="/var/log/agent-app"
ARCHIVE_DIR="/var/log/monitor/agent-app/archive"

# 아카이브 디렉토리 미존재 시 생성
mkdir -p "$ARCHIVE_DIR"

echo "[$(date)] Starting Log Retention Policy..."

# 1. 7일 경과 로그 압축 및 이동
# find 명령어로 7일 이상 된 .log 파일을 찾아 압축 후 이동
find "$LOG_DIR" -name "*.log.*" -mtime +7 -exec bash -c '
    for file do
        echo "Archiving: $file"
        tar -czf "${file}.tar.gz" "$file" --remove-files
        mv "${file}.tar.gz" "'"$ARCHIVE_DIR"'"
    done
' bash {} +

# 2. 30일 경과 아카이브 삭제
find "$ARCHIVE_DIR" -name "*.tar.gz" -mtime +30 -exec bash -c '
    for arch do
        echo "Deleting old archive: $arch"
        rm -f "$arch"
    done
' bash {} +

echo "[$(date)] Log Retention Policy Completed."
```

---

### **3. 실행 권한 및 자동화 설정**

두 스크립트 모두 보안 가이드에 따라 적절한 권한을 부여하고, 특히 `logretain.sh`는 매일 정해진 시간에 자동 실행되도록 설정하는 것이 권장됩니다.

```bash
# 권한 설정 (admin 실행 가능하도록)
chmod 750 $AGENT_HOME/bin/report.sh
chmod 750 $AGENT_HOME/bin/logretain.sh
chown agent-dev:agent-core $AGENT_HOME/bin/*.sh

# logretain.sh 자동화 등록 (매일 새벽 0시에 실행)
# agent-admin 계정의 crontab에 등록
0 0 * * * /home/agent-admin/agent-app/bin/logretain.sh >> /var/log/agent-app/retention.log 2>&1
```

이로써 **시스템 상태 수집(`monitor.sh`) → 데이터 분석(`report.sh`) → 용량 관리(`logretain.sh`)**로 이어지는 운영 라이프사이클 전체가 완성되었습니다. 이 스크립트들을 통해 더욱 전문적인 서버 운영 환경을 구축하실 수 있습니다. 추가로 필요한 설명이 있으신가요?