#!/bin/bash

# =========================================================================
# 1. 환경 변수 및 모니터링 기본 설정
# =========================================================================
AGENT_HOME="/home/agent-admin/agent-app"     # 애플리케이션 홈 디렉토리 경로
AGENT_LOG_DIR="/var/log/agent-app"           # 로그 파일이 저장될 시스템 로그 디렉토리
LOG_FILE="$AGENT_LOG_DIR/monitor.log"        # 리소스 정보가 누적될 모니터링 로그 파일 경로
APP_NAME="agent-app"                         # 모니터링 대상인 서비스 프로세스 이름
PORT=15034                                   # 모니터링 대상 서비스가 사용하는 포트 번호
MAX_SIZE=$((10 * 1024 * 1024))               # 로그 파일 용량 임계치 (10MB를 바이트 단위로 환산)
MAX_FILES=10                                 # 보관할 백업 로그 파일의 최대 개수 (monitor.log.1 ~ .10)

# =========================================================================
# 2. Health Check (프로세스 기동 여부 및 포트 바인딩 확인)
# =========================================================================
# pgrep: 프로세스 이름 패턴(-f)으로 검색하여 해당 프로세스의 PID를 조회. head -1로 최상위 프로세스 ID 1개만 추출
PID=$(pgrep -f "$APP_NAME" | head -1)

# PID가 비어있으면 프로세스가 비정상 종료된 것으로 간주하고 즉시 에러(exit 1) 종료
if [ -z "$PID" ]; then
    echo "[FAIL] Process $APP_NAME is not running."
    exit 1
fi

# ss -tulnp: 현재 시스템에서 LISTEN 상태인 TCP(-t) 및 UDP(-u) 소켓 포트 정보를 프로세스 정보(-p)와 함께 출력
# 수집한 정보 중 대상 포트(:15034)가 정상 바인딩되어 동작 중인지 필터링
PORT_CHECK=$(ss -tulnp | grep ":$PORT")

# 지정한 포트에서 프로세스가 대기(LISTEN)하고 있지 않다면 즉시 스크립트를 에러(exit 1) 종료
if [ -z "$PORT_CHECK" ]; then
    echo "[FAIL] Port $PORT is not listening."
    exit 1
fi

# =========================================================================
# 3. 방화벽 상태 점검 (UFW 비활성화 시 경고 메시지만 출력하며 모니터링 진행)
# =========================================================================
# ufw status의 결과를 조회하여 방화벽이 활성화(Status: active)되어 있는지 확인
# 에러 스트림(2>)은 무시(/dev/null)하여 UFW 권한 에러 등이 터미널에 노출되지 않도록 제어
UFW_STATUS=$(ufw status 2>/dev/null | grep "Status: active")

# UFW 방화벽이 켜져있지 않은 경우 경고(WARNING) 메시지 출력 (스크립트는 계속 실행됨)
if [ -z "$UFW_STATUS" ]; then
    echo "[WARNING] Firewall is not active"
fi

# =========================================================================
# 4. 시스템 리소스 사용량 수집
# =========================================================================
# CPU: top 명령어를 일회성 배치 모드(-b -n1)로 구동한 후 CPU 사용율 정보 파싱
# user cpu($2)와 system cpu($4) 값을 더하여 총 CPU 사용량을 백분율로 계산
CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2+$4}')

# Memory: free 명령어 결과를 파싱하여 전체 메모리($2) 대비 사용 중인 메모리($3)의 비율을 계산
MEM=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100}')

# Disk: df 명령어의 결과 중 루트(/) 파티션의 5번째 컬럼(사용률 %)을 추출한 뒤, tr -d '%'로 % 기호를 제거하여 정수화
DISK=$(df / | tail -1 | awk '{print $5}' | tr -d '%')

# =========================================================================
# 5. 리소스 임계값 점검 및 모니터링 경고 출력
# =========================================================================
# 소수점이 포함된 CPU 및 Memory 값을 비교 연산하기 위해 cut 명령어로 소수점 앞 정수부만 잘라냄
CPU_INT=$(echo $CPU | cut -d'.' -f1)
MEM_INT=$(echo $MEM | cut -d'.' -f1)

# CPU 사용량이 20%를 초과할 경우 경고 출력
if [ "$CPU_INT" -gt 20 ]; then
    echo "[WARNING] CPU threshold exceeded ($CPU% > 20%)"
fi

# 메모리 사용량이 10%를 초과할 경우 경고 출력
if [ "$MEM_INT" -gt 10 ]; then
    echo "[WARNING] MEM threshold exceeded ($MEM% > 10%)"
fi

# 디스크 사용량이 80%를 초과할 경우 경고 출력
if [ "$DISK" -gt 80 ]; then
    echo "[WARNING] DISK threshold exceeded ($DISK% > 80%)"
fi

# =========================================================================
# 6. 모니터링 데이터 파일 로깅 (지정된 규격 포맷 준수)
# =========================================================================
# YYYY-MM-DD HH:MM:SS 형식의 타임스탬프 생성
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 로그 라인 구성: [시간] PID, CPU, MEM, DISK 상태 수집 내용 기록
LOG_LINE="[$TIMESTAMP] PID:$PID CPU:$CPU% MEM:$MEM% DISK_USED:$DISK%"

# 지정된 로그 파일의 맨 끝에 로그 라인 추가 기록 (누적 로깅)
echo "$LOG_LINE" >> "$LOG_FILE"

# =========================================================================
# 7. 로그 로테이션 (용량 제한 및 백업 보존)
# =========================================================================
# 현재 누적 중인 로그 파일이 실제로 존재할 경우 진행
if [ -f "$LOG_FILE" ]; then
    # stat -c%s: 로그 파일의 크기를 바이트 단위로 측정하여 파일 용량 조회
    FILE_SIZE=$(stat -c%s "$LOG_FILE")
    
    # 로그 파일 크기가 지정된 임계치(10MB)를 초과할 경우 백업 로테이션 실행
    if [ "$FILE_SIZE" -gt "$MAX_SIZE" ]; then
        # 가장 오래된 백업 로그 파일(monitor.log.10)이 존재한다면 삭제
        if [ -f "$LOG_FILE.$MAX_FILES" ]; then
            rm -f "$LOG_FILE.$MAX_FILES"
        fi
        
        # 파일명을 뒤에서부터 하나씩 뒤로 미룸 (예: 9번을 10번으로, 8번을 9번으로 ...)
        # seq 9 -1 1 명령어는 9부터 1까지 역순으로 숫자 생성
        for i in $(seq $((MAX_FILES-1)) -1 1); do
            if [ -f "$LOG_FILE.$i" ]; then
                mv "$LOG_FILE.$i" "$LOG_FILE.$((i+1))"
            fi
        done
        
        # 현재 활성 로그 파일(monitor.log)을 백업 1번(monitor.log.1)으로 파일명 변경
        mv "$LOG_FILE" "$LOG_FILE.1"
    fi
fi
