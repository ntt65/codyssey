
좋다. 이건 단순 과제가 아니라 **“DevOps 감각 + 개발 환경 구축 사고방식”**을 보는 과제야.
핵심은 *명령어 치는 것*이 아니라 → **“재현 가능한 환경 + 증거 + 설명”**이야.

---

# 🔍 1. 과제 구조 먼저 해석 (핵심만 뽑기)

이 과제는 크게 4덩어리야:

### ① 로컬 환경 기초 (CLI + 권한)

* 터미널 조작
* 파일/디렉토리
* 권한 (rwx, 755 등)

👉 “리눅스 기본기 확인”

---

### ② Docker 기초 + 운영

* docker 설치 확인
* 컨테이너 실행 (hello-world, ubuntu)
* logs / stats / ps 등

👉 “컨테이너를 다룰 수 있냐”

---

### ③ Docker 실전 (핵심)

* Dockerfile 작성
* 웹 서버 컨테이너 만들기
* 포트 매핑
* 바인드 마운트
* 볼륨 (영속성)

👉 **이게 핵심 평가 포인트**

---

### ④ Git + 문서화

* Git 설정
* GitHub 업로드
* README 작성 (가장 중요)

👉 **“남이 보고 따라할 수 있냐”**

---

# 🎯 2. 이 과제의 진짜 목표 (중요)

이걸 꼭 이해해야 방향 안 틀림

👉 단순 실행 ❌
👉 설명 가능 + 재현 가능 ⭕

즉:

* 왜 포트 매핑이 필요한지 설명 가능해야 함
* 왜 volume이 필요한지 설명 가능해야 함
* 왜 Docker 쓰는지 설명 가능해야 함

---

# 🧠 3. 전체 전략 (이대로 하면 됨)

## ✅ 전략 핵심

👉 “실행 → 캡처 → README 정리” 반복

---

# 🪜 4. 단계별 실행 계획 (실전용)

## 🔵 STEP 0 — 저장소 먼저 만들기

1. GitHub repo 생성
2. 로컬에서 clone
3. 폴더 구조 만들기

```bash
mkdir devops-mission
cd devops-mission
touch README.md
```

👉 이유:

* 모든 결과를 여기에 모아야 함

---

## 🔵 STEP 1 — 터미널 + 권한

할 것:

* pwd, ls -la
* mkdir, cp, mv, rm
* cat, touch
* chmod

👉 반드시:

✔ 명령어 + 결과 캡처
✔ 권한 변경 전/후 비교

---

## 🔵 STEP 2 — Docker 설치 확인

```bash
docker --version
docker info
```

OrbStack 쓰니까 여기서 막힐 가능성 있음 → 트러블슈팅 후보

---

## 🔵 STEP 3 — Docker 기본 실습

```bash
docker run hello-world
docker run -it ubuntu bash
```

안에서:

```bash
ls
echo hello
```

👉 여기서 관찰할 것:

* exit하면 종료됨
* detach vs attach 차이

---

## 🔵 STEP 4 — Docker 운영 명령

```bash
docker images
docker ps
docker ps -a
docker logs <컨테이너>
docker stats
```

👉 이건 그냥 다 찍어서 README 넣으면 됨

---

## 🔥 STEP 5 — 핵심: 웹 서버 만들기

### 방법 추천 (쉬운 루트)

👉 Nginx 기반 (강추)

### 폴더 구조

```
project/
 ├── Dockerfile
 └── site/
     └── index.html
```

### index.html

```html
<h1>Hello DevOps</h1>
```

### Dockerfile

```dockerfile
FROM nginx:alpine
COPY site/ /usr/share/nginx/html/
```

---

### 빌드 & 실행

```bash
docker build -t my-web .
docker run -d -p 8080:80 my-web
```

👉 브라우저 접속:

```
http://localhost:8080
```

📸 캡처 필수

---

## 🔥 STEP 6 — 포트 매핑 이해

👉 반드시 README에 설명:

* 컨테이너는 외부에서 접근 불가
* 그래서 포트 연결 필요

---

## 🔥 STEP 7 — 바인드 마운트

```bash
docker run -d -p 8080:80 \
-v $(pwd)/site:/usr/share/nginx/html \
nginx
```

👉 실험:

1. html 수정
2. 새로고침

👉 바로 반영됨 → 캡처

---

## 🔥 STEP 8 — 볼륨 (진짜 중요)

```bash
docker volume create mydata

docker run -it -v mydata:/data ubuntu bash
```

```bash
echo hello > /data/test.txt
exit
```

컨테이너 삭제 후 다시:

```bash
docker run -it -v mydata:/data ubuntu bash
cat /data/test.txt
```

👉 남아있으면 성공

---

## 🔵 STEP 9 — Git 설정

```bash
git config --global user.name "이름"
git config --global user.email "이메일"
git config --list
```

👉 캡처

---

## 🔵 STEP 10 — README 작성 (가장 중요)

구조는 이렇게 가면 됨:

```
1. 프로젝트 개요
2. 실행 환경
3. 수행 체크리스트
4. 터미널 로그
5. Docker 실습
6. Dockerfile 설명
7. 포트 매핑 설명
8. 마운트 vs 볼륨
9. 트러블슈팅
```

---

# ⚠️ 5. 자주 터지는 포인트 (미리 방지)

### 💥 Docker 안됨

→ OrbStack 실행 안함

---

### 💥 포트 접속 안됨

→ 포트 번호 틀림
→ 컨테이너 죽음

---

### 💥 권한 안바뀜

→ chmod 숫자 이해 못함

---

### 💥 README 빈약

→ 가장 많이 탈락하는 이유

---

# 🧩 6. 트러블슈팅 미리 준비 (2개 필요)

예시:

1. Docker 실행 안됨
2. 포트 접속 안됨
3. volume 데이터 안남음

---

# 🚀 7. 한줄 요약 전략

👉 **“모든 명령은 증거로 남기고, README에서 설명까지 한다”**

---

# 👉 다음 단계

원하면 바로:

* ✅ README 템플릿 만들어줄게 (붙여넣기용)
* ✅ Dockerfile + 전체 폴더 구조 완성해줄게
* ✅ 트러블슈팅 2개 같이 만들어줄게

어디부터 같이 할까?
