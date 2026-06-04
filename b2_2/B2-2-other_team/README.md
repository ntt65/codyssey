# 실전 Git 협업 워크플로우

## 프로젝트 개요

팀이 GitHub 기반 실제 협업 흐름을 연습하기 위한 프로젝트입니다.

## 실행환경

- Python 3.10 이상
- Git
- GitHub

## 프로젝트 구조

```text
.
├── .github/
│   ├── CODEOWNERS                # 파일/폴더별 책임 리뷰어 지정
│   ├── ISSUE_TEMPLATE/           # Issue 템플릿
│   │   ├── bug_report.md
│   │   ├── docs-템플릿.md
│   │   ├── feat-템플릿.md
│   │   └── refactor-템플릿.md
│   └── PULL_REQUEST_TEMPLATE.md  # PR 본문 템플릿
├── .gitignore
├── README.md                      # 프로젝트 개요, 실행환경, 구조, 수행 항목 정리
├── SUBMISSION.md                  # 팀원별 Issue, PR, 문서, 증빙 링크 제출 인덱스
├── docs/
│   ├── CONTRIBUTING.md            # 브랜치, 커밋, PR, 리뷰, 충돌 대응 규칙
│   ├── conflict-resolution.md     # 충돌 상황과 해결 과정 기록
│   ├── rebase-history.md          # rebase 히스토리 정리 기록
│   └── troubleshooting-log.md     # Git 트러블슈팅 시나리오 수행 기록
├── git_history.md                 # git log --oneline --graph --all 증빙
├── images/
│   ├── git_main_rule1.png         # main 브랜치 보호 규칙 증빙 이미지
│   ├── git_main_rule2.png         # main 브랜치 보호 규칙 증빙 이미지
│   └── trouble-shooting/          # Git 트러블슈팅 증빙 이미지
└── src/                           # 팀별 유틸 함수와 사용 예시
    ├── data_utils.py
    └── text_utils.py
```

## 수행 항목 체크리스트

### 팀 구성 및 저장소 준비

- [x] 3~5인 팀 구성
- [x] GitHub Organization 저장소 생성 또는 개인 저장소에 Collaborator 초대
- [x] 기본 폴더 및 파일 구성
  - [x] `README.md`
  - [x] `docs/`
  - [x] `src/`
- [x] `main` 브랜치 Branch Protection Rule 설정
  - [x] `main` 직접 push 금지
  - [x] PR을 통한 병합만 허용
  - [x] 최소 1명 승인 필요

### 브랜치 전략 적용

- [x] GitHub Flow 적용
- [x] `main`은 항상 배포 가능한(깨지지 않는) 상태 유지
- [x] 작업 단위별 `feature/*` 브랜치 사용
- [x] 브랜치 네이밍 규칙 수립
- [x] 브랜치 규칙을 `docs/CONTRIBUTING.md`에 문서화
- [x] GitHub Flow 선택 이유를 3줄 이내로 `README.md` 또는 `docs/CONTRIBUTING.md`에 기록

### 이슈 기반 작업 및 PR 연동

- [x] 각 작업을 GitHub Issue로 생성
- [x] PR과 Issue 연동
- [x] PR 본문에 `Closes #이슈번호` 또는 `Fixes #이슈번호` 포함
- [x] `SUBMISSION.md`에서 팀원별 Issue/PR 확인 가능하도록 정리

### 커밋 메시지 컨벤션

- [x] 팀 커밋 메시지 규칙 수립
- [x] `docs/CONTRIBUTING.md`에 커밋 메시지 컨벤션 문서화
- [x] `feat: subject`, `fix: subject`, `docs: subject`, `refactor: subject` 등 의미 있는 형식 사용
- [x] `update`, `fix`, `temp`, `wip`, `final`, `bug fix`, `edit file`처럼 변경 대상을 알 수 없는 메시지 금지

### PR 기반 협업

- [x] 모든 `feature/*` 브랜치를 PR로 `main`에 병합
- [x] 팀원별 PR 생성 및 병합 최소 2개 이상
- [x] 팀원별 코드 리뷰 최소 2개 이상 작성
- [x] 본인 PR 제외 리뷰 작성
- [x] 본인 PR에서 리뷰 코멘트 반영 경험 최소 1회 이상 기록
- [x] PR 본문에 변경 사항(What) 포함
- [x] PR 본문에 변경 이유(Why) 포함
- [x] PR 본문에 테스트/검증 방법(How) 포함

### 코드 리뷰 최소 품질 기준

- [x] 각 PR에 실질적인 리뷰 코멘트 1개 이상 작성
- [x] 단순한 `LGTM`, `좋아요`만 작성하지 않기
- [x] 특정 라인/파일에 대한 질문, 대안, 리스크, 개선 제안 중 하나 이상 포함
- [x] 리뷰어와 작성자 간 최소 1회 이상 상호작용 기록

### 충돌 해결 실습

- [x] 의도적으로 충돌 상황 생성
- [x] 팀 전체 기준 최소 2회 이상 충돌 해결 기록 남기기
- [x] 최소 1회 이상 비자명 충돌 포함
  - [x] 같은 파일의 같은 hunk 또는 인접 라인을 서로 다르게 수정
- [x] 충돌 해결 과정을 `docs/conflict-resolution.md`에 기록

### Git 트러블슈팅 실습

- [x] `git commit --amend`로 최근 커밋 메시지 수정
- [x] `git reset --soft HEAD~1^`로 로컬 커밋 취소 및 변경 유지
- [x] `git revert`로 원격에 push된 커밋 취소
- [x] `git stash` / `git stash pop`으로 작업 보관 후 복원
- [x] 팀원별 최소 1개 시나리오 해결 기록 작성 참여
- [x] 모든 기록을 `docs/troubleshooting-log.md`에 작성

### 협업 가이드 문서 작성

- [x] `docs/CONTRIBUTING.md`에 팀 협업 규칙 작성(팀원 분담 후 작성)
- [x] 브랜치 네이밍 규칙 포함
- [x] 커밋 메시지 컨벤션 포함
- [x] PR 작성 규칙 포함
- [x] 코드 리뷰 규칙 포함
- [x] 충돌 발생 시 대응 흐름 포함
- [x] 충돌 기록 담당자와 기록 위치 명시

### 보너스 과제

- [x] 히스토리 정리: `git rebase -i`로 개인 `feature/*` 브랜치의 커밋을 squash/reword하고 정리 전/후 히스토리 비교 문서화
- [x] CODEOWNERS/리뷰어 자동화: `.github/CODEOWNERS`를 추가해 파일/폴더별 책임 리뷰어 지정

## 제약 사항

### 팀별 제약 사항

- 3~5인 팀 진행
- 전원 Git 작업 참여
- GitHub 사용
- 기능 구현보다 협업 과정 기록 우선
- 공유 브랜치 히스토리 재작성 금지
- 팀 합의 없는 강제 push/rebase 금지
- 충돌/트러블슈팅 기록 필수

### 개인별 제약 사항

- PR 생성 및 병합 2개 이상
- 본인 PR 제외 코드 리뷰 2개 이상
- 본인 PR 리뷰 반영 1회 이상
- Git 트러블슈팅 기록 1개 이상 참여
- 유틸 함수 기여 커밋 1건 이상

## 산출 결과물

### 제출 링크

- GitHub 저장소: [codyssey-git/B2-2](https://github.com/codyssey-git/B2-2)
- `SUBMISSION.md`: [SUBMISSION.md](./SUBMISSION.md)
- Git 히스토리 증빙: [git_history.md](./git_history.md)

### 협업 문서

- `docs/CONTRIBUTING.md`: [docs/CONTRIBUTING.md](./docs/CONTRIBUTING.md)
- `docs/conflict-resolution.md`: [docs/conflict-resolution.md](./docs/conflict-resolution.md)
- `docs/troubleshooting-log.md`: [docs/troubleshooting-log.md](./docs/troubleshooting-log.md)
- Git rule: [docs/CONTRIBUTING.md](./docs/CONTRIBUTING.md)
- Git rule 이미지: [images/git_main_rule1.png](./images/git_main_rule1.png), [images/git_main_rule2.png](./images/git_main_rule2.png)

### 보너스 과제

- 히스토리 정리: [docs/rebase-history.md](./docs/rebase-history.md)
- CODEOWNERS/리뷰어 자동화: [.github/CODEOWNERS](./.github/CODEOWNERS)
