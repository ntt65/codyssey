=# Codyssey_rookieQ1 — 개발 워크스테이션 미션

---

## 1. 프로젝트 개요 (미션 목표 요약)

- **환경 세팅이 개발의 시작:** 리눅스 CLI, Docker(컨테이너), Git/GitHub(버전 관리·협업)을 함께 사용해 재현 가능한 실행 환경을 만듭니다.
- **이번 저장소에서 한 일:** 작업 디렉터리·권한 정리 → Docker 설치·점검 및 컨테이너 운영 → **기존 `nginx` 베이스** 위에 정적 웹을 올린 **커스텀 이미지** 빌드 → **포트 매핑**으로 호스트에서 접속 확인 → **바인드 마운트**(호스트 변경 반영)와 **Docker 볼륨**(컨테이너 삭제 후에도 데이터 유지) 검증 → Git 설정 및 GitHub 연동.
- **구조적 관점:** 이미지와 컨테이너 분리, 격리된 네트워크에서 **포트·스토리지 연결**이 필요한 이유를 로그와 함께 설명합니다.

---

## 2. 실행 환경

| 항목 | 내용 |
|------|------|
| OS | macOS (Darwin)|
| Shell / 터미널 | zsh, macOS 터미널(또는 VS Code 통합 터미널) |
| Docker | `Docker version 29.2.1` (클라이언트·서버는 `docker info`로 동일 계열 확인) |
| Git | `git version 2.50.1`|

---

## 3. 수행 항목 체크리스트

- [x] 터미널: 현재 위치, 목록(숨김 포함), 이동, 생성, 복사, 이름 변경/이동, 삭제, 내용 확인, 빈 파일 생성
- [x] 권한: 파일 1개·디렉터리 1개에 대해 변경 전/후 비교
- [x] Docker 설치·점검: `docker --version`, `docker info`(또는 동등 점검)
- [x] Docker 운영: `docker images`, `docker ps` / `docker ps -a`, `docker logs`, `docker stats`(또는 `docker top`)
- [x] `hello-world` 실행 성공
- [x] `ubuntu` 컨테이너 내부에서 `ls`, `echo` 등
- [x] 컨테이너 유지/종료: `attach` vs `exec` 관찰 및 정리
- [x] 기존 Dockerfile 베이스로 커스텀 이미지 (NGINX + 정적 `index.html`)
- [x] 포트 매핑 접속 검증 (호스트 포트 2개 예시 포함)
- [x] 바인드 마운트: 호스트 변경 전/후 컨테이너에서 내용 비교
- [x] Docker 볼륨: 생성·연결·컨테이너 삭제 후 재부착 시 데이터 유지
- [x] Git 사용자 정보·기본 브랜치 설정 및 `git config --list` 기록(민감값 마스킹)
- [x] GitHub 원격 저장소 연동(아래 로그·저장소 URL). VS Code에서 GitHub 로그인·연동 완료(스크린샷은 제출 시 `docs/` 등에 두고 여기 링크를 추가하면 됨)

---

## 4. 검증 방법 (명령 → 확인 내용) 및 결과 위치

| 확인 목적 | 예시 명령 | 결과 위치 |
|-----------|-----------|-----------|
| 터미널 기본기 | `pwd`, `ls -la`, `mkdir`, `touch`, `mv`, `cat` | [logs/terminal.md](logs/terminal.md) |
| 권한 | `ls -l`, `chmod 755`, `chmod 644` | 동일 |
| Docker 버전·데몬 | `docker --version`, `docker info` | [logs/docker.md](logs/docker.md) §1 |
| 이미지·컨테이너 | `docker images`, `docker ps`, `docker ps -a`, `docker logs <id>` | [logs/docker.md](logs/docker.md) §2–3 |
| hello-world | `docker run --rm hello-world` | [logs/docker.md](logs/docker.md) §2–3 |
| ubuntu 셸 | `docker run -it ubuntu bash` 후 `ls`, `echo` | [logs/docker.md](logs/docker.md) §3 |
| 커스텀 웹 이미지 | `docker build -t my-webserver:1.0 my_webserver` | [logs/docker_web.md](logs/docker_web.md) |
| 포트 매핑 | `docker run -d -p 8080:80 --name web-test1 my-webserver:1.0` 후 `curl` | 아래 §7.7 및 [logs/docker_web.md](logs/docker_web.md) |
| 바인드 마운트 | `-v ~:/app/data` 후 호스트에서 파일 수정 → 컨테이너에서 `cat` | [logs/docker.md](logs/docker.md) §5 |
| 볼륨 영속성 | `docker volume create`, 컨테이너 삭제 후 새 컨테이너에 동일 볼륨 마운트 | [logs/docker.md](logs/docker.md) §4 |

브라우저 접속 증거:

```bash
curl -s http://localhost:8080
```

logs/home.png

두 번째 포트(예: `8081`)는 아래와 같이 별도 컨테이너로 띄워 동일 이미지가 **여러 호스트 포트**에서 재현됨을 보입니다.

```bash
docker run -d -p 8081:80 --name web-test2 my-webserver:1.0
curl -s http://localhost:8081
```

---

## 5. 트러블슈팅 (2건 이상)

### 5.1 `docker create my-vol` 로 볼륨을 만들려다 실패

- **문제:** `Unable to find image 'my-vol:latest' locally` — 볼륨 이름을 이미지 이름으로 해석함.
- **원인 가설:** `docker create`는 기본적으로 **이미지로부터 컨테이너 생성**용이며, 볼륨 생성 명령이 아님.
- **확인:** 공식 도움말·에러 메시지에서 이미지 pull 시도로 동작함을 확인.
- **해결:** 명시적으로 `docker volume create my-vol` 사용. ([logs/docker.md](logs/docker.md) §4)

### 5.2 볼륨 마운트 경로를 상대경로로 줘서 실패

- **문제:** `-v my-vol:app/data` → `mount path must be absolute`.
- **원인 가설:** 컨테이너 쪽 마운트 포인트는 **절대 경로**여야 함.
- **확인:** 에러 메시지에 `invalid mount path` 표시.
- **해결:** `-v my-vol:/app/data`처럼 컨테이너 경로를 `/`로 시작하게 수정. ([logs/docker.md](logs/docker.md) §4)

### 5.3 디렉터리에 `chmod 644` 후 `ls`가 Permission denied

- **문제:** 디렉터리에 실행 비트가 없어 목록 조회가 막힘.
- **원인 가설:** 디렉터리의 `x`는 **내부 진입·목록 탐색**에 필요.
- **확인:** `ls -l practice` 전후 비교.
- **해결:** 디렉터리는 일반적으로 `755` 등으로 실행 비트 부여. ([logs/terminal.md](logs/terminal.md) §3)

---

## 6. 과제 목표와의 연결 (스스로 설명 가능한 요지)

- **절대 vs 상대 경로:** 절대 경로는 `/`부터 전체 경로, 상대 경로는 현재 디렉터리(`.`)·상위(`..`) 기준. Docker 볼륨 컨테이너 경로는 절대 경로가 필수인 이유와 맞물려 이해합니다.
- **rwx / 755·644:** `r=4, w=2, x=1`을 소유자·그룹·기타에 더해 한 자리 숫자로 표현. 디렉터리는 `x` 없으면 `ls`가 실패할 수 있음.
- **커스텀 이미지:** 공식 `nginx:stable-alpine` 위에 `index.html`과 `LABEL`/`ENV`/`EXPOSE`/`CMD`를 얹은 [my_webserver/Dockerfile](my_webserver/Dockerfile).
- **포트 매핑:** 컨테이너는 기본적으로 호스트와 네트워크가 분리되어 있어, **호스트:컨테이너**로 포트를 연결해야 브라우저·`curl`이 접근 가능.
- **Docker 볼륨:** 컨테이너 파일시스템과 별도로 Docker가 관리하는 저장소에 데이터를 두어 **컨테이너를 지워도** 데이터가 남음.
- **Git vs GitHub:** Git은 로컬 커밋·브랜치·히스토리, GitHub는 원격 저장·협업·PR 등의 플랫폼.

---

## 7. 수행 로그 (발췌, 코드 블록)

명령과 출력의 **전체 원문**은 `logs/*.md`를 참고합니다. 아래는 README에서 핵심만 인용합니다.

### 7.1 터미널 기본 조작

```bash
pwd
# /Users/hugeung/Documents/Codyssey/Codyssey1st_rookie

ls -la
# total 8
# drwxr-xr-x@  5 hugeung  staff  160 Apr  1 15:27 .
# drwxr-xr-x   7 hugeung  staff  224 Apr  1 15:25 ..
# drwxr-xr-x@ 13 hugeung  staff  416 Apr  1 15:25 .git
# ...

mkdir practice
cd practice
touch test.txt
cd ..
mv test.txt renamed.txt
```

### 7.2 권한 변경 전/후 (파일 1 + 디렉터리 1)

```bash
ls -l renamed.txt
# -rw-r--r--@ 1 hugeung staff 0 Apr  1 15:29 renamed.txt

chmod 755 renamed.txt
ls -l renamed.txt
# -rwxr-xr-x@ 1 hugeung staff 0 Apr  1 15:29 renamed.txt

chmod 644 practice
ls -l practice
# ls: fts_read: Permission denied.

chmod 755 practice
ls -l practice
# total 0
```

### 7.3 Docker 설치·점검

```bash
docker --version
# Docker version 29.2.1, build a5c7197

docker info
# (출력 발췌) Server Version: 29.2.1, Storage Driver: overlayfs, ...
```

### 7.4 이미지·컨테이너·로그

```bash
docker images
# REPOSITORY    TAG       IMAGE ID       SIZE
# hello-world   latest    85404b3c5395   ...
# ubuntu        latest    186072bba1b2   ...

docker ps -a
# CONTAINER ID   IMAGE     COMMAND   CREATED         STATUS
# ab0839e389dc   ubuntu    "bash"    4 minutes ago   Exited (0)
# 8defa3a2e456   hello-world "/hello" 5 minutes ago   Exited (0)

docker logs 8defa3a2e456
# Hello from Docker!
# This message shows that your installation appears to be working correctly.
```

### 7.5 `hello-world` 및 `ubuntu` 내부

```bash
docker run --rm hello-world
# (이미지 pull 및 Hello from Docker! 메시지)

docker run -it ubuntu bash
# root@container:/# ls
# bin boot dev etc home lib ...
# root@container:/# echo "inside"
# inside
```

### 7.6 `attach` vs `exec` (관찰 요약)

- **`docker exec`:** 이미 떠 있는 컨테이너에 **새 프로세스(셸)**를 붙임. `exit`해도 컨테이너의 메인 프로세스는 유지되는 경우가 많음.
- **`docker attach`:** 컨테이너의 **주 프로세스 stdin/stdout/stderr**에 터미널을 연결. 인터랙티브 셸이 PID 1이면 `exit` 시 **컨테이너가 종료**될 수 있음.

로그 예: [logs/docker.md](logs/docker.md) §3.

### 7.7 Dockerfile 커스텀 이미지 (베이스·포인트·빌드)

**선택한 기존 베이스:** 공식 이미지 **`nginx:stable-alpine`** (경량 NGINX).

**커스텀 포인트와 목적:**

| 요소 | 목적 |
|------|------|
| `RUN rm ... html/*` | 기본 welcome 페이지 제거 후 우리 정적 파일만 제공 |
| `COPY index.html` | 미션용 간단 HTML을 기본 문서 루트에 배치 |
| `LABEL` | 이미지 식별·출처 메타데이터 |
| `ENV APP_NAME, APP_ENV, TZ` | 실행 환경 표시·타임존 일관성 |
| `EXPOSE 80` | 컨테이너 내부 리스닝 포트 문서화 |
| `CMD ["nginx", "-g", "daemon off;"]` | PID 1로 NGINX를 포그라운드 실행해 컨테이너 유지 |

```bash
cd my_webserver
docker build -t my-webserver:1.0 .
# => naming to docker.io/library/my-webserver:1.0
```

### 7.8 포트 매핑 (예: 8080) 및 응답 확인

```bash
docker run -d -p 8080:80 --name web-test1 my-webserver:1.0
# 2533ec825f4a07fd91983dd52404bb4cdf90a6982988146175c38245c7ab4c64

curl -s http://localhost:8080
# <!DOCTYPE html>
# <html>
# ...
# <h1>Hello World</h1>
```

**두 번째 호스트 포트(재현성):** `docker run -d -p 8081:80 --name web-test2 my-webserver:1.0` 후 `curl http://localhost:8081` (동일 본문 기대).

### 7.9 바인드 마운트 (호스트 변경 전/후)

```bash
echo "version1" > ~/msg.txt
docker run -it --name bind-demo -v ~/:/app/data ubuntu bash
# root@container:/# cat /app/data/msg.txt
# version1

# (호스트 다른 터미널에서)
echo "version2" > ~/msg.txt

# root@container:/# cat /app/data/msg.txt
# version2
```

### 7.10 Docker 볼륨 영속성 (삭제 전/후)

```bash
docker volume create my-vol
docker volume ls
# local     my-vol

docker run -it --name ubuntu1 -v my-vol:/app/data ubuntu bash
# echo hello > /app/data/test.txt
# cat /app/data/test.txt
# hello
# exit

docker rm ubuntu1
docker run -it --name ubuntu2 -v my-vol:/app/data ubuntu bash
# cat /app/data/test.txt
# hello
```

### 7.11 Git 설정 및 GitHub 연동

민감정보는 마스킹했습니다. 실제 로컬에서는 본인 이름·이메일이 설정되어 있습니다.

```bash

mpeg46551@c5r1s2 E1_1 % git config --global -l
user.name=mpegdj
user.email=mpeg4@ymail.com
init.defaultbranch=main

hugeung@gimdaeung-ui-MacBookAir Codyssey1st_rookie % git remote -v
origin  https://github.com/Daeung-03/Codyssey_rookieQ1.git (fetch)
origin  https://github.com/Daeung-03/Codyssey_rookieQ1.git (push)
```
연동
```bash
mpeg46551@c5r1s2 E1_1 % git remote -v
origin  https://github.com/mpegdj/E1_1.git (fetch)
origin  https://github.com/mpegdj/E1_1.git (push)
mpeg46551@c5r1s2 E1_1 % git log --oneline --graph

mpeg46551@c5r1s2 E1_1 % git log --oneline --graph --all
* db8eb00 (HEAD -> main, origin/main, origin/HEAD) ammend git and study file
```


---

## 8. 저장소 구조 (제출물)

