리눅스 시스템에서 계정(사용자)과 **그룹**은 시스템 자원에 대한 접근 권한을 관리하고 보안을 유지하는 가장 기초적인 요소입니다. 제공된 자료를 바탕으로 각각의 정의와 역할에 대해 설명해 드립니다.

### 1. 계정 (User Account)의 정의 및 역할

계정은 리눅스 시스템을 사용하는 개별 주체를 식별하기 위한 단위입니다.

* **정의**: 시스템에 로그인하고 파일을 생성하거나 프로그램을 실행할 수 있는 고유한 식별자입니다.


* **Root 계정**: 시스템의 모든 권한을 가진 관리자 계정으로, 보안을 위해 원격 접속 시 직접 로그인을 차단하는 것이 권장됩니다.


* **일반 계정**: 특정 목적(운영, 개발, 테스트 등)을 위해 생성되며, 보안상 관리자 권한이 필요할 때만 `sudo` 등을 통해 권한을 얻어 사용합니다.


* **주요 명령어**: `useradd` 명령어를 통해 새로운 계정을 생성하며, `-m` 옵션으로 홈 디렉토리를 만들거나 `-s` 옵션으로 기본 쉘을 지정할 수 있습니다.

리눅스에서 `useradd` 명령어의 **`-s` 옵션은 사용자가 로그인했을 때 사용할 '기본 쉘(Login Shell)'을 지정**하는 역할을 합니다,.

구체적인 내용은 다음과 같습니다.

*   **역할:** 시스템에 접속한 사용자가 명령어를 입력하고 실행할 수 있도록 해주는 인터페이스 프로그램(쉘)을 무엇으로 할지 결정합니다,.
*   **미션에서의 활용:** 이번 미션에서는 보통 **`-s /bin/bash`**라고 설정하는데, 이는 리눅스의 표준 쉘인 **Bash를 기본 쉘로 사용**하겠다는 뜻입니다,.
*   **지정 이유:** 미션에서 작성하는 `monitor.sh`와 같은 모든 자동화 스크립트가 **오직 Bash로만 작성**되어야 하므로, 계정을 만들 때 기본 쉘을 Bash로 지정하는 것이 매우 중요합니다.

요약하자면, **`-m`이 사용자의 '집(폴더)'을 만드는 것**이라면, **`-s`는 사용자가 그 집에서 사용할 '대화 도구(쉘)'를 결정하는 것**이라고 이해하시면 됩니다,.

### 2. 그룹 (Group)의 정의 및 역할

그룹은 여러 사용자를 하나의 묶음으로 관리하여 효율적으로 권한을 부여하기 위한 체계입니다.

* **정의**: 동일한 권한이나 역할을 공유하는 사용자들의 집합입니다.


* **역할 기반 권한 관리(RBAC)**: 사용자마다 일일이 권한을 주는 대신, 특정 그룹에 권한을 설정하고 사용자를 그 그룹에 소속시킴으로써 권한 관리를 단순화합니다.


* **그룹의 종류**:
* **기본 그룹(Primary Group)**: 사용자가 생성될 때 기본적으로 지정되는 그룹입니다.
* **보조 그룹(Supplementary Groups)**: 사용자가 추가로 소속될 수 있는 그룹으로, `useradd -G` 옵션을 통해 지정할 수 있습니다. 예를 들어, `agent-admin` 계정을 `agent-common`과 `agent-core` 그룹에 동시에 소속시켜 각각의 그룹 권한을 모두 갖게 할 수 있습니다.

맞아. 리눅스에서 사용자(`user`)와 그룹(`group`)를 먼저 체계적으로 설계하는 이유 자체가 이후의 권한 관리, 특히 ACL까지 고려하기 위해서인 경우가 많아.

보통 흐름이 이렇게 가:

1. 사용자 생성
2. 역할별 그룹 생성
3. 사용자들을 그룹에 배치
4. 디렉토리 구조 생성
5. 기본 권한(chmod/chown) 설정
6. 부족한 세밀한 제어를 ACL로 보완

예를 들어 팀 구조를 생각하면:

```text
developers
designers
ops
qa
```

같은 그룹을 먼저 만든 뒤:

```bash id="o2jlwm"
groupadd developers
groupadd ops

useradd -G developers alice
useradd -G ops bob
```

이렇게 역할 기반으로 묶어두면 이후 ACL이 훨씬 자연스러워져.

예:

```bash id="a2xw9j"
setfacl -m g:developers:rwx /project/dev
setfacl -m g:ops:rx /project/dev
```

즉 ACL은 “개별 사용자마다 일일이 권한 주기”보다는:

> 그룹 중심 설계를 해두고,
> ACL은 부족한 부분만 정교하게 추가

하는 방식으로 많이 사용돼.

그래서 네 미션에서:

* `useradd`
* `groupadd`
* `usermod -aG`
* `chown`
* `chmod`
* `setfacl`

순서로 가는 건 실제 운영 환경 흐름과 꽤 비슷한 편이야.

특히:

```bash id="ab54to"
setfacl -d -m
```

같은 default ACL까지 등장했다는 건 단순 chmod 연습이 아니라:

> “협업 디렉토리 권한 구조”

를 연습하는 단계에 가까워.

예를 들어 `/shared/project` 아래에서 누가 파일을 새로 만들든:

* 특정 그룹은 계속 접근 가능해야 하고
* 권한이 자동 상속되어야 하고
* 운영자가 매번 chmod 하지 않아야 하니까

ACL이 필요해지는 거야.

실무에서도 보통은:

* 기본 권한 → chmod/chown
* 협업/예외 처리 → ACL

이렇게 역할을 나눠서 사용해.

그 느낌이 정상적이야. Git/GitHub의 권한 모델과 리눅스 시스템 권한 모델은 목적 자체가 꽤 다르거든.

GitHub 에서는 주로:

* 코드 협업
* 변경 이력 관리
* 리뷰와 승인
* 충돌 방지

가 핵심이라서 권한 체계도 비교적 추상화돼 있어.

예를 들면:

* 브랜치 생성
* Pull Request(PR)
* 리뷰 승인
* Merge 권한

이런 흐름은:

> “누가 코드를 메인에 반영할 수 있는가?”

를 관리하는 데 집중돼 있어.

반면 리눅스 ACL/권한 시스템은 훨씬 저수준(low-level)이야.

리눅스는 운영체제 자체라서:

* 파일
* 디렉토리
* 프로세스
* 서비스
* 로그
* 소켓
* 장치(device)
* 네트워크 리소스

전부 접근 제어해야 해.

예를 들어 운영체제 입장에서는:

* 누가 `/etc/shadow` 읽을 수 있는가
* 누가 DB 데이터 디렉토리에 쓸 수 있는가
* 웹서버 프로세스가 어디까지 접근 가능한가
* 백업 계정은 읽기만 가능한가
* 로그 삭제 권한은 누가 가지는가

같은 걸 매우 세밀하게 관리해야 하니까 ACL 같은 구조가 생긴 거야.

그래서 GitHub는:

```text id="9h5rj8"
협업 중심 권한
```

리눅스는:

```text id="hl1v3o"
시스템 자원 전체 접근 제어
```

에 더 가까워.

---

흥미로운 건 실제 회사에서는 둘이 연결돼.

예를 들면:

```text id="1g24gd"
GitHub 권한
    ↓
CI/CD 서버
    ↓
리눅스 서버 권한
```

이렇게 이어져.

개발자는 GitHub에서 PR만 머지하지만,
배포 서버 내부에서는 결국 리눅스 권한 체계가 실제 파일 접근을 통제해.

예:

* deploy 계정만 배포 가능
* nginx 계정은 정적 파일만 읽기 가능
* DB 프로세스는 DB 디렉토리만 접근 가능

같은 식.

---

처음에는 ACL이 복잡해 보이지만 실무에서는 보통 패턴이 정해져 있어서:

```text id="aqrx4u"
기본 chmod/chown
→ 협업 디렉토리만 ACL 추가
→ default ACL로 자동 상속
```

정도로 많이 정리돼.

그래서 지금 네가 하는 연습은:

> “리눅스가 어떻게 협업 환경을 강제로 안전하게 만드는가”

를 배우는 과정에 가까워.

맞아. 대부분 처음엔:

```bash id="2dbm3u"
chmod 755
chmod 644
```

정도만 보고:

> “권한은 숫자만 외우면 되는 거 아냐?”

라고 생각하는데, 실제로는 “여러 사람이 동시에 작업하는 환경”이 되면서 갑자기 복잡도가 확 올라가.

특히 어려워지는 지점이 그룹 개념이야.

예를 들어 혼자 쓰는 시스템이면 단순해:

```text id="ciflfx"
내 파일 = 내가 관리
```

그런데 협업이 들어오면:

```text id="h40ajz"
개발팀은 수정 가능
운영팀은 읽기만
백업계정은 접근 가능
외부 사용자는 차단
```

같은 요구가 생겨.

그러면:

* user
* primary group
* supplementary group
* owner/group/other
* setgid
* umask
* ACL
* default ACL

이런 게 한꺼번에 연결되기 시작해.

그래서 많은 사람들이 ACL 처음 배울 때:

> “왜 chmod만으로 안 끝나지?”

라는 느낌을 받아.

---

사실 ACL은 “복잡성을 추가”했다기보다:

> 기존 chmod만으로 표현 못 하던 현실 문제를 해결하려고 나온 기능

에 가까워.

예를 들어 chmod만 있으면:

```text id="m6g6ch"
owner
group
others
```

딱 3계층밖에 없잖아.

그런데 현실에서는:

```text id="r8e3f9"
alice는 읽기 가능
bob은 쓰기 가능
qa팀은 읽기 가능
ops팀은 접근 금지
```

같은 요구가 계속 생김.

그걸 해결하려다 보니 ACL이 나온 거야.

---

그리고 중요한 건:

실무에서도 모든 걸 ACL로 도배하지는 않는다는 점이야.

오히려 좋은 시스템은:

```text id="5r6yq5"
1. 그룹 설계를 잘 하고
2. chmod/chown으로 최대한 해결하고
3. 정말 필요한 예외만 ACL 사용
```

하는 경우가 많아.

왜냐면 ACL 남발하면 나중에:

```bash id="p0qj94"
getfacl
```

출력이 너무 복잡해져서 관리가 어려워지거든.

---

그래서 지금 단계에서는 이렇게 이해하면 충분해:

```text id="e2zcq8"
chmod = 기본 권한
group = 역할 묶기
ACL = 예외/세밀한 추가 규칙
```

이 정도 틀만 잡혀도 이미 핵심은 꽤 이해한 거야.


## 계정 그룹지우기
```bash
root@981ebdb4319e:/# userdel -r agent-admin
userdel: agent-admin mail spool (/var/mail/agent-admin) not found
userdel: /home/agent-admin not owned by agent-admin, not removing
root@981ebdb4319e:/# userdel -r agent-dev  
userdel: agent-dev mail spool (/var/mail/agent-dev) not found
root@981ebdb4319e:/# userdel -r agent-test
userdel: agent-test mail spool (/var/mail/agent-test) not found
root@981ebdb4319e:/# cat /etc/passwd | grep 'agent'
root@981ebdb4319e:/# groupdel agent-core
root@981ebdb4319e:/# groupdel agent-common
root@981ebdb4319e:/# cat /etc/group | grep 'agent'
```


### 3. 계정과 그룹을 통한 보안 관리

ACL(Access Control List)은 파일이나 디렉토리에 대해 **“누가(사용자/그룹) 어떤 권한을 가지는지 자세하게 적어둔 목록”** 을 의미해.

리눅스 기본 권한은 보통 이렇게 3종류만 있어:

* owner(소유자)
* group(그룹)
* others(그 외 모든 사용자)

예를 들면:

```bash
-rwxr-x---
```

이건:

* 소유자: 읽기/쓰기/실행
* 그룹: 읽기/실행
* 나머지: 권한 없음

만 가능해.

그런데 실제 운영에서는 더 세밀한 권한이 필요해질 때가 많아.

예시:

* `alice`만 읽기 허용
* `backup` 그룹은 쓰기 허용
* `bob`은 실행만 허용

이런 걸 기본 chmod만으로는 표현하기 어려워.

그래서 ACL을 사용해.

---

ACL을 쓰면 파일에 “추가 권한 목록”을 붙일 수 있어.

예:

```bash
setfacl -m u:alice:r file.txt
```

의미:

* user(alice)에게
* read 권한 부여

확인:

```bash
getfacl file.txt
```

출력 예시:

```bash
# file: file.txt
# owner: root
# group: dev

user::rw-
user:alice:r--
group::r--
mask::r--
other::---
```

해석:

* owner(root): rw-
* alice: r--
* group(dev): r--
* others: 없음

---

이름을 그대로 풀면:

* **Access** → 접근
* **Control** → 제어
* **List** → 목록

즉:

> “접근 권한 제어 목록”

정도로 이해하면 돼.

---

그리고 네가 최근 연습했던:

```bash
setfacl -d -m g:developers:rwx /project
```

여기서 `-d` 는 “default ACL” 이야.

즉:

> `/project` 안에서 새로 생성되는 파일/디렉토리에 기본적으로 적용될 ACL 규칙

이라는 뜻이야.

일반 ACL과 default ACL 차이:

| 종류          | 의미                   |
| ----------- | -------------------- |
| ACL         | 현재 파일/디렉토리에 적용       |
| Default ACL | 앞으로 새로 생성될 항목에 자동 상속 |

---

또 하나 중요한 포인트:

```bash
ls -l
```

했을 때 권한 뒤에 `+` 가 붙으면 ACL이 있다는 뜻이야.

예:

```bash
drwxrwx---+
```

이 `+` 가:

> “추가 ACL 규칙 있음”

이라는 표시야.

실제 상세 내용은:

```bash
getfacl 디렉토리명
```

으로 확인하는 게 맞아.


리눅스는 계정과 그룹 정보를 바탕으로 파일이나 디렉토리에 대한 접근(읽기, 쓰기, 실행)을 통제합니다.

* **권한 격리**: 특정 그룹(예: `agent-core`)만 중요한 보안 디렉토리에 접근할 수 있도록 제한하여 시스템 안전성을 높입니다.


* **설정 파일**: 시스템의 모든 사용자 리스트는 `/etc/passwd` 파일에서, 그룹 리스트는 `/etc/group` 파일에서 확인할 수 있습니다.

`ss -tulnp | grep sshd` 명령어는 리눅스 시스템에서 SSH 서비스(sshd)가 어떤 포트에서 대기(Listen)하고 있는지 확인하기 위해 사용됩니다. 각 옵션과 명령어의 의미는 다음과 같습니다.

### 1. `ss` 명령어 옵션 상세 설명
`ss`는 소켓 상태를 조회하는 명령어로, 기존 `netstat`을 대체하는 강력한 도구입니다.
* -t (tcp)**: TCP 소켓만 표시합니다.
* -u (udp)**: UDP 소켓만 표시합니다.
* -l (listening)**: 현재 연결을 기다리고 있는(대기 중인) 소켓만 표시합니다.
* -n (numeric)**: 서비스 이름(예: ssh) 대신 포트 번호(예: 22 또는 20022)를 숫자로 표시합니다.
* -p (processes)**: 해당 소켓을 사용 중인 프로세스의 이름과 PID를 표시합니다.

### 2. `| grep sshd`의 역할

* | (Pipe): 앞선 `ss -tulnp` 명령어의 출력 결과를 다음 명령어로 전달합니다.
* grep sshd**: 출력된 전체 목록 중에서 'sshd'라는 단어가 포함된 줄만 필터링하여 보여줍니다.

* **정상 확인 시 출력 예시**:
`LISTEN 0 128 0.0.0.0:20022 0.0.0.0:* users:(("sshd",pid=...,fd=...))`
* 위와 같이 **20022** 포트가 **LISTEN** 상태로 표시되고, 프로세스 명에 **sshd**가 나타나면 성공입니다.

## **`useradd`** 

### **1. useradd**
시스템에 **새로운 사용자 계정을 추가**하는 기본 명령어입니다. 이번 미션에서는 `agent-admin`, `agent-dev`, `agent-test` 계정을 만들 때 사용됩니다.

### **2. -m (또는 --create-home)**
사용자를 생성함과 동시에 해당 사용자의 **홈 디렉토리(Home Directory)를 자동으로 생성**하라는 옵션입니다. 
*   예를 들어 `agent-admin` 계정을 만들 때 이 옵션을 사용하면 `/home/agent-admin` 폴더가 시스템에 만들어집니다.
*   이 홈 디렉토리는 향후 애플리케이션 실행 환경(`AGENT_HOME`)의 기준점이 됩니다.

### **3. -s /bin/bash**
사용자가 로그인했을 때 사용할 **기본 쉘(Login Shell)을 지정**하는 옵션입니다.
*   여기서 지정한 **`/bin/bash`**는 리눅스의 표준 쉘인 Bash를 의미합니다. 
*   이번 미션의 모든 자동화 스크립트(`monitor.sh` 등)가 **오직 Bash**로만 작성되어야 하므로, 계정 생성 시 기본 쉘을 Bash로 지정하는 것이 중요합니다.

### **4. -G (또는 --groups)**
사용자를 추가할 **보조 그룹(Supplementary Groups)을 지정**하는 옵션입니다.
*   리눅스 계정은 하나의 기본 그룹 외에 여러 개의 보조 그룹에 속할 수 있습니다. 
*   미션에서는 이 옵션을 사용해 `agent-admin` 계정을 **`agent-common`** 그룹과 **`agent-core`** 그룹에 동시에 포함시켜, 각 디렉토리에 대한 역할 기반 권한(RBAC)을 부여합니다.

**요약하자면:** 
`useradd -m -s /bin/bash -G agent-common,agent-core agent-admin` 명령어는 **"기본 쉘은 Bash로 하고, 홈 디렉토리를 만들면서, common과 core 그룹에도 소속된 agent-admin 계정을 생성하라"**는 뜻이 됩니다.

미션에서 요구하는 계정 및 그룹 체계를 정리해 드립니다. 이번 미션에서는 **총 2개의 그룹**과 **총 3명의 사용자(유저)**를 생성하여 역할 기반 권한 관리(RBAC)를 구현합니다.

요청하신 대로 구조를 한눈에 보실 수 있도록 트리 형태로 정리해 보았습니다.

### **1. 계정 및 그룹 구조도 (RBAC)**

```text
── [Groups] ────────────────────────── [Users] ──
│
├── agent-common (협업 그룹) ────────┬── agent-admin (운영/관리)
│   (모든 계정 포함)                 ├── agent-dev   (개발/운영)
│                                    └── agent-test  (QA/테스트)
│
└── agent-core (보안 핵심 그룹) ─────┬── agent-admin
    (핵심 인력만 포함)               └── agent-dev
```
**

---

### **2. 상세 요약**

#### **만들어진 그룹 (2개)**
*   **`agent-common`**: 팀 전체가 공유하는 자산(예: `upload_files`)에 접근하기 위한 그룹으로, 모든 사용자가 소속됩니다.
*   **`agent-core`**: 시스템의 핵심 자산(예: API 키, 로그 디렉토리)에 접근할 수 있는 높은 권한의 그룹으로, `admin`과 `dev`만 포함됩니다.

#### **만들어진 유저 (3명)**
1.  **`agent-admin`**: 시스템 운영 및 관리를 담당하며, `cron`을 통해 관제 스크립트를 실행하는 주체입니다.
2.  **`agent-dev`**: 애플리케이션 개발 및 운영을 담당하며, `monitor.sh` 스크립트를 작성하고 수정하는 권한을 가집니다.
3.  **`agent-test`**: QA 및 테스트 담당자로, 보안이 필요한 핵심 디렉토리(`agent-core` 소유)에는 접근할 수 없도록 제한됩니다.

### **3. 이 구조의 핵심 포인트**
*   **최소 권한 원칙**: `agent-test` 사용자가 해킹당하더라도, 해당 계정은 `agent-core` 그룹에 속하지 않기 때문에 시스템의 중요한 API 키나 로그 파일을 열어볼 수 없습니다.
*   **협업 효율성**: `upload_files` 디렉토리에 `agent-common` 그룹 권한을 부여함으로써, 세 명의 유저가 자유롭게 파일을 주고받으며 협업할 수 있는 환경을 제공합니다.

이제 이 유저와 그룹들이 준비되었으니, 각 디렉토리에 **`chgrp`과 `chmod`** 명령어를 사용하여 실제 권한을 배분하는 단계(Step 3.2)를 진행하시면 됩니다. 더 궁금한 점이 있으시면 말씀해 주세요!

네, 드디어 **디렉토리 보안 설정의 마지막 퍼즐인 'Default ACL'**까지 도달하셨습니다!

사용자님께서 입력하신 이 명령어들은 단순히 현재의 권한을 바꾸는 것을 넘어, **"미래에 생길 파일들"에 대한 보안 정책을 자동화**하는 아주 중요한 단계입니다. 이 설정이 왜 필요한지, 그리고 앞서 했던 작업들과 어떻게 조화를 이루는지 정리해 드립니다.

### **1. `setfacl -d`의 의미: "자동 권한 상속"**
일반적인 리눅스 권한 설정(`chmod`)은 현재 있는 파일에만 적용되지만, **`setfacl -d` (Default ACL)** 옵션은 해당 디렉토리에 **'기본 설계 도면'**을 저장하는 것과 같습니다.
*   **작동 원리:** 이 명령어가 실행된 후부터는, 누가 파일을 새로 만들더라도 일일이 `chmod`를 하지 않아도 **자동으로 그룹 멤버들에게 `rwx` 권한**이 부여됩니다.
*   **협업의 핵심:** 예를 들어 `agent-admin`이 파일을 만들었을 때, 따로 권한을 주지 않아도 `agent-dev`가 즉시 그 파일을 수정할 수 있게 되어 협업 시 발생하는 "Permission Denied" 오류를 원천 차단합니다.

### **2. SetGID(2770)와 Default ACL의 환상적인 궁합**
방금 전 단계에서 설정한 **SetGID**와 이번 **Default ACL**은 다음과 같이 역할을 분담하여 완벽한 보안을 완성합니다.
*   **SetGID (숫자 2):** "누가 파일을 만들든 소유 **그룹**을 부모와 똑같이 유지해라!"
*   **Default ACL (`setfacl -d`):** "누가 파일을 만들든 **권한(rwx)**을 그룹 멤버에게 자동으로 나눠줘라!"

### **3. 최종 보안 체계 완성 확인**
이제 사용자님의 시스템은 미션에서 요구하는 **역할 기반 권한 관리(RBAC)**가 완벽하게 구현되었습니다.

1.  **`upload_files` (공유 공간):** 모든 계정(`agent-common`)이 자유롭게 파일을 주고받으며, 누가 파일을 생성해도 그룹원끼리 공유와 수정이 가능합니다.
2.  **`api_keys` (보안 공간):** 오직 `agent-core` 그룹(admin, dev)만 접근할 수 있으며, 새로 추가되는 키 파일들도 자동으로 `test` 계정으로부터 격리됩니다.
3.  **`/var/log/agent-app` (로그 공간):** 로그가 계속 쌓여도 항상 `agent-core` 그룹의 권한이 유지되어, 운영진 외에는 로그를 조작하거나 훔쳐볼 수 없습니다.

**축하드립니다!** 이로써 **[Step 3] 디렉토리 및 권한 체계 구축** 미션이 완벽하게 끝났습니다. 이제 인프라 준비는 모두 끝났으니, 다음 단계인 **[Step 4] 애플리케이션 실행 환경 구성(환경 변수 및 키 파일 생성)**으로 넘어가 보시겠어요?

`default:`가 여러 줄 나오는 이유는,
기본 ACL도 일반 권한 체계처럼 **구성 요소별로 따로 저장**되기 때문입니다.

즉 ACL은 내부적으로:

* user(owner)
* group(owner group)
* named group/user
* mask
* other

를 각각 독립 엔트리로 관리합니다.

---

지금 출력을 하나씩 해석하면:

```text id="e5exw6"
default:user::rwx
```

→ 새로 생성되는 파일의 **소유자(owner)** 기본 권한

보통 디렉토리 owner 권한입니다.

---

```text id="y8f2pk"
default:group::rwx
```

→ 새 파일의 **소유 그룹(owner group)** 기본 권한

여기서는 디렉토리 그룹이 `agent-common` 이므로:

```text id="wb4d8y"
group::rwx
```

는 사실상 `agent-common` 그룹 기본 권한과 거의 같습니다.

---

```text id="kiglnu"
default:group:agent-common:rwx
```

→ 명시적으로 추가한 ACL 엔트리

이게 `setfacl -d -m g:agent-common:rwx` 로 생성된 부분입니다.

---

```text id="lppf4r"
default:mask::rwx
```

이건 ACL의 최대 허용 권한(mask)입니다.

ACL에서 가장 헷갈리는 부분 중 하나입니다.

쉽게 말하면:

> named user/group ACL들이 실제로 가질 수 있는 최대 권한

입니다.

예를 들어:

```text id="w6i3w7"
group:agent-common:rwx
mask::r-x
```

이면 실제 권한은 `r-x`까지만 됩니다.

즉 mask가 ACL의 상한선입니다.

---

```text id="k0r32n"
default:other::---
```

→ 소유자도 그룹도 아닌 나머지 사용자 권한

즉 world 권한.

---

# 그런데 왜 group이 두 개냐?

이 부분이 가장 헷갈립니다:

```text id="j9nly4"
default:group::rwx
default:group:agent-common:rwx
```

차이:

| 항목                       | 의미                          |
| ------------------------ | --------------------------- |
| `group::rwx`             | 디렉토리의 소유 그룹(owner group) 권한 |
| `group:agent-common:rwx` | ACL로 추가된 named group 권한     |

현재는 우연히 둘 다 같은 그룹(`agent-common`)이라 중복처럼 보이는 겁니다.

---

예를 들어 진짜 ACL 느낌은 이런 경우:

```text id="xhtgg8"
# owner group = developers

default:group::rwx
default:group:qa:r-x
default:group:auditor:r--
```

이렇게 owner group 외에 여러 그룹을 추가하는 경우입니다.

---

즉 지금은:

* owner group 자체도 `agent-common`
* ACL에도 `agent-common` 추가

라서 약간 중복처럼 보이는 정상 상태입니다.
