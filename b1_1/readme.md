# 1.  **요구사항 수행 내역서 (문서 1개)**

## 0. WSL2 기반 도커 인프라 구축 및 실행 가이드
본격적인 미션 수행에 앞서, 지금까지 WSL2 환경에 도커(Docker)를 설치하고 권한 문제를 해결하여 실행하기까지의 과정을 깔끔하게 정리해 드리겠습니다.

### 0.1. 도커 엔진 설치 (Docker Engine Only)
Docker Desktop을 사용하지 않고 WSL2 내부에서 직접 도커 엔진만 설치하는 방식을 선택했습니다 [1].
명령어: sudo apt update &amp;&amp; sudo apt install -y docker.io
이유: 리소스(CPU/메모리) 절약 및 실무적인 터미널 환경 구축을 위함입니다 [1, 2].

### 0.2. 권한 설정 및 세션 초기화
설치 직후 발생한 permission denied 오류를 해결하기 위해 사용자 계정에 권한을 부여하고 이를 시스템에 반영했습니다 [1].

* 그룹 추가: sudo usermod -aG docker $USER 명령어로 현재 사용자를 docker 그룹에 포함시켰습니다 [1].

* 환경 반영: wsl --shutdown(Windows PowerShell에서 실행)을 통해 WSL2 인스턴스를 완전히 종료했다가 다시 켜서 변경된 그룹 권한을 활성화했습니다 [1].

* 서비스 시작: sudo service docker start를 통해 도커 엔진을 구동시켰습니다 [1].

### 0.3. 미션용 컨테이너 실행 조건 (중요)
이제 미션을 위해 ubuntu:22.04 이미지를 실행할 때 반드시 포함해야 할 핵심 옵션들입니다 [2, 3].

* --privileged (특권 모드): 컨테이너 내부에서 SSH 설정 변경 및 방화벽(UFW) 활성화와 같은 핵심 커널 기능을 제어하기 위해 반드시 필요합니다 [4, 5].

* -p 20022:20022 (포트 포워딩): 컨테이너 내부에서 변경할 SSH 포트(20022)를 외부 호스트와 연결하여 접속 통로를 확보합니다 [6, 7].

* 최종 실행 명령어 예시:

```bash
docker run -it --privileged -p 20022:20022 --name mission-box ubuntu:22.04 /bin/bash  
```

### 0.4. Docker 설치 확인

```bash
user@4CAT1:~$ docker ps
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```

### 0.4. Docker 실행 : ubuntu:22.04

```bash
user@4CAT1:~$ docker run -it --privileged -p 20022:20022 --name mission-box ubuntu:22.04 /bin/bash
Unable to find image 'ubuntu:22.04' locally
22.04: Pulling from library/ubuntu
f63eb04151bc: Pull complete
bf0d6867143e: Download complete
Digest: sha256:962f6cadeae0ea6284001009daa4cc9a8c37e75d1f5191cf0eb83fe565b63dd7
Status: Downloaded newer image for ubuntu:22.04
```

### 0.6. 컨테이너 안에서 ssh 서비스 설치

```bash
root@41bc6dbe4c07:/# apt update && apt install -y openssh-server nano
```

## 1. sshd_config 변경하기
### 1.1. Port 20022, rootlogin권한 설정

```bash
root@41bc6dbe4c07:/# nano /etc/ssh/sshd_config
Port 20022
PermitRootLogin no
```

### 1.2. SSH 서비스 시작

```bash
root@41bc6dbe4c07:/# service ssh start
 * Starting OpenBSD Secure Shell server sshd
```

### 1.3. SSH 서비스 확인

```bash
root@41bc6dbe4c07:/# service ssh status
 * sshd is running
root@41bc6dbe4c07:/# apt install -y iproute2
root@41bc6dbe4c07:/# ss -tulnp | grep sshd
tcp   LISTEN 0      128          0.0.0.0:20022      0.0.0.0:*    users:(("sshd",pid=3972,fd=3))
tcp   LISTEN 0      128             [::]:20022         [::]:*    users:(("sshd",pid=3972,fd=4))
```

### 1.3.1  참조 : 변경된 설정을 적용하기 위해 재시작  

```bash
service ssh restart
```
## 2. 방화벽(UFW) 활성화 및 포트 허용
SSH라는 '문'을 바꿨으니, 이제 그 문을 지킬 '보안 요원'을 배치해야 합니다. 소스에 따르면 **TCP 20022(SSH)**와 TCP 15034(APP) 포트만 허용하는 것이 핵심입니다
.
### 2-1. 기본 정책 설정: 들어오는 모든 연결은 차단하고, 나가는 연결은 허용합니다.

* ufw default deny incoming
* ufw default allow outgoing

```bash
root@41bc6dbe4c07:/# apt update && apt install -y ufw
root@41bc6dbe4c07:/# ufw default deny incoming
Default incoming policy changed to 'deny'
(be sure to update your rules accordingly)

root@41bc6dbe4c07:/# ufw default allow outgoing
Default outgoing policy changed to 'allow'
(be sure to update your rules accordingly)
```

### 2-2. 필수 포트 허용: 미션에서 요구한 두 포트만 엽니다.

* ufw allow 20022/tcp
* ufw allow 15034/tcp
```bash


root@41bc6dbe4c07:/# ufw allow 15034/tcp
Rules updated
Rules updated (v6)

root@41bc6dbe4c07:/# ufw allow 20022/tcp
Rule added
Rule added (v6)
```

### 2-3. 방화벽 활성화: 설정 완료 후 방화벽을 켭니다 (질문에 y 입력).

ufw enable

```bash
root@41bc6dbe4c07:/# ufw enable
Firewall is active and enabled on system startup
```

### 2-4. 확인: ufw status verbose 명령어로 20022와 15034 포트가 ALLOW 상태인지 확인합니다.

```bash
root@41bc6dbe4c07:/# ufw status verbose
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

### 2-4-1. 현재 상태 분석 및 성공 확인**
출력된 `ufw status verbose` 결과는 미션 요구사항을 정확히 충족하고 있습니다.
*   **방화벽 활성화:** `Status: active`로 보안 요원이 정상 근무 중입니다.
*   **기본 정책 적용:** `Default: deny (incoming)`를 통해 허용되지 않은 모든 외부 접속을 차단하는 보안 원칙을 수립했습니다.
*   **필수 포트 허용:** 미션에서 명시한 **20022/tcp (SSH)**와 **15034/tcp (APP)** 포트가 `ALLOW IN` 상태로 정확히 열려 있습니다.

이 출력 화면은 나중에 제출하실 **'요구사항 수행 내역서'의 핵심 증거 자료**가 되므로 잘 기록해 두시기 바랍니다.

---

## 3. 디렉토리 및 권한(ACL) 체계 구축**
기본 보안과 네트워크 설정이 끝났으니, 이제 실제 데이터가 저장될 **디렉토리를 생성하고 그룹별로 접근 권한**을 정교하게 설정할 차례입니다.

다음 명령어들을 컨테이너 내부에서 순서대로 입력하여 체계를 구축해 보세요.



### 3.2. 그룹 및 계정 생성

```bash
root@dbdaf2e0de72:/# chgrp agent-common /home/agent-admin/agent-app/upload_files
chgrp: invalid group: 'agent-common'
```

`chgrp: invalid group: 'agent-common'` 에러가 발생하는 이유는 현재 시스템에 **`agent-common`이라는 그룹이 생성되어 있지 않기 때문**입니다.

미션의 요구사항에 따르면 디렉토리 권한 설정을 하기 전에 먼저 **계정과 그룹을 생성**하는 작업이 선행되어야 합니다. 아래 순서대로 명령어를 입력하여 그룹과 계정을 먼저 만든 후, 다시 디렉토리 권한 설정을 진행해 보세요.

### 3.2.1. 그룹 및 계정 생성 (먼저 수행)

루트(`root`) 권한에서 다음 명령어를 순서대로 입력하세요.

```bash
# 1. 그룹 생성
root@dbdaf2e0de72:/# groupadd agent-common
root@dbdaf2e0de72:/# groupadd agent-core

# 2. 사용자 계정 생성 (홈 디렉토리 생성 및 쉘 지정)
root@dbdaf2e0de72:/# useradd -m -s /bin/bash agent-admin
root@dbdaf2e0de72:/# useradd -m -s /bin/bash agent-dev
root@dbdaf2e0de72:/# useradd -m -s /bin/bash agent-test

# 3. 사용자를 그룹에 추가
# agent-common 그룹에는 모두 포함
root@dbdaf2e0de72:/# usermod -aG agent-common agent-admin
root@dbdaf2e0de72:/# usermod -aG agent-common agent-dev
root@dbdaf2e0de72:/# usermod -aG agent-common agent-test

# agent-core 그룹에는 admin과 dev만 포함
root@dbdaf2e0de72:/# usermod -aG agent-core agent-admin
root@dbdaf2e0de72:/# usermod -aG agent-core agent-dev

```
**# 3.1. 미션용 디렉토리 생성**
먼저 앱 실행에 필요한 핵심 디렉토리들을 만듭니다. (AGENT_HOME을 `/home/agent-admin/agent-app`으로 가정할 때의 예시입니다)
```bash
# 디렉토리 생성

mkdir -p /home/agent-admin/agent-app/upload_files
mkdir -p /home/agent-admin/agent-app/api_keys
mkdir -p /var/log/agent-app
```

### 3.2.2. 디렉토리 소유권 및 권한 설정 (다시 수행)

그룹이 정상적으로 생성되었다면, 이제 에러가 났던 명령어를 다시 실행할 수 있습니다.


### 3.2.3. 소유 그룹 변경
```bash

root@dbdaf2e0de72:/# chgrp agent-common /home/agent-admin/agent-app/{upload_files,api_keys}
root@dbdaf2e0de72:/# chgrp agent-core /var/log/agent-app

root@dbdaf2e0de72:/# ls -ld /home/agent-admin/agent-app/upload_files
drwxr-xr-x 1 root agent-common 0 May 11 10:54 /home/agent-admin/agent-app/upload_files
root@dbdaf2e0de72:/# ls -ld /home/agent-admin/agent-app/api_keys
drwxr-xr-x 1 root agent-core 0 May 11 10:54 /home/agent-admin/agent-app/api_keys
root@dbdaf2e0de72:/# ls -ld /var/log/agent-app
drwxr-xr-x 1 root agent-core 0 May 11 10:55 /var/log/agent-app
```

### 3.2.4. 권한 설정 (770: 소유자/그룹은 모든 권한, 나머지는 없음)

```bash
root@dbdaf2e0de72:/# chmod 770 /home/agent-admin/agent-app/upload_files
root@dbdaf2e0de72:/# chmod 770 /home/agent-admin/agent-app/api_keys
root@dbdaf2e0de72:/# chmod 770 /var/log/agent-app

root@dbdaf2e0de72:/# ls -ld /home/agent-admin/agent-app/upload_files
drwxrwx--- 1 root agent-common 0 May 11 10:54 /home/agent-admin/agent-app/upload_files
root@dbdaf2e0de72:/# ls -ld /home/agent-admin/agent-app/api_keys
drwxrwx--- 1 root agent-core 0 May 11 10:54 /home/agent-admin/agent-app/api_keys
root@dbdaf2e0de72:/# ls -ld /var/log/agent-app
drwxrwx--- 1 root agent-core 0 May 11 10:55 /var/log/agent-app

```

**성공 시 출력 예시:**
`drwxrwx--- 2 root agent-common ... upload_files` 처럼 그룹명이 정확히 표시되어야 합니다.

**Tip:** 만약 소유자도 `root`가 아닌 `agent-admin`으로 바꾸고 싶다면 `chown agent-admin:agent-common [경로]` 명령어를 사용하시면 됩니다. 미션지 가이드에 따라 소유 그룹을 먼저 맞추는 것이 핵심입니다!
