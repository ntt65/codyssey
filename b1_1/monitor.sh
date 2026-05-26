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

