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

## 3. 역할 기반 권한 관리(RBAC) 및 디렉토리 보안 설정
ACL(Access Control List)이란 **`chmod`만으로는 해결할 수 없는 현실적인 협업 문제**를 해결하기 위해 도입된 아주 강력한 도구입니다.

### **1. `chmod`의 한계: 딱 3칸뿐인 권한 슬롯**
리눅스의 전통적인 권한(`chmod`)은 **소유자(Owner) / 그룹(Group) / 기타(Others)**라는 딱 3개의 계층으로만 구성됩니다.
*   **문제 발생:** 만약 특정 디렉토리에 대해 "A 그룹도 읽고 써야 하고, B 그룹도 읽어야 하는데, 나머지는 절대 못 보게 하고 싶다"라고 한다면 `chmod`로는 불가능합니다. 그룹은 하나만 지정할 수 있기 때문입니다.
*   **ACL의 해결:** ACL은 기존 3개 계층 외에 **"특정 사용자나 특정 그룹"을 위한 권한 칸을 무한정 추가**할 수 있게 해줍니다.

### **2. 이번 미션의 핵심: "미래를 위한 자동화" (`setfacl -d`)**
사용자님을 가장 헷갈리게 했던 `-d` (Default ACL) 옵션이야말로 ACL을 쓰는 진정한 이유입니다.
*   **협업의 난제:** `chmod`만 쓰면 `agent-admin`이 만든 파일은 기본적으로 다른 사람은 못 고치는 상태로 생성됩니다. 그럼 운영자가 매번 쫓아가서 `chmod`를 다시 해줘야 합니다.
*   **ACL의 마법:** `setfacl -d`를 설정해 두면, "이 폴더에 앞으로 생길 모든 파일은 **누가 만들든 상관없이** 특정 그룹에게 권한을 줘라"라는 **설계 도면**을 미리 박아두는 것입니다. 덕분에 운영자가 일일이 신경 쓰지 않아도 협업 환경이 안전하게 유지됩니다.

### **3. 복잡함을 줄이는 마인드셋**
실무에서도 모든 폴더에 ACL을 도배하지는 않습니다. 다음의 흐름으로 생각하면 마음이 편해집니다.
1.  **기본은 `chmod/chown`:** 소유자와 기본 그룹을 정해 큰 틀을 잡습니다.
2.  **예외와 자동화는 `ACL`:** 여러 그룹이 섞이거나(협업), 파일 생성 시 권한을 자동 상속시키고 싶을 때만 ACL이라는 '정교한 칼'을 꺼내 드는 것입니다.

이번 미션에서 **`upload_files`**에 ACL을 적용한 것은 단순히 명령어를 외우는 연습이 아니라, **"운영자가 개입하지 않아도 시스템이 스스로 보안 정책을 유지하게 만드는 법"**을 배우신 것입니다.

이제 인프라 보안과 권한 설정의 가장 어려운 고비를 넘기셨습니다! 이 정교한 권한 체계 위에서 실제 앱을 구동해보는 **[Step 4] 애플리케이션 실행 환경 구성** 단계로 넘어가 보시겠어요?
기본 보안과 네트워크 설정후, 이제 실제 데이터가 저장될 **디렉토리를 생성하고 그룹별로 접근 권한**을 정교하게 설정

1. 생성해야 할 계정 및 그룹 목록
미션 요구사항에 따라 총 3개의 계정과 2개의 그룹을 생성해야 합니다
.
2. 계정:
    * agent-admin: 운영 및 관리 담당, 크론탭(cron) 실행 주체
    * agent-dev: 개발 및 운영 담당, 모니터링 스크립트(monitor.sh) 작성자
    * agent-test: QA 및 테스트 담당

3. 그룹:
    * agent-common: 모든 계정(admin, dev, test)이 포함되는 공용 그룹
    * agent-core: 운영과 개발 핵심 인력(admin, dev)만 포함되는 보안 그룹

#### 3.1. 그룹 및 계정 생성 (기반 구축)**
그룹이 존재하지 않으면 권한 부여 시 에러가 발생하므로, 반드시 **그룹을 먼저 만들고 계정을 생성**해야 합니다.

```bash
#### **3.1.1. 그룹 생성
root@981ebdb4319e:/# groupadd agent-common
root@981ebdb4319e:/# groupadd agent-core
root@981ebdb4319e:/# cat /etc/group | grep 'agent-'
agent-common:x:1000:
agent-core:x:1001:

#### 3.1.2. 계정 생성 및 그룹 배정 (한 번에 처리)
# agent-common은 모두 포함, agent-core는 admin/dev만 포함
root@981ebdb4319e:/# useradd -m -s /bin/bash -G agent-common,agent-core agent-admin
root@981ebdb4319e:/# useradd -m -s /bin/bash -G agent-common,agent-core agent-dev
root@981ebdb4319e:/# useradd -m -s /bin/bash -G agent-common agent-test
```
*   **보안 원칙:** `agent-test` 계정은 핵심 보안 그룹인 `agent-core`에서 제외하여 철저히 격리합니다.

```bash
root@981ebdb4319e:/# cat /etc/group | grep 'agent'
agent-common:x:1000:agent-admin,agent-dev,agent-test
agent-core:x:1001:agent-admin,agent-dev
agent-admin:x:1002:
agent-dev:x:1003:
agent-test:x:1004:

root@981ebdb4319e:/# cat /etc/passwd | grep 'agent'
agent-admin:x:1000:1002::/home/agent-admin:/bin/bash
agent-dev:x:1001:1003::/home/agent-dev:/bin/bash
agent-test:x:1002:1004::/home/agent-test:/bin/bash
```

#### 3.2. 미션용 디렉토리 생성**
애플리케이션 홈 디렉토리(`AGENT_HOME`)를 기준으로 필요한 upload_files, api_keys, agent-app, 자식 폴더를 만듭니다.

```bash
# 변수 설정 (작업 편의성)
export AGENT_HOME=/home/agent-admin/agent-app

# 디렉토리 생성
root@981ebdb4319e:/# mkdir -p $AGENT_HOME
root@981ebdb4319e:/# mkdir -p $AGENT_HOME/upload_files
root@981ebdb4319e:/# mkdir -p $AGENT_HOME/api_keys
root@981ebdb4319e:/# mkdir -p /var/log/agent-app

# 권한 확인
root@981ebdb4319e:/# ls -ld $AGENT_HOME/upload_files
drwxr-xr-x 1 root root 0 May 13 11:49 /home/agent-admin/agent-app/upload_files
root@981ebdb4319e:/# ls -ld $AGENT_HOME/api_keys
drwxr-xr-x 1 root root 0 May 13 11:49 /home/agent-admin/agent-app/api_keys
root@981ebdb4319e:/# ls -ld /var/log/agent-app
drwxr-xr-x 1 root root 0 May 13 12:10 /var/log/agent-app
```

#### 3.3. 소유권 및 심화 권한 설정 (RBAC + ACL)**
단순한 `chmod`를 넘어, 협업 시 권한이 꼬이지 않도록 **SetGID**와 **ACL**을 적용하는 것이 핵심입니다.

#### 3.3.1. 그룹 소유권 변경
```bash
root@981ebdb4319e:/# chgrp agent-common $AGENT_HOME/upload_files
root@981ebdb4319e:/# chgrp agent-core $AGENT_HOME/api_keys
root@981ebdb4319e:/# chgrp agent-core /var/log/agent-app
# 확인
root@981ebdb4319e:/# ls -ld $AGENT_HOME/upload_files
drwxr-xr-x 1 root agent-common 0 May 13 11:49 /home/agent-admin/agent-app/upload_files
root@981ebdb4319e:/# ls -ld $AGENT_HOME/api_keys
drwxr-xr-x 1 root agent-core 0 May 13 11:49 /home/agent-admin/agent-app/api_keys
root@981ebdb4319e:/# ls -ld /var/log/agent-app
drwxr-xr-x 1 root agent-core 0 May 13 12:10 /var/log/agent-app
```

#### 3.3.2. 기본 권한 및 SetGID 적용
# upload_files에 2770을 주면 이후 생성 파일도 그룹 소유권이 유지됩니다.
```bash
root@981ebdb4319e:/# chmod 2770 $AGENT_HOME/upload_files
root@981ebdb4319e:/# chmod 770 $AGENT_HOME/api_keys
root@981ebdb4319e:/# chmod 770 /var/log/agent-app

#확인
root@981ebdb4319e:/# ls -ld $AGENT_HOME/upload_files
drwxrws--- 1 root agent-common 0 May 13 11:49 /home/agent-admin/agent-app/upload_files
root@981ebdb4319e:/# ls -ld $AGENT_HOME/api_keys
drwxrwx--- 1 root agent-core 0 May 13 11:49 /home/agent-admin/agent-app/api_keys
root@981ebdb4319e:/# ls -ld /var/log/agent-app
drwxrwx--- 1 root agent-core 0 May 13 12:10 /var/log/agent-app
```

##### 3.3.3. Default ACL 설정 (자동 권한 상속)
# 새로 생기는 파일에도 그룹 rwx 권한을 강제로 부여합니다.
```bash
root@981ebdb4319e:/# getfacl  $AGENT_HOME/upload_files
getfacl: Removing leading '/' from absolute path names
# file: home/agent-admin/agent-app/upload_files
# owner: root
# group: agent-common
# flags: -s-
user::rwx
group::rwx
other::---

root@981ebdb4319e:/# getfacl  $AGENT_HOME/api_keys/   
getfacl: Removing leading '/' from absolute path names
# file: home/agent-admin/agent-app/api_keys/
# owner: root
# group: agent-core
user::rwx
group::rwx
other::---

root@981ebdb4319e:/# getfacl  /var/log/agent-app   
getfacl: Removing leading '/' from absolute path names
# file: var/log/agent-app
# owner: root
# group: agent-core
user::rwx
group::rwx
other::---

root@981ebdb4319e:/# setfacl -d -m g:agent-common:rwx $AGENT_HOME/upload_files
root@981ebdb4319e:/# setfacl -d -m g:agent-core:rwx $AGENT_HOME/api_keys
root@981ebdb4319e:/# setfacl -d -m g:agent-core:rwx /var/log/agent-app
```

#### 3.4. 최종 검증 및 상태 확인**
설정이 요구사항에 맞게 반영되었는지 반드시 확인해야 합니다.



```bash
# 계정 그룹 소속 확인
root@981ebdb4319e:/# id agent-admin && id agent-dev && id agent-test
```

# 디렉토리 권한 및 그룹 확인

현재는 디렉토리의 owner group 자체가 agent-common 이므로,
default:group::rwx 와 default:group:agent-common:rwx 가
유사하게 보일 수 있다.
ACL은 여러 그룹에 세밀한 권한을 줄 때 진가를 발휘한다.

```bash
root@981ebdb4319e:/#  ls -ld $AGENT_HOME/upload_files
drwxrws---+ 1 root agent-common 0 May 13 11:49 /home/agent-admin/agent-app/upload_files
root@981ebdb4319e:/# ls -ld $AGENT_HOME/api_keys
drwxrwx---+ 1 root agent-core 0 May 13 11:49 /home/agent-admin/agent-app/api_keys
root@981ebdb4319e:/# ls -ld /var/log/agent-app
drwxrwx---+ 1 root agent-core 0 May 13 12:10 /var/log/agent-app

root@981ebdb4319e:/# getfacl  $AGENT_HOME/upload_files
getfacl: Removing leading '/' from absolute path names
# file: home/agent-admin/agent-app/upload_files
# owner: root
# group: agent-common
# flags: -s-
user::rwx
group::rwx
other::---
default:user::rwx
default:group::rwx
default:group:agent-common:rwx
default:mask::rwx
default:other::---

root@981ebdb4319e:/# getfacl  $AGENT_HOME/api_keys/
getfacl: Removing leading '/' from absolute path names
# file: home/agent-admin/agent-app/api_keys/
# owner: root
# group: agent-core
user::rwx
group::rwx
other::---
default:user::rwx
default:group::rwx
default:group:agent-core:rwx
default:mask::rwx
default:other::---

root@981ebdb4319e:/# getfacl  /var/log/agent-app
getfacl: Removing leading '/' from absolute path names
# file: var/log/agent-app
# owner: root
# group: agent-core
user::rwx
group::rwx
other::---
default:user::rwx
default:group::rwx
default:group:agent-core:rwx
default:mask::rwx
default:other::---
```

---

### **💡 고쳐진 내용의 핵심 요약**
1.  **순서 교정:** 에러를 방지하기 위해 `groupadd` → `useradd` → `chgrp` 순서로 재배치했습니다.
2.  **`api_keys` 보안 강화:** 이전 작성본에서 `agent-common`으로 되어 있던 `api_keys`의 그룹을 **`agent-core`**로 수정하여 테스트 계정의 접근을 차단했습니다.
3.  **SetGID 도입:** 공유 폴더에 `2770` 권한을 부여하여 협업 중 발생하는 권한 오류를 원천 봉쇄했습니다.
4.  **ACL 적용:** `setfacl`을 통해 파일 생성 시마다 권한을 일일이 수정하지 않아도 보안 정책이 유지되도록 자동화했습니다.

이제 이 순서대로 터미널에 입력하시면 어제의 에러 없이 완벽한 보안 체계를 구축하실 수 있습니다. 바로 실행해 보시겠어요?