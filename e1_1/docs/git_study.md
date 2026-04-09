Docker와 리눅스 환경에서 개발을 시작하기 위한 **Git 풀 코스 설정 가이드**입니다. 전문가 수준으로 깔끔하게 정리해 드릴게요.

---

## 1. Git 설치 (Installation)
리눅스(Ubuntu/Debian 계열)에서는 패키지 관리자를 통해 간단히 설치합니다.

```bash
$ sudo apt update
$ sudo apt install git -y

# 설치 확인
$ git --version
```

---

## 2. 사용자 설정 (Configuration)
커밋 이력에 남을 이름과 이메일을 설정합니다. (최초 1회)

```bash
# 사용자 정보 설정
$ git config --global user.name "본인이름"
$ git config --global user.email "your_email@example.com"

# 설정 확인 (이전에 물어보신 명령어!)
$ git config --global --list
```

---

## 3. 로컬 저장소 초기화 (Init & Commit)
프로젝트 폴더를 만들고 Git 관리를 시작합니다.

```bash
# 1. 폴더 생성 및 이동
$ mkdir my-project && cd my-project

# 2. Git 초기화 (이때부터 .git 폴더가 생성됨)
$ git init

# 3. 파일 생성 (예: README)
$ echo "# My Docker Project" > README.md

# 4. 스테이징 및 커밋
$ git add .
$ git commit -m "Initial commit"
```

---

## 4. 원격 저장소 연결 및 Push (Remote & Push)
GitHub 등에 만든 빈 저장소와 내 로컬 폴더를 연결합니다.

```bash
# 1. 원격 저장소 주소 연결 (GitHub URL 입력)
$ git remote add origin https://github.com/사용자이름/저장소이름.git

# 2. 브랜치 이름 변경 (최신 표준인 main으로 변경 권장)
$ git branch -M main

# 3. 원격으로 전송 (업스트림 설정)
$ git push -u origin main
```

### 💡 `-u` (또는 `--set-upstream`)의 의미는?
* **최초 1번만** 실행하면 됩니다.
* 로컬의 `main` 브랜치와 원격의 `origin/main` 브랜치를 **동기화(연결)** 시켜주는 옵션입니다.
* 이후에는 단순히 `git push` 또는 `git pull`만 입력해도 알아서 `origin main`으로 동작하게 됩니다. 매우 편리하죠!

---

### 🚀 Docker 전문가의 추가 팁: `.gitignore`
Docker를 활용하신다면, 불필요한 파일이 Git에 올라가지 않도록 `.gitignore` 파일을 꼭 만드세요.

```bash
$ cat <<EOF > .gitignore
# Docker 관련 무시
.docker/
*.tar
.env

# OS/IDE 관련
.DS_Store
.vscode/
node_modules/
__pycache__/
EOF
```

이제 Git 설정은 완벽합니다! 이제 이 환경 위에 **Dockerfile**을 만들어서 컨테이너를 빌드해 볼까요? 어떤 서비스를 띄워보고 싶으신가요? (예: Nginx, Python 앱 등)