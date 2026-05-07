네, 저 작업들도 `Dockerfile` 안으로 상당 부분 자동화할 수 있습니다.

다만 중요한 점:

> `EXPOSE`는 방화벽 설정이 아닙니다.

입니다.

---

지금 정리하면 역할이 이렇게 나뉩니다:

| 작업             | 위치             |
| -------------- | -------------- |
| ssh 설치         | Dockerfile     |
| sshd_config 수정 | Dockerfile     |
| 포트 선언(EXPOSE)  | Dockerfile     |
| ssh 서비스 실행     | ENTRYPOINT/CMD |
| 실제 포트 포워딩      | docker run -p  |
| UFW 방화벽        | 컨테이너 내부 또는 호스트 |

---

그리고 Docker에서는 보통:

```text id="8htrw0"
호스트 방화벽
+ docker -p 포트포워딩
```

만 쓰는 경우가 많고,

컨테이너 내부에서 `ufw`까지 돌리는 경우는 상대적으로 드뭅니다.

왜냐하면 Docker 자체가 네트워크 격리를 이미 어느 정도 하기 때문입니다.

---

하지만 미션 요구사항 때문에 UFW까지 해야 한다면 가능합니다.

예시 Dockerfile:

```dockerfile id="dockerfile_inline_comment"
FROM ubuntu:22.04                          # Ubuntu 22.04 이미지를 베이스로 사용

ENV DEBIAN_FRONTEND=noninteractive         # apt 설치 시 사용자 입력 없이 자동 진행

RUN apt update && apt install -y \         # 패키지 목록 업데이트 후 필요한 패키지 설치
    openssh-server \                       # SSH 서버 설치
    ufw \                                  # UFW 방화벽 설치
    vim gcc python3                        # vim, gcc, python3 설치

RUN mkdir /var/run/sshd                    # SSH 실행에 필요한 디렉토리 생성

RUN sed -i 's/#Port 22/Port 20022/' /etc/ssh/sshd_config
                                            # SSH 기본 포트 22 → 20022로 변경

RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config
                                            # root 로그인 금지 설정

RUN ufw default deny incoming              # 들어오는 연결 기본 차단

RUN ufw default allow outgoing             # 나가는 연결 기본 허용

RUN ufw allow 20022/tcp                    # SSH 포트 20022 허용

RUN ufw allow 15034/tcp                    # 앱 포트 15034 허용

EXPOSE 20022                               # 컨테이너가 20022 포트 사용함을 명시

EXPOSE 15034                               # 컨테이너가 15034 포트 사용함을 명시

CMD service ssh start && bash              # 컨테이너 시작 시 SSH 실행 후 bash 유지
```

```

실행:

```bash id="4b3sqa"
docker build -t mission-box .
docker run -it --privileged \
  -p 20022:20022 \
  -p 15034:15034 \
  mission-box
```

---

근데 여기서 핵심 함정이 하나 있습니다.

`ufw enable`은 컨테이너 안에서 종종 문제를 일으킵니다.

이유:

* UFW는 내부적으로 iptables 만짐
* Docker도 iptables 만짐
* 충돌 가능
* 권한 제한 이슈 존재

그래서 대부분:

```text id="xpd8xz"
Docker 컨테이너 내부에서는 UFW 잘 안 씀
```

입니다.

---

실무적으로는 보통:

```text id="df4f7w"
호스트(Ubuntu 서버)
 └─ UFW 관리

Docker
 └─ 필요한 포트만 -p
```

구조를 많이 씁니다.

예:

호스트에서:

```bash id="m2o5o0"
ufw allow 20022/tcp
ufw allow 15034/tcp
```

그리고 Docker는:

```bash id="8okjlwm"
docker run -p 20022:20022 -p 15034:15034 ...
```

만.

---

즉 지금 미션이라면:

* 학습 목적 → 컨테이너 내부 UFW 가능
* 실제 운영 → 보통 호스트 방화벽 사용

으로 이해하면 됩니다.
