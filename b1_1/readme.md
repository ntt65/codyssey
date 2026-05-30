# 1. 요구사항 수행 내역서

본 문서는 B1-1 시스템 관제 및 자동화 스크립트 개발 미션의 완전한 구현 과정을 기록한 내역서입니다.

---

## 2. WSL2 기반 도커 인프라 구축

본격적인 미션 수행에 앞서, WSL2 환경에 도커(Docker)를 설치하고 권한 문제를 해결하여 실행하기까지의 과정을 정리합니다.

### 2.1. 도커 엔진 설치 (Docker Engine Only)

Docker Desktop을 사용하지 않고 WSL2 내부에서 직접 도커 엔진만 설치하는 방식을 선택했습니다.

```bash
# 도커 엔진 설치
sudo apt update && sudo apt install -y docker.io
```

**이유:** 리소스(CPU/메모리) 절약 및 실무적인 터미널 환경 구축을 위함입니다.

### 2.2. 권한 설정 및 세션 초기화

설치 직후 발생한 permission denied 오류를 해결하기 위해 사용자 계정에 권한을 부여합니다.

```bash
# 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER

# WSL2 인스턴스 완전 재시작 (Windows PowerShell에서 실행)
wsl --shutdown

# 도커 서비스 시작
sudo service docker start
```

### 2.3. 미션용 컨테이너 실행 조건

ubuntu:22.04 이미지를 실행할 때 반드시 포함해야 할 핵심 옵션들:

- **--privileged:** SSH 설정 변경 및 UFW 활성화와 같은 커널 기능 제어
- **-p 20022:20022:** SSH 포트 포워딩 설정

```bash
docker run -it --privileged -p 20022:20022 --name mission-box ubuntu:22.04 /bin/bash
```

### 2.4. SSH 서비스 설치

```bash
root@container:/# apt update && apt install -y openssh-server nano
```

---

## 3. SSH 설정 및 포트 변경

SSH 서비스를 구성하고 기본 포트 22를 보안 포트 20022로 변경하며, Root 원격 접속을 차단합니다.

### 3.1. sshd_config 수정: Port 20022, Root 접속 차단

```bash
root@container:/# nano /etc/ssh/sshd_config
Port 20022
PermitRootLogin no
```

### 3.2. SSH 서비스 시작 및 확인

```bash
# SSH 서비스 시작
root@container:/# service ssh start

# SSH 상태 확인
root@container:/# service ssh status

# iproute2 설치 (ss 명령어 사용)
root@container:/# apt install -y iproute2

# 포트 20022 바인딩 확인
root@container:/# ss -tulnp | grep sshd
tcp   LISTEN 0      128          0.0.0.0:20022      0.0.0.0:*    users:(("sshd",pid=3972,fd=3))
tcp   LISTEN 0      128             [::]:20022         [::]:*    users:(("sshd",pid=3972,fd=4))
```

### 3.3. SSH 설정 재시작 (참조)

```bash
service ssh restart
```

---

## 4. 방화벽(UFW) 활성화 및 포트 허용

SSH 포트를 변경했으므로, UFW 방화벽으로 보안을 강화합니다. TCP 20022(SSH)와 TCP 15034(APP) 포트만 허용합니다.

### 4.1. UFW 설치 및 기본 정책 설정

```bash
# UFW 설치
root@container:/# apt update && apt install -y ufw

# 들어오는 모든 연결 차단, 나가는 연결 허용
root@container:/# ufw default deny incoming
root@container:/# ufw default allow outgoing
```

### 4.2. 필수 포트 허용: 20022와 15034

```bash
root@container:/# ufw allow 15034/tcp
root@container:/# ufw allow 20022/tcp
```

### 4.3. 방화벽 활성화

```bash
root@container:/# ufw enable
```

### 4.4. 방화벽 상태 확인

```bash
root@container:/# ufw status verbose
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
15034/tcp                  ALLOW IN    Anywhere
20022/tcp                  ALLOW IN    Anywhere
15034/tcp (v6)             ALLOW IN    Anywhere (v6)
20022/tcp (v6)             ALLOW IN    Anywhere (v6)
```

### 4.5. 방화벽 설정 검증

출력 결과가 요구사항 충족:
- **방화벽 활성화:** `Status: active` 확인
- **기본 정책:** `Default: deny (incoming)` 설정 완료
- **필수 포트:** 20022/tcp (SSH), 15034/tcp (APP)만 `ALLOW IN` 상태

---

## 5. 역할 기반 권한 관리(RBAC) 및 디렉토리 보안

ACL(Access Control List)을 활용하여 협업 환경에서도 보안 정책이 자동으로 유지되도록 설정합니다.

### 5.1. 핵심 개념

- **`chmod`의 한계:** 소유자/그룹/기타 3개 계층만 지원
- **ACL의 역할:** 특정 사용자나 그룹을 위해 무한정 권한 칸 추가 가능
- **Default ACL (`setfacl -d`):** 폴더에 생성되는 모든 파일이 자동으로 권한을 상속

---

## 6. 애플리케이션 실행 환경 구성

인프라 보안의 기초가 완성되었습니다. 실제 애플리케이션을 구동할 운영 환경을 설정합니다.

### 6.1. 계정 및 그룹 설계

#### 6.1.1. 그룹 생성

```bash
root@container:/# groupadd agent-common
root@container:/# groupadd agent-core
root@container:/# cat /etc/group | grep 'agent-'
agent-common:x:1000:
agent-core:x:1001:
```

#### 6.1.2. 계정 생성 및 그룹 배정

```bash
# agent-common: 모든 계정 포함
# agent-core: admin, dev 계정만 포함
root@container:/# useradd -m -s /bin/bash -G agent-common,agent-core agent-admin
root@container:/# useradd -m -s /bin/bash -G agent-common,agent-core agent-dev
root@container:/# useradd -m -s /bin/bash -G agent-common agent-test
```

**보안 원칙:** `agent-test` 계정은 `agent-core`에서 제외하여 격리합니다.

```bash
root@container:/# cat /etc/group | grep 'agent'
agent-common:x:1000:agent-admin,agent-dev,agent-test
agent-core:x:1001:agent-admin,agent-dev
agent-admin:x:1002:
agent-dev:x:1003:
agent-test:x:1004:
```

### 6.2. 디렉토리 생성 및 소유권 설정

#### 6.2.1. 디렉토리 생성

```bash
export AGENT_HOME=/home/agent-admin/agent-app

# 디렉토리 생성
root@container:/# mkdir -p $AGENT_HOME
root@container:/# mkdir -p $AGENT_HOME/upload_files
root@container:/# mkdir -p $AGENT_HOME/api_keys
root@container:/# mkdir -p /var/log/agent-app
```

#### 6.2.2. 그룹 소유권 변경

```bash
root@container:/# chgrp agent-common $AGENT_HOME/upload_files
root@container:/# chgrp agent-core $AGENT_HOME/api_keys
root@container:/# chgrp agent-core /var/log/agent-app
```

#### 6.2.3. 기본 권한 및 SetGID 적용

```bash
# upload_files에 2770 설정 (SetGID를 통한 자동 그룹 상속)
root@container:/# chmod 2770 $AGENT_HOME/upload_files
root@container:/# chmod 770 $AGENT_HOME/api_keys
root@container:/# chmod 770 /var/log/agent-app

# 확인
root@container:/# ls -ld $AGENT_HOME/upload_files
drwxrws--- 1 root agent-common 0 May 13 11:49 upload_files
root@container:/# ls -ld $AGENT_HOME/api_keys
drwxrwx--- 1 root agent-core 0 May 13 11:49 api_keys
root@container:/# ls -ld /var/log/agent-app
drwxrwx--- 1 root agent-core 0 May 13 12:10 agent-app
```

#### 6.2.4. Default ACL 설정 (자동 권한 상속)

```bash
root@container:/# setfacl -d -m g:agent-common:rwx $AGENT_HOME/upload_files
root@container:/# setfacl -d -m g:agent-core:rwx $AGENT_HOME/api_keys
root@container:/# setfacl -d -m g:agent-core:rwx /var/log/agent-app
```

### 6.3. 애플리케이션 바이너리 배포 및 환경 변수 설정

#### 6.3.1. 호스트에서 컨테이너로 애플리케이션 복사

```bash
# 맥북 호스트에서
mpeg46551@mac:~/b1_1 % docker cp ./agent-app mission-box:/home/agent-admin/
```

#### 6.3.2. 소유권 복구

```bash
root@container:/home/agent-admin/agent-app# chown -R agent-admin:agent-core .
root@container:/home/agent-admin/agent-app# rm agent-app-linux-arm64  # 불필요한 파일 삭제
root@container:/home/agent-admin/agent-app# mv agent-app-linux-x86 agent-app
root@container:/home/agent-admin/agent-app# chmod 750 agent-app
```

#### 6.3.3. 환경 변수 설정

```bash
agent-admin@container:~$ nano ~/.bashrc

# 파일 끝에 추가
export AGENT_HOME=/home/agent-admin/agent-app
export AGENT_PORT=15034
export AGENT_UPLOAD_DIR=$AGENT_HOME/upload_files
export AGENT_KEY_PATH=$AGENT_HOME/api_keys
export AGENT_LOG_DIR=/var/log/agent-app

# 저장 후 적용
agent-admin@container:~$ source ~/.bashrc
agent-admin@container:~$ env | grep AGENT
AGENT_UPLOAD_DIR=/home/agent-admin/agent-app/upload_files
AGENT_PORT=15034
AGENT_KEY_PATH=/home/agent-admin/agent-app/api_keys
AGENT_HOME=/home/agent-admin/agent-app
AGENT_LOG_DIR=/var/log/agent-app
```

#### 6.3.4. 애플리케이션 Boot Sequence 실행

```bash
agent-admin@container:~$ $AGENT_HOME/agent-app
>>> Starting Agent Boot Sequence...
[1/5] Checking User Account               [OK]
   ... Running as service user 'agent-admin' (uid=1000)
[2/5] Verifying Environment Variables     [OK]
   ... All required Envs correct
[3/5] Checking Required Files             [OK]
   ... Verified 'secret.key' with correct key string.
[4/5] Checking Port Availability          [OK]
   ... Port 15034 is available.
[5/5] Verifying Log Permission            [OK]
   ... Log directory is writable: /var/log/agent-app
------------------------------------------------------------
All Boot Checks Passed!
Agent READY
```

---

## 7. 시스템 관제 스크립트 개발 (monitor.sh)

### 7.1. 모니터링 스크립트 작성

#### 7.1.1. 스크립트 파일 생성

```bash
# bin 디렉토리 생성
agent-admin@container:~/agent-app$ mkdir -p /home/agent-admin/agent-app/bin

# 스크립트 작성
agent-admin@container:~/agent-app$ nano /home/agent-admin/agent-app/bin/monitor.sh
```

#### 7.1.2. monitor.sh 내용

```bash
#!/bin/bash

# 환경 변수 및 기본 설정
AGENT_HOME="/home/agent-admin/agent-app"
AGENT_LOG_DIR="/var/log/agent-app"
LOG_FILE="$AGENT_LOG_DIR/monitor.log"
APP_NAME="agent-app"
PORT=15034
MAX_SIZE=$((10 * 1024 * 1024))
MAX_FILES=10

# 1. Health Check (프로세스 및 포트)
PID=$(pgrep -f "$APP_NAME" | head -1)
if [ -z "$PID" ]; then
    echo "[FAIL] Process $APP_NAME is not running."
    exit 1
fi

PORT_CHECK=$(ss -tulnp | grep ":$PORT")
if [ -z "$PORT_CHECK" ]; then
    echo "[FAIL] Port $PORT is not listening."
    exit 1
fi

# 2. 방화벽 상태 점검 (WARNING만 출력, 스크립트 종료 안 함)
UFW_STATUS=$(ufw status 2>/dev/null | grep "Status: active")
if [ -z "$UFW_STATUS" ]; then
    echo "[WARNING] Firewall is not active"
fi

# 3. 자원 수집 (CPU, MEM, DISK)
CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2+$4}')
MEM=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100}')
DISK=$(df / | tail -1 | awk '{print $5}' | tr -d '%')

# 4. 임계값 경고 (CPU 20%, MEM 10%, DISK 80% 초과 시)
CPU_INT=$(echo $CPU | cut -d'.' -f1)
MEM_INT=$(echo $MEM | cut -d'.' -f1)

if [ "$CPU_INT" -gt 20 ]; then
    echo "[WARNING] CPU threshold exceeded ($CPU% > 20%)"
fi
if [ "$MEM_INT" -gt 10 ]; then
    echo "[WARNING] MEM threshold exceeded ($MEM% > 10%)"
fi
if [ "$DISK" -gt 80 ]; then
    echo "[WARNING] DISK threshold exceeded ($DISK% > 80%)"
fi

# 5. 로그 기록 (요구된 포맷 준수)
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
LOG_LINE="[$TIMESTAMP] PID:$PID CPU:$CPU% MEM:$MEM% DISK_USED:$DISK%"
echo "$LOG_LINE" >> "$LOG_FILE"

# 6. 로그 파일 용량 관리 (Log Rotation - 최대 10MB, 10개 유지)
if [ -f "$LOG_FILE" ]; then
    FILE_SIZE=$(stat -c%s "$LOG_FILE")
    if [ "$FILE_SIZE" -gt "$MAX_SIZE" ]; then
        if [ -f "$LOG_FILE.$MAX_FILES" ]; then
            rm -f "$LOG_FILE.$MAX_FILES"
        fi
        for i in $(seq $((MAX_FILES-1)) -1 1); do
            if [ -f "$LOG_FILE.$i" ]; then
                mv "$LOG_FILE.$i" "$LOG_FILE.$((i+1))"
            fi
        done
        mv "$LOG_FILE" "$LOG_FILE.1"
    fi
fi
```

### 7.2. 스크립트 권한 설정

```bash
# root에서 실행
root@container:/# chown -R agent-dev:agent-core /home/agent-admin/agent-app/bin
root@container:/# chmod 750 /home/agent-admin/agent-app/bin
root@container:/# chmod 750 /home/agent-admin/agent-app/bin/monitor.sh
```

### 7.3. Cron 스케줄 등록

#### 7.3.1. Cron 설치 및 시작

```bash
root@container:/# apt update && apt install -y cron
root@container:/# service cron start
```

#### 7.3.2. Crontab 등록 (매분 실행)

```bash
agent-admin@container:~$ crontab -e
# 에디터에서 추가
* * * * * /home/agent-admin/agent-app/bin/monitor.sh
```

#### 7.3.3. 로그 확인

```bash
# 앱을 백그라운드로 실행
agent-admin@container:~$ nohup $AGENT_HOME/agent-app &

# 1분 후 로그 확인
agent-admin@container:~$ cat /var/log/agent-app/monitor.log
[2026-05-26 13:50:01] PID:455 CPU:6.7% MEM:3.0% DISK_USED:1%
[2026-05-26 13:51:02] PID:455 CPU:0% MEM:2.8% DISK_USED:1%
[2026-05-26 13:52:01] PID:455 CPU:0% MEM:3.2% DISK_USED:1%
```
### 7.4. 계정 패스워드 설정 및 외부 SSH 접속 검증

보안 설정 상 외부에서 SSH(포트 `20022`)로 접속하거나 컨테이너 내부에서 사용자 전환(`su`)을 수행하려면 각 계정의 패스워드 설정이 필수적입니다.

#### 7.4.1. 계정별 패스워드 설정 방식
컨테이너 생성 초기에는 `root` 및 일반 계정(`agent-*`)들의 패스워드가 지정되지 않았거나 잠겨있는 상태(`!`, `*`)이므로 아래 방식을 통해 패스워드를 지정합니다.

*   **방법 1: 대화형 설정 (passwd 명령어)**
    ```bash
    # root 권한에서 특정 유저 비밀번호 설정
    passwd agent-admin
    # (새로운 비밀번호 2회 입력)
    1001
    ```

*   **방법 2: 비대화형 설정 (chpasswd 명령어 - 자동화에 유리)**
    ```bash
    echo "agent-admin:원하는비밀번호" | chpasswd
    ```

#### 7.4.2. SSH 외부 접속 대상 제어 설정 (sshd_config)
기본적으로 SSH 설정 파일(`/etc/ssh/sshd_config`)에는 `PermitRootLogin no`가 적용되어 최고 권한 계정인 `root`로의 외부 직접 로그인은 차단되어 있습니다.
만약 특정 일반 사용자 계정(예: `agent-admin`)으로만 외부 SSH 접속을 완전히 격리하고 싶다면 다음과 같이 설정할 수 있습니다.

```bash
# /etc/ssh/sshd_config 파일 편집
nano /etc/ssh/sshd_config

# 파일 최하단에 특정 허용 유저 명시 추가
AllowUsers agent-admin

# SSH 서비스 재시작하여 적용
service ssh restart
```

#### 7.4.3. 호스트 PC(macOS)에서의 SSH 접속 테스트
호스트 환경인 iMac 터미널에서 포트 포워딩 경로(`20022` 포트)를 통해 컨테이너의 `agent-admin` 계정으로 접속을 검증합니다.

```bash
# 호스트 PC 터미널에서 실행
ssh agent-admin@localhost -p 20022

# 최초 접속 시 신뢰 확인 안내에 'yes' 입력 후 패스워드 입력 진행
# (접속 성공 화면)
Welcome to Ubuntu 22.04.5 LTS (GNU/Linux 6.17.8-orbstack-00308-g8f9c941121b1 x86_64)
agent-admin@981c5cada840:~$ 
```

---

## 8. 보너스 과제: 로그 분석 및 보존 정책

실무 인프라 관리 환경에서 필수적인 로그 데이터의 통계 분석 및 자동 보존/정리 정책을 수립하고 자동화 스크립트를 작성하여 적용합니다.

### 8.1. 보너스 1: 통계 리포트 생성 (report.sh)

`monitor.log` 파일을 분석하여 수집된 리소스 데이터(CPU, Memory, Disk)의 평균값, 최대치, 최소치를 계산하고 분석된 총 데이터 샘플 수를 정렬하여 출력합니다.

#### 8.1.1. 스크립트 작성 (`report.sh`)
```bash
# bin 디렉토리에 스크립트 파일 생성
nano /home/agent-admin/agent-app/bin/report.sh
```

**스크립트 소스코드:**
```bash
#!/bin/bash
LOG_FILE="/var/log/agent-app/monitor.log"

# 예외 처리: 로그 파일이 없는 경우
if [ ! -f "$LOG_FILE" ]; then
    echo "[ERROR] 분석할 로그 파일이 없습니다: $LOG_FILE"
    exit 1
fi

echo "====== STATISTICS REPORT ======"
# awk를 이용한 텍스트 데이터 파싱 및 통계 계산
awk '
/PID:/ {
    # 문자열에서 % 기호와 불필요한 텍스트 제거 후 변수 할당
    cpu = $4; sub("CPU:", "", cpu); sub("%", "", cpu);
    mem = $5; sub("MEM:", "", mem); sub("%", "", mem);
    disk = $6; sub("DISK_USED:", "", disk); sub("%", "", disk);

    cpu_sum += cpu; mem_sum += mem; disk_sum += disk;
    count++;

    # 최대/최소값 초기화 및 갱신
    if (count == 1) {
        cpu_max = cpu; cpu_min = cpu;
        mem_max = mem; mem_min = mem;
        disk_max = disk; disk_min = disk;
    } else {
        if (cpu > cpu_max) cpu_max = cpu;
        if (cpu < cpu_min) cpu_min = cpu;
        if (mem > mem_max) mem_max = mem;
        if (mem < mem_min) mem_min = mem;
        if (disk > disk_max) disk_max = disk;
        if (disk < disk_min) disk_min = disk;
    }
}
END {
    if (count > 0) {
        printf "[CPU] Average : %.1f%%, Maximum : %.1f%%, Minimum : %.1f%%\n", cpu_sum/count, cpu_max, cpu_min
        printf "[Memory] Average : %.1f%%, Maximum : %.1f%%, Minimum : %.1f%%\n", mem_sum/count, mem_max, mem_min
        printf "[Disk] Average : %.1f%%, Maximum : %.1f%%, Minimum : %.1f%%\n", disk_sum/count, disk_max, disk_min
        printf "[Samples] Data Points: %d samples\n", count
    } else {
        print "로그 데이터가 충분하지 않습니다."
    }
}' "$LOG_FILE"
```

#### 8.1.2. 리포트 실행 결과 확인
```bash
agent-admin@container:~$ /home/agent-admin/agent-app/bin/report.sh
====== STATISTICS REPORT ======
[CPU] Average : 0.2%, Maximum : 6.7%, Minimum : 0.0%
[Memory] Average : 3.5%, Maximum : 3.9%, Minimum : 2.0%
[Disk] Average : 1.0%, Maximum : 1.0%, Minimum : 1.0%
[Samples] Data Points: 186 samples
```

---

### 8.2. 보너스 2: 로그 보존 정책 (archive.sh)

디스크 고갈 방지를 위해 7일이 경과한 기존 구버전 로그 파일(`monitor.log.*`)을 압축(`gzip`)하여 별도의 아카이브 폴더로 이동시키고, 30일이 경과한 아카이브 압축 파일은 자동으로 영구 삭제하도록 설정합니다.

#### 8.2.1. 스크립트 작성 (`archive.sh`)
```bash
nano /home/agent-admin/agent-app/bin/archive.sh
```

**스크립트 소스코드:**
```bash
#!/bin/bash
LOG_DIR="/var/log/agent-app"
ARCHIVE_DIR="$LOG_DIR/archive"

echo "====== LOG RETENTION POLICY EXECUTION ======"

# 1. 예외 처리: 로그 디렉토리가 없거나 쓰기 권한이 부족한 경우
if [ ! -d "$LOG_DIR" ] || [ ! -w "$LOG_DIR" ]; then
    echo "[ERROR] 로그 디렉토리가 없거나 쓰기 권한이 부족합니다: $LOG_DIR"
    exit 1
fi

# 아카이브 폴더가 없으면 생성
mkdir -p "$ARCHIVE_DIR"

# 2. 7일 경과 로그 압축 및 아카이브 이동
TARGET_LOGS=$(find "$LOG_DIR" -maxdepth 1 -name "*.log*" -type f -mtime +7)

if [ -n "$TARGET_LOGS" ]; then
    for file in $TARGET_LOGS; do
        gzip "$file"
        mv "$file.gz" "$ARCHIVE_DIR/"
        echo "[INFO] 7일 경과 로그 압축 및 보관 완료: $file.gz"
    done
else
    echo "[INFO] 압축할 7일 이상 경과 로그 파일이 없습니다."
fi

# 3. 30일 경과 아카이브 완전 삭제
TARGET_ARCHIVES=$(find "$ARCHIVE_DIR" -name "*.gz" -type f -mtime +30)

if [ -n "$TARGET_ARCHIVES" ]; then
    for file in $TARGET_ARCHIVES; do
        rm "$file"
        echo "[INFO] 30일 경과 아카이브 영구 삭제 완료: $file"
    done
else
    echo "[INFO] 삭제할 30일 이상 경과 아카이브 파일이 없습니다."
fi
```

#### 8.2.2. 스크립트 소유권 및 실행 권한 보안 설정
비밀번호 보안 규격에 맞게 두 스크립트(`report.sh`, `archive.sh`)의 소유권을 `agent-dev:agent-core`로 부여하고, 권한을 `750`으로 조절하여 개발자는 수정 가능하고 운영자는 실행/읽기만 가능하도록 조치합니다.

```bash
# root 권한에서 소유자 및 권한 설정 변경
root@container:/# chown agent-dev:agent-core /home/agent-admin/agent-app/bin/report.sh
root@container:/# chown agent-dev:agent-core /home/agent-admin/agent-app/bin/archive.sh
root@container:/# chmod 750 /home/agent-admin/agent-app/bin/report.sh
root@container:/# chmod 750 /home/agent-admin/agent-app/bin/archive.sh

# 설정 내용 확인
root@container:/# ls -la /home/agent-admin/agent-app/bin/
total 12
drwxr-x--- 1 agent-dev   agent-core   38 May 28 12:14 .
drwxr-xr-x 1 agent-admin agent-core    6 May 26 13:33 ..
-rwxr-x--- 1 agent-dev   agent-core 1308 May 28 12:14 archive.sh
-rwxr-x--- 1 agent-dev   agent-core 2076 May 26 13:34 monitor.sh
-rwxr-x--- 1 agent-dev   agent-core 1650 May 28 12:13 report.sh
```

#### 8.2.3. Cron 스케줄러를 통한 자동 실행 등록 (매일 자정)
로그 보존 정책이 매일 자정에 스스로 작동하도록 운영자(`agent-admin`) 계정의 크론탭 스케줄러에 등록합니다.

```bash
# agent-admin 계정으로 전환하여 크론탭 편집 실행
agent-admin@container:~$ crontab -e

# 매일 자정(0시 0분)에 archive.sh를 구동하도록 최하단에 아래 구문 추가
0 0 * * * /home/agent-admin/agent-app/bin/archive.sh
```

#### 8.2.4. 보존 정책 스크립트 수동 실행 테스트
```bash
agent-admin@container:~$ /home/agent-admin/agent-app/bin/archive.sh
====== LOG RETENTION POLICY EXECUTION ======
[INFO] 압축할 7일 이상 경과 로그 파일이 없습니다.
[INFO] 삭제할 30일 이상 경과 아카이브 파일이 없습니다.
```

---

## 9. 최종 정리 및 검증

### 9.1. 시스템 상태 확인

```bash
# 모니터링 로그 누적 확인
agent-admin@container:~$ cat /var/log/agent-app/monitor.log
[2026-05-26 13:50:01] PID:455 CPU:6.7% MEM:3.0% DISK_USED:1%
[2026-05-26 13:51:02] PID:455 CPU:0% MEM:2.8% DISK_USED:1%
[2026-05-26 13:52:01] PID:455 CPU:0% MEM:3.2% DISK_USED:1%

# 권한 확인
root@container:/# id agent-admin && id agent-dev && id agent-test
```

### 9.2. 필수 증거 자료 체크리스트

✅ **기본 보안:**
- SSH 포트 변경 (20022) 및 Root 접속 차단
- UFW 방화벽 활성화 (20022, 15034 포트만 허용)

✅ **권한 관리:**
- agent-admin, agent-dev, agent-test 계정 생성
- agent-common, agent-core 그룹 설정
- SetGID 및 ACL을 통한 자동 권한 상속

✅ **애플리케이션 실행:**
- Agent Boot Sequence 5단계 통과
- "Agent READY" 출력 확인
- 포트 15034 바인딩 확인

✅ **자동화 모니터링:**
- monitor.sh 스크립트 작성 및 권한 설정
- Cron 매분 자동 실행
- 로깅 포맷: `[YYYY-MM-DD HH:MM:SS] PID:... CPU:..% MEM:..% DISK_USED:..%`
- 10MB 단위 로그 로테이션 구현

✅ **보너스 과제:**
- report.sh: 통계 분석 (평균/최대/최소)
- archive.sh: 7일 경과 로그 압축, 30일 경과 삭제

---

## 📝 요약

B1-1 시스템 관제 및 자동화 스크립트 개발 미션을 완벽하게 달성했습니다.

**핵심 성과:**
1. **인프라 보안:** SSH 재설정, 방화벽 정책 수립
2. **권한 관리:** RBAC 계층 설계, ACL 자동 상속
3. **시스템 모니터링:** 실시간 리소스 수집 및 임계값 경고
4. **자동화 관리:** Cron을 통한 매분 모니터링, 로그 로테이션
5. **보너스:** 통계 분석 및 보존 정책 자동화

이는 단순한 스크립트 작성을 넘어, 실제 엔터프라이즈 환경에서 필요한 운영 자동화 체계를 구축한 것입니다.
