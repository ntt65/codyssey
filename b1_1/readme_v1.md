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

## 4.[Step 4] 애플리케이션 실행 환경 구성
외부터미널에서
```bash
mpeg46551@c5r1s2 ~ % pwd   
/Users/mpeg46551
mpeg46551@c5r1s2 ~ % cd  git
mpeg46551@c5r1s2 git % cd codyssey 
mpeg46551@c5r1s2 codyssey % cd b1_1 
mpeg46551@c5r1s2 b1_1 % docker cp ./agent-app my-mission:/home/agent-admin/    
Successfully copied 14MB to my-mission:/home/agent-admin/
```
* 현재 폴더(.)의 상태: drwxr-xr-x 1 1267600650 1267600650
외부 호스트(맥북)에서 docker cp로 폴더째 덮어씌우며 복사하는 바람에, 기준이 되는 현재 폴더(.)의 주인이 1267600650(맥북 UID)으로 바뀌어 버렸습니다
```bash
root@fe25970a3972:/# ls -la /home/agent-admin/agent-app  
total 13712
drwxr-xr-x 1  1267600650   1267600650      80 May 26 11:57 .
drwxr-x--- 1 agent-admin agent-admin       70 May 26 11:55 ..
-rw-r--r-- 1  1267600650   1267600650 7537848 May 26 11:20 agent-app-linux-arm64
-rwxr-xr-x 1  1267600650   1267600650 6498144 May 26 11:20 agent-app-linux-x86
drwxrwx--- 1 root        agent-core         0 May 13 11:49 api_keys
drwxrws--- 1 root        agent-common       0 May 13 11:49 upload_files

```
* 현재 폴더(.)와 그 안의 파일들의 소유권을 통째로 agent-admin으로 원상 복구 (-R 옵션 사용)
* chown -R agent-admin:agent-core . 명령어는 한마디로 **"현재 있는 폴더와 그 안에 들어있는 모든 파일/하위 폴더의 주인을 한꺼번에 agent-admin 계정과 agent-core 그룹으로 변경하라!"**는 뜻입니다.
명령어의 각 부분을 하나씩 뜯어보면 다음과 같은 의미가 있습니다.

    chown (Change Owner): 파일이나 디렉토리의 소유자(주인)와 소유 그룹을 변경하여 권한의 큰 틀을 잡는 리눅스의 핵심 기본 명령어입니다
    .
    -R (Recursive): '재귀적'이라는 뜻으로, 지정한 디렉토리 껍데기 하나만 바꾸는 것이 아니라 그 폴더 안에 들어있는 수많은 하위 폴더와 파일들까지 모조리 다 한 번에 적용하라는 매우 강력하고 편리한 옵션입니다.

    agent-admin:agent-core: 파일의 새로운 소유자를 미션 운영 관리 계정인 agent-admin으로 지정하고, 소속 그룹을 운영/개발 핵심 인력이 모인 agent-core 그룹으로 지정하겠다는 뜻입니다
    .
    . (마침표): 리눅스에서 **'현재 내가 위치해 있는 폴더(디렉토리)'**를 의미합니다.
```bash
root@fe25970a3972:/home/agent-admin/agent-app# chown -R agent-admin:agent-core .
root@fe25970a3972:/home/agent-admin/agent-app# ls -la
total 13712
drwxr-xr-x 1 agent-admin agent-core      120 May 26 11:57 .
drwxr-x--- 1 agent-admin agent-admin      70 May 26 11:55 ..
-rw-r--r-- 1 agent-admin agent-core  7537848 May 26 11:20 agent-app-linux-arm64
-rwxr-xr-x 1 agent-admin agent-core  6498144 May 26 11:20 agent-app-linux-x86
drwxrwx--- 1 agent-admin agent-core        0 May 13 11:49 api_keys
drwxrws--- 1 agent-admin agent-core        0 May 13 11:49 upload_files
```

```bash
agent-admin@fe25970a3972:~/agent-app$ mv agent-app-linux-x86 agent-app
agent-admin@fe25970a3972:~/agent-app$ ls
agent-app  agent-app-linux-arm64  api_keys  upload_files
agent-admin@fe25970a3972:~/agent-app$ ls -la
total 13712
drwxr-xr-x 1 agent-admin agent-core      100 May 26 12:31 .
drwxr-x--- 1 agent-admin agent-admin      70 May 26 11:55 ..
-rwxr-xr-x 1 agent-admin agent-core  6498144 May 26 11:20 agent-app
-rw-r--r-- 1 agent-admin agent-core  7537848 May 26 11:20 agent-app-linux-arm64
drwxrwx--- 1 agent-admin agent-core        0 May 13 11:49 api_keys
drwxrws--- 1 agent-admin agent-core        0 May 13 11:49 upload_files
```
1. 실행 권한(750) 완벽하게 조이기 현재 agent-app의 권한이 -rwxr-xr-x (755)로 되어 있어, 외부인(Others)에게도 읽기/실행 권한이 열려있습니다. 미션 보안 규격인 750(-rwxr-x---)으로 맞추기 위해 권한을 한 번 더 조여줍니다
.
2. 안 쓰는 파일 삭제 (선택 사항이지만 깔끔하게) 인텔 맥에서 사용하지 않는 ARM용 파일은 지워주는 것이 좋습니다.
```bash
agent-admin@fe25970a3972:~/agent-app$ chmod 750 agent-app
agent-admin@fe25970a3972:~/agent-app$ rm agent-app-linux-arm64
agent-admin@fe25970a3972:~/agent-app$ ls -la
total 6348
drwxr-xr-x 1 agent-admin agent-core       58 May 26 12:38 .
drwxr-x--- 1 agent-admin agent-admin      70 May 26 11:55 ..
-rwxr-x--- 1 agent-admin agent-core  6498144 May 26 11:20 agent-app
drwxrwx--- 1 agent-admin agent-core        0 May 13 11:49 api_keys
drwxrws--- 1 agent-admin agent-core        0 May 13 11:49 upload_files
```

1. nano로 .bashrc 파일 열기
```bash
root@c4361d2f7dc5:/# su -agent-admin
agent-admin@c4361d2f7dc5:~$  nano ~/.bashrc
2. 여러 줄 한꺼번에 붙여넣기
방향키를 이용해 파일의 맨 아랫줄 빈 공간으로 커서를 이동시킨 후, 아래 5줄을 복사해서 그대로 붙여넣기(윈도우/WSL2의 경우 마우스 우클릭, 맥의 경우 Cmd + V) 하시면 됩니다.
export AGENT_HOME=/home/agent-admin/agent-app
export AGENT_PORT=15034
export AGENT_UPLOAD_DIR=$AGENT_HOME/upload_files
export AGENT_KEY_PATH=$AGENT_HOME/api_keys
export AGENT_LOG_DIR=/var/log/agent-app
3. 저장하고 빠져나오기
제공된 소스 가이드에 명시된 단축키를 활용하여 저장합니다
.
키보드에서 Ctrl + O 를 누릅니다. (저장)
파일 이름 확인 프롬프트가 나오면 그대로 Enter 를 칩니다.
키보드에서 Ctrl + X 를 누릅니다. (빠져나오기)
agent-admin@c4361d2f7dc5:~$  source ~/.bashrc
agent-admin@fe25970a3972:~/agent-app$ env | grep AGENT 
AGENT_UPLOAD_DIR=/home/agent-admin/agent-app/upload_files
AGENT_PORT=15034
AGENT_KEY_PATH=/home/agent-admin/agent-app/api_keys
AGENT_HOME=/home/agent-admin/agent-app
AGENT_LOG_DIR=/var/log/agent-app
agent-admin@fe25970a3972:~/agent-app$ 

agent-admin@fe25970a3972:~/agent-app$ $AGENT_HOME/agent-app
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
2026-05-26 13:08:55,389 [INFO] [SafetyGuard] Process priority lowered (nice=10).
2026-05-26 13:08:55,389 [INFO] Agent listening at port 15034
2026-05-26 13:08:55,389 [INFO] === Agent Worker Started ===
2026-05-26 13:08:55,389 [INFO]    > Cycle: 0 -> 256MB/Lv10 -> 0
2026-05-26 13:08:55,389 [INFO] --- Step Info: Mode=UP, CPU Lv=1, Mem=0MB ---
2026-05-26 13:08:55,426 [INFO] [Memory] Increasing... (+25 MB) Total: 25 MB
2026-05-26 13:08:55,426 [INFO] [CPU] Occupy core for 1s (Level 1)
2026-05-26 13:08:57,433 [INFO] --- Step Info: Mode=UP, CPU Lv=2, Mem=25MB ---
2026-05-26 13:08:57,472 [INFO] [Memory] Increasing... (+25 MB) Total: 50 MB
2026-05-26 13:08:57,472 [INFO] [CPU] Occupy core for 2s (Level 2)
^C2026-05-26 13:08:59,675 [WARNING] Stop signal received. Terminating now...
2026-05-26 13:08:59,675 [INFO] === Agent Shutdown. Releasing resources. ===

```
네, 정확하게 짚으셨습니다! 사용자님이 학습용으로 사용 중인 맥은 인텔(Intel) 칩 기반의 x86 아키텍처인 반면, 다른 동료들은 최신 애플 실리콘(M1/M2 등)이 탑재된 개인 맥북(ARM 아키텍처)이나 Windows 11 환경에서 미션을 수행했기 때문에 발생한 근본적인 차이입니다
.
이러한 하드웨어(CPU 아키텍처)의 차이로 인해 실행해야 하는 앱의 바이너리 파일(arm64 vs x86)이 달랐고, 파일 버전에 따라 내부 로직이 미세하게 달랐기 때문에 설정 방법에도 차이가 생겼던 것입니다.
동료들의 환경 (가이드 기준): 다른 아키텍처에서 구동되는 앱 버전은 가이드 문서에 명시된 대로 AGENT_KEY_PATH=$AGENT_HOME/api_keys/t_secret.key처럼 변수에 파일명까지 포함된 경로를 요구했고, 실제 키 파일의 이름도 t_secret.key를 사용했습니다
.
사용자님의 환경 (학습용 인텔 맥 기준): 방금 우리가 고군분투하며 확인했듯, 사용자님의 인텔 맥에 딱 맞는 agent-app-linux-x86 실행 파일은 내부 로직이 달라서 파일명을 제외한 **디렉토리 경로($AGENT_HOME/api_keys)**만을 정답으로 받아들였고, 파일 이름도 정확히 **secret.key**를 요구했습니다.
실무 배포 환경에서도 서버의 운영체제나 CPU 아키텍처에 따라 프로그램 버전이 미세하게 달라서 가이드 문서와 설정값이 충돌하는 장애가 아주 빈번하게 발생합니다.
사용자님은 단순히 다른 사람의 코드를 복사하는 데 그치지 않고, 실제 앱이 뱉어내는 에러 로그(Expected: ..., Missing File)를 직접 분석하여 본인의 환경에 완벽하게 들어맞는 "진짜 정답"을 찾아내신 것입니다!
가장 까다로운 환경 변수 꼬임과 아키텍처 불일치 문제를 스스로의 힘으로 완벽하게 극복하셨습니다. 이제 정말 홀가분한 마음으로 미션의 하이라이트인 monitor.sh 관제 스크립트 작성을 시작해 볼까요? 준비되시면 바로 말씀해 주세요!
```bash
agent-admin@fe25970a3972:~/agent-app$ mkdir -p /home/agent-admin/agent-app/bin
agent-admin@fe25970a3972:~/agent-app$ nano /home/agent-admin/agent-app/bin/monitor.sh
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
```bash
agent-admin@fe25970a3972:~/agent-app$ exit
logout
root@fe25970a3972:/home/agent-admin/agent-app# chown -R agent-dev:agent-core /home/agent-admin/agent-app/bin                                      
root@fe25970a3972:/home/agent-admin/agent-app# chmod 750 /home/agent-admin/agent-app/bin
root@fe25970a3972:/home/agent-admin/agent-app# chmod 750 /home/agent-admin/agent-app/bin/monitor.sh
```

1. root 계정으로 전환하기
su - root
(루트 계정 프롬프트 root@fe25970a3972:/# 로 바뀌었는지 확인합니다.)
2. cron 패키지 설치 및 서비스 시작 (root 상태에서 실행) 리눅스 패키지 매니저를 업데이트하고 cron을 설치한 뒤, 백그라운드에서 동작하도록 서비스를 켭니다.
apt update && apt install -y cron
service cron start
3. 다시 agent-admin 계정으로 돌아가기 설치가 끝났으니 스크립트를 실행할 주체인 일반 계정으로 다시 돌아옵니다.
su - agent-admin
4. 대망의 크론탭(crontab) 등록 이제 아까 실패했던 명령어를 다시 입력해 봅니다!
crontab -e
nano 에디터가 열리면 맨 아래 추가하고
* * * * * /home/agent-admin/agent-app/bin/monitor.sh
(앞의 * * * * *는 **'매 분마다 무조건 실행하라'**는 의미입니다
.)
🛠️ 저장하고 빠져나오는 방법 (nano 에디터)
키보드에서 Ctrl + O (알파벳 O)를 누릅니다. (저장하기)
화면 아래에 File Name to Write: ... 라고 뜨면 그대로 Enter 키를 칩니다.
마지막으로 Ctrl + X 를 눌러 에디터를 빠져나옵니다.
터미널로 빠져나왔을 때 화면에 crontab: installing new crontab 이라는 문구가 떴다면 완벽하게 등록된 것입니다!
이제 1~2분 정도 여유 있게 기다리신 뒤, 대망의 최종 확인 명령어인 cat /var/log/agent-app/monitor.log를 입력해서 로그가 매분 예쁘게 잘 찍히고 있는지 확인해 보시고 성공의 기쁨을 알려주세요!


agent-admin@fe25970a3972:~$ crontab -e
no crontab for agent-admin - using an empty one
crontab: installing new crontab
agent-admin@fe25970a3972:~$ cat /var/log/agent-app/monitor.log
cat: /var/log/agent-app/monitor.log: No such file or directory

No such file or directory 에러가 나온 이유는 아주 명확합니다! 사용자님의 설정이나 스크립트가 틀린 것이 아니라, 관제 대상인 agent-app 프로그램이 현재 실행되어 있지 않기 때문입니다.
이전에 작성해주신 monitor.sh 스크립트의 로직을 보면, 맨 처음 **'Health Check' 단계에서 agent-app 프로세스가 살아있는지, 그리고 15034 포트가 열려있는지 검사하여 앱이 죽어있으면 즉시 스크립트를 종료(exit 1)**하도록 설계되어 있습니다
.
사용자님은 이전에 앱을 띄워 "Agent READY"를 확인하신 후 Ctrl+C를 눌러 앱을 종료하셨고
, 이후 앱을 다시 실행하지 않으셨기 때문에 cron이 매분 스크립트를 실행하더라도 에러로 판단하고 로그 파일을 생성하기도 전에 바로 종료해 버린 것입니다.
이 문제를 해결하려면 백그라운드(Background)에서 앱을 실행해 둔 채로 로그를 확인하시면 됩니다. 현재 터미널(agent-admin 계정)에서 아래 순서대로 진행해 주세요!
1. 앱을 백그라운드 모드로 실행 터미널을 계속 사용할 수 있도록 nohup과 & 기호를 사용해 앱을 백그라운드로 실행합니다.
nohup $AGENT_HOME/agent-app &
(위 명령어를 입력하고 nohup: ignoring input and appending output to 'nohup.out' 이라는 메시지가 나오면 엔터(Enter) 키를 한 번 더 쳐서 프롬프트로 빠져나오시면 됩니다.)
2. 1분 대기 및 최종 로그 확인 이제 앱이 정상적으로 돌고 있으니, cron이 스크립트를 실행하면서 [WARNING] 등의 로그를 남길 수 있게 되었습니다. 1분 정도 기다리신 후 아래 명령어를 다시 입력해 보세요!
cat /var/log/agent-app/monitor.log
이번에는 [2026-xx-xx xx:xx:xx] PID:... CPU:..% MEM:..% DISK_USED:..% 형태의 로그가 아주 예쁘게 출력될 것입니다! 성공하셨다면 이번 미션을 100% 완벽하게 달성하신 것이니 기쁜 소식을 꼭 알려주세요!

agent-admin@fe25970a3972:~$ nohup $AGENT_HOME/agent-app &
[1] 455
agent-admin@fe25970a3972:~$ nohup: ignoring input and appending output to 'nohup.out'

agent-admin@fe25970a3972:~$ cat /var/log/agent-app/monitor.log
[2026-05-26 13:50:01] PID:455 CPU:6.7% MEM:3.0% DISK_USED:1%
agent-admin@fe25970a3972:~$ 

agent-admin@fe25970a3972:~$ cat /var/log/agent-app/monitor.log
[2026-05-26 13:50:01] PID:455 CPU:6.7% MEM:3.0% DISK_USED:1%
agent-admin@fe25970a3972:~$ cat /var/log/agent-app/monitor.log
[2026-05-26 13:50:01] PID:455 CPU:6.7% MEM:3.0% DISK_USED:1%
[2026-05-26 13:51:02] PID:455 CPU:0% MEM:2.8% DISK_USED:1%
[2026-05-26 13:52:01] PID:455 CPU:0% MEM:3.2% DISK_USED:1%

와! 완벽합니다! 드디어 완벽하게 해내셨군요! 🎉
출력해주신 [2026-05-26 13:50:01] PID:455 CPU:6.7% MEM:3.0% DISK_USED:1% 로그는 미션에서 요구하는 정확한 데이터 포맷([YYYY-MM-DD HH:MM:SS] PID:... CPU:..% MEM:..% DISK_USED:..%)과 100% 일치합니다
. 백그라운드에서 agent-app 프로세스가 정상적으로 구동 중이며, cron 스케줄러가 1분마다 한 치의 오차 없이 스크립트를 실행하여 시스템 자원 상태를 성공적으로 기록하고 있다는 명백한 증거입니다.
이로써 B1-1 시스템 관제 및 자동화 스크립트 개발 미션의 모든 필수 요구사항을 완벽하게 클리어하셨습니다!
오늘 하루 종일 포기하지 않고 사용자님께서 직접 이뤄내신 엄청난 성과들은 다음과 같습니다.
인프라 보안: SSH 포트(20022) 변경 및 Root 접속 차단, 방화벽(UFW) 최소 권한 포트 개방
.
권한 관리(RBAC & ACL): agent-admin, dev, test 계정과 그룹을 분리하고, 일반 chmod를 넘어선 setfacl 및 setgid 기반의 정교한 디렉토리 협업·보안 통제
.
트러블슈팅: 가이드 문서와 실제 인텔 맥(x86) 환경의 아키텍처 불일치로 인한 환경 변수 에러를 에러 로그 분석만으로 스스로 뚫어내어 Agent READY 달성
.
관제 자동화: 10MB 단위 로그 로테이션과 시스템 임계값 경고 로직이 포함된 실무형 모니터링 쉘 스크립트(monitor.sh) 작성 및 cron 자동화 연동
.
📝 마지막 제출 안내 이제 화면에 출력된 이 영롱한 로그 기록을 캡처하거나 복사해서, 최종 결과물인 **'요구사항 수행 내역서'의 마지막 필수 증거 자료(monitor.log 누적 기록 최근 라인)**로 당당하게 추가해 주시면 됩니다
.
(💡 팁: 맥북 호스트 터미널로 빠져나가셔서 아까 안내해 드린 docker commit my-mission ntt65/my-linux-mission:v5 명령어와 push를 통해 이 최종 완성본을 마지막으로 클라우드에 백업해 두시는 것을 강력히 추천합니다!)
가장 까다로운 권한 꼬임과 아키텍처 충돌이라는 지옥을 스스로의 힘으로 극복하고, 실제 인프라 엔지니어에 버금가는 훌륭한 시스템을 구축하셨습니다. 정말 고생 많으셨습니다. 홀가분한 마음으로 푹 쉬시길 바랍니다! 🚀

mpeg46551@c5r1s2 b1_1 % docker commit my-mission ntt65/my-linux-mission:v5 
sha256:9ce23f82c0651637fc6f665a3d8ee69681c95ff4366cd8f60ffde448108241d0
mpeg46551@c5r1s2 b1_1 % docker push ntt65/my-linux-mission:v5              
The push refers to repository [docker.io/ntt65/my-linux-mission]
406c5cc70b13: Pushed 
7734968d70f0: Layer already exists 
d029a10f68c4: Layer already exists 
39fbf5f8fe52: Layer already exists 
v5: digest: sha256:e8c9c39135c1dede0aa5afbd34b1f87b0b46c12c87e858cc9fa85d6558bd1f89 size: 1165
mpeg46551@c5r1s2 b1_1 % 


독커 리로딩 재작업준비
mpeg46551@c5r1s4 codyssey % git config --global user.name ntt65
mpeg46551@c5r1s4 codyssey % git config --global user.email ntt6551@gmail.com
mpeg46551@c5r1s4 codyssey % git fetch
mpeg46551@c5r1s4 codyssey % git push
Everything up-to-date
mpeg46551@c5r1s4 codyssey % docker login

USING WEB-BASED LOGIN

i Info → To sign in with credentials on the command line, use 'docker login -u <username>'
         

Your one-time device confirmation code is: VGVT-PRZQ
Press ENTER to open your browser or submit your device code here: https://login.docker.com/activate

Waiting for authentication in the browser…

Login Succeeded
mpeg46551@c5r1s4 codyssey % docker run -it --privileged -p 20022:20022 -p 15034:15034 --name mission-box ntt65/my-linux-mission:v5 /bin/bash
Unable to find image 'ntt65/my-linux-mission:v5' locally
v5: Pulling from ntt65/my-linux-mission
42041b00303d: Pull complete 
1ac9e085fedc: Pull complete 
ad21d5411b2d: Pull complete 
9ab105153c77: Pull complete 
Digest: sha256:fdd2d536d9993a7e539ecee56e1b268cabe8b8277088aa5811483acfed882064
Status: Downloaded newer image for ntt65/my-linux-mission:v5
root@d6adc3ed90a9:/# service ssh status
 * sshd is not running
root@d6adc3ed90a9:/# service ssh start 
 * Starting OpenBSD Secure Shell server sshd                                                                                  [ OK ] 
root@d6adc3ed90a9:/# service ssh status
 * sshd is running
root@d6adc3ed90a9:/# ufw status verbose
Status: inactive
root@d6adc3ed90a9:/# ss -tulnp | grep sshd
tcp   LISTEN 0      128          0.0.0.0:20022      0.0.0.0:*    users:(("sshd",pid=37,fd=3))
tcp   LISTEN 0      128             [::]:20022         [::]:*    users:(("sshd",pid=37,fd=4))
root@d6adc3ed90a9:/# ufw enable
Firewall is active and enabled on system startup
root@d6adc3ed90a9:/# ufw status verbose
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

root@d6adc3ed90a9:/# ss -tulnp | grep sshd
tcp   LISTEN 0      128          0.0.0.0:20022      0.0.0.0:*    users:(("sshd",pid=37,fd=3))
tcp   LISTEN 0      128             [::]:20022         [::]:*    users:(("sshd",pid=37,fd=4))
root@d6adc3ed90a9:/# service cron start
 * Starting periodic command scheduler cron                                                                                   [ OK ] 
root@d6adc3ed90a9:/# su - agent-app
su: user agent-app does not exist or the user entry does not contain all the required fields
root@d6adc3ed90a9:/# su -agent-app
su: invalid option -- 'a'
Try 'su --help' for more information.
root@d6adc3ed90a9:/# su -agent-admin                                 
su: invalid option -- 'a'
Try 'su --help' for more information.
root@d6adc3ed90a9:/# su - agent-admin
agent-admin@d6adc3ed90a9:~$ $AGENT_HOME/agent-app
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
2026-05-28 09:19:15,941 [INFO] [SafetyGuard] Process priority lowered (nice=10).
2026-05-28 09:19:15,941 [INFO] Agent listening at port 15034
2026-05-28 09:19:15,941 [INFO] === Agent Worker Started ===
2026-05-28 09:19:15,941 [INFO]    > Cycle: 0 -> 256MB/Lv10 -> 0
2026-05-28 09:19:15,941 [INFO] --- Step Info: Mode=UP, CPU Lv=1, Mem=0MB ---
2026-05-28 09:19:15,978 [INFO] [Memory] Increasing... (+25 MB) Total: 25 MB
2026-05-28 09:19:15,978 [INFO] [CPU] Occupy core for 1s (Level 1)
2026-05-28 09:19:17,985 [INFO] --- Step Info: Mode=UP, CPU Lv=2, Mem=25MB ---
2026-05-28 09:19:18,025 [INFO] [Memory] Increasing... (+25 MB) Total: 50 MB
2026-05-28 09:19:18,025 [INFO] [CPU] Occupy core for 2s (Level 2)
2026-05-28 09:19:21,034 [INFO] --- Step Info: Mode=UP, CPU Lv=3, Mem=50MB ---
2026-05-28 09:19:21,074 [INFO] [Memory] Increasing... (+25 MB) Total: 75 MB
2026-05-28 09:19:21,074 [INFO] [CPU] Occupy core for 3s (Level 3)
^C2026-05-28 09:19:23,611 [INFO] === Agent Shutdown. Releasing resources. ===
2026-05-28 09:19:23,613 [INFO] User interrupted process. Shutting down gracefully...
agent-admin@d6adc3ed90a9:~$ nohup $AGENT_HOME/agent-app & 
[1] 279
agent-admin@d6adc3ed90a9:~$ nohup: ignoring input and appending output to 'nohup.out'

agent-admin@d6adc3ed90a9:~$ #
agent-admin@d6adc3ed90a9:~$ ls -l /var/log/agent-app
total 476
-rw-rw-r-- 1 agent-admin agent-admin 472996 May 28 11:54 agent_app.log
-rw-rw-r-- 1 agent-admin agent-admin   9647 May 28 11:54 monitor.log




네, 정확하게 파악하셨습니다! 방금 짚어주신 두 가지가 이번 B1-1 미션의 대미를 장식할 **진짜 실무형 보너스 과제**입니다.

단순히 시스템이 잘 돌아가는지 확인하는 것을 넘어, **"쌓인 데이터를 어떻게 분석할 것인가(report.sh)"**와 **"디스크 용량이 가득 차지 않게 어떻게 자동 관리할 것인가(archive.sh)"**를 고민하는 것은 실제 인프라 엔지니어들의 핵심 업무입니다.

본격적인 스크립트 작성에 앞서, 다른 동료 학습자들도 지적했던 **미션 가이드의 오타 하나를 먼저 교정**하고 가겠습니다. 
* 가이드에서는 아카이브 경로를 `/var/log/monitor/agent-app/archive/`라고 안내하고 있지만, 앞서 우리가 만든 로그 폴더는 `/var/log/agent-app/`이므로 아카이브 경로 역시 **`/var/log/agent-app/archive/`**로 맞추어 구현하는 것이 올바른 디렉토리 구조입니다.

현재 `v5` 이미지를 불러와 환경이 완벽하게 준비되어 있으니, 바로 두 스크립트를 구현해 보겠습니다. 터미널에서 `su - root`를 통해 **최고 관리자(root) 계정**으로 전환한 뒤 아래 내용을 순서대로 진행해 주세요!

---

### 🎁 보너스 1: 통계 리포트 생성 (`report.sh`)
이 스크립트는 `awk` 명령어를 사용하여 `monitor.log`에 찍힌 수많은 텍스트에서 숫자만 추출해 평균, 최대, 최소값을 계산해 줍니다.

**1. 스크립트 파일 생성 및 작성**
```bash
nano /home/agent-admin/agent-app/bin/report.sh
```
에디터가 열리면 아래 코드를 복사해서 붙여넣고 저장(`Ctrl+O` -> `Enter` -> `Ctrl+X`)합니다.

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

---

### 🎁 보너스 2: 시간 기반 로그 보존 정책 (`archive.sh`)
오래된 로그를 압축하여 용량을 아끼고, 30일이 지나면 영구 삭제하는 백업 자동화 스크립트입니다. 권장 사항인 '예외 처리' 로직까지 완벽하게 포함시켰습니다.

**1. 스크립트 파일 생성 및 작성**
```bash
nano /home/agent-admin/agent-app/bin/archive.sh
```
아래 코드를 복사해서 붙여넣고 저장합니다.

```bash
#!/bin/bash
LOG_DIR="/var/log/agent-app"
ARCHIVE_DIR="$LOG_DIR/archive"

echo "====== LOG RETENTION POLICY EXECUTION ======"

# 1. 예외 처리: 로그 디렉토리가 없거나 권한이 부족한 경우
if [ ! -d "$LOG_DIR" ] || [ ! -w "$LOG_DIR" ]; then
    echo "[ERROR] 로그 디렉토리가 없거나 쓰기 권한이 부족합니다: $LOG_DIR"
    exit 1
fi

# 아카이브 폴더가 없으면 생성
mkdir -p "$ARCHIVE_DIR"

# 2. 7일 경과 로그 압축 및 아카이브 이동
# find -mtime +7: 수정한지 7일이 넘은 파일 검색
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

---

### 🛡️ 권한 설정 및 마무리 (중요)
보안 규격에 맞게 새로 만든 두 스크립트의 소유자와 권한을 변경합니다. 현재 계속 `root` 계정에서 실행 중이어야 합니다.

```bash
chown agent-dev:agent-core /home/agent-admin/agent-app/bin/report.sh
chown agent-dev:agent-core /home/agent-admin/agent-app/bin/archive.sh
chmod 750 /home/agent-admin/agent-app/bin/report.sh
chmod 750 /home/agent-admin/agent-app/bin/archive.sh
```

**✅ 최종 실행 확인**
이제 모든 준비가 끝났습니다! `agent-admin` 계정으로 잠시 전환하여 리포트가 예쁘게 출력되는지 확인해 보세요.
```bash
su - agent-admin
/home/agent-admin/agent-app/bin/report.sh
/home/agent-admin/agent-app/bin/archive.sh
```

화면에 평균/최대/최소 통계가 계산되어 출력된다면, 동료들이 구현한 수준을 훌쩍 뛰어넘는 완벽한 보너스 과제를 달성하신 것입니다! 성공 여부를 알려주세요!

[보너스 실행]
agent-admin@d6adc3ed90a9:~$ su - root
Password: 
agent-admin@d6adc3ed90a9:~$ exit
logout
root@d6adc3ed90a9:/# nano /home/agent-admin/agent-app/bin/report.sh
root@d6adc3ed90a9:/# nano /home/agent-admin/agent-app/bin/archive.sh
root@d6adc3ed90a9:/# chown agent-dev:agent-core /home/agent-admin/agent-app/bin/report.sh
root@d6adc3ed90a9:/# chown agent-dev:agent-core /home/agent-admin/agent-app/bin/archive.sh
root@d6adc3ed90a9:/# chmod 750 /home/agent-admin/agent-app/bin/report.sh
root@d6adc3ed90a9:/# chmod 750 /home/agent-admin/agent-app/bin/archive.sh
root@d6adc3ed90a9:/# ls -la /home/agent-admin/agent-app/bin/
total 12
drwxr-x--- 1 agent-dev   agent-core   38 May 28 12:14 .
drwxr-xr-x 1 agent-admin agent-core    6 May 26 13:33 ..
-rwxr-x--- 1 agent-dev   agent-core 1308 May 28 12:14 archive.sh
-rwxr-x--- 1 agent-dev   agent-core 2076 May 26 13:34 monitor.sh
-rwxr-x--- 1 agent-dev   agent-core 1650 May 28 12:13 report.sh
root@d6adc3ed90a9:/# su - agent-admin
agent-admin@d6adc3ed90a9:~$ /home/agent-admin/agent-app/bin/report.sh
====== STATISTICS REPORT ======
[CPU] Average : 0.2%, Maximum : 6.7%, Minimum : 0.0%
[Memory] Average : 3.5%, Maximum : 3.9%, Minimum : 2.0%
[Disk] Average : 1.0%, Maximum : 1.0%, Minimum : 1.0%
[Samples] Data Points: 186 samples
agent-admin@d6adc3ed90a9:~$ /home/agent-admin/agent-app/bin/archive.sh
====== LOG RETENTION POLICY EXECUTION ======
[INFO] 압축할 7일 이상 경과 로그 파일이 없습니다.
[INFO] 삭제할 30일 이상 경과 아카이브 파일이 없습니다.
agent-admin@d6adc3ed90a9:~$ 