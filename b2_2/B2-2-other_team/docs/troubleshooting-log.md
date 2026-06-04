### 시나리오: git commit --amend

* 종류: `git commit --amend`
* 참여자: 팀원 1

### 상황

* `docs/troubleshooting-log.md`에 Git 트러블슈팅 기록을 추가한 뒤, 첫 커밋 메시지를 너무 모호하게 작성한 상황을 가정했습니다.
* 처음 작성한 커밋 메시지는 `docs: 기록 추가`였는데, 이 메시지만 보면 어떤 기록을 추가했는지 명확히 알기 어렵습니다.
* 따라서 `git commit --amend`를 사용하여 최근 커밋 메시지를 더 구체적으로 수정했습니다.
* 실습 과정에서 원격 브랜치에 한 번 push한 뒤 커밋 메시지를 수정하게 되었기 때문에, 수정된 커밋을 원격 브랜치에 다시 반영하기 위해 `git push --force-with-lease`를 사용했습니다.

### 수행 명령 또는 절차

```bash
git switch main
git pull origin main
git switch docs/31

git add docs/troubleshooting-log.md
git commit -m "docs: 기록 추가"
git log --oneline -1

git push origin docs/31

git commit --amend -m "docs: git amend 트러블슈팅 기록 추가"
git log --oneline -1

git push --force-with-lease origin docs/31
```

### 결과

* 최근 커밋 메시지가 `docs: 기록 추가`에서 `docs: git amend 트러블슈팅 기록 추가`로 변경되었습니다.
* `git log --oneline -1` 명령어를 통해 amend 전후의 최근 커밋 메시지가 달라진 것을 확인했습니다.
* `git commit --amend`를 사용하면서 기존 커밋이 수정되고 커밋 해시가 변경되는 것을 확인했습니다.
* 이미 원격 브랜치에 push된 커밋을 수정했기 때문에, 원격 브랜치에는 `git push --force-with-lease origin docs/31` 명령어로 반영했습니다.
* 새로운 커밋을 하나 더 추가한 것이 아니라, 가장 최근 커밋 자체를 수정하여 Git 히스토리를 더 명확하게 정리했습니다.

### 배운 점

* `git commit --amend`는 가장 최근 커밋을 수정할 때 사용하는 명령어입니다.
* 커밋 메시지를 잘못 작성했거나, 방금 만든 커밋에 작은 수정 사항을 함께 포함하고 싶을 때 사용할 수 있습니다.
* `git commit --amend`를 사용하면 기존 커밋이 수정되면서 커밋 해시가 바뀝니다.
* 따라서 이미 원격 저장소에 push한 커밋에 사용하면 로컬 브랜치와 원격 브랜치의 커밋 이력이 달라질 수 있습니다.
* 이미 push한 커밋을 amend한 경우 일반 `git push`가 거부될 수 있으며, 이때는 원격 브랜치 상태를 확인한 뒤 `git push --force-with-lease`를 사용할 수 있습니다.
* `--force-with-lease`는 원격 브랜치가 내가 마지막으로 확인한 상태에서 바뀌지 않았을 때만 강제 push를 허용하므로, 단순 `--force`보다 안전합니다.
* 다만 공유 브랜치나 `main` 브랜치에서는 다른 팀원의 작업에 영향을 줄 수 있으므로 신중하게 사용해야 합니다.
* 협업 상황에서는 일반적으로 push하기 전의 로컬 커밋에 `git commit --amend`를 사용하는 것이 가장 안전합니다.

---

## 시나리오 기록

### 시나리오: git revert

* 종류: `git revert`
* 참여자: 팀원 3 (성원모)

### 상황

* `validate_length()` 함수에 음수 길이 검증 로직을 추가하는 과정에서 잘못된 조건 처리가 포함된 커밋을 생성하였다.
* 해당 커밋이 원격 저장소에 push된 이후 오류를 발견하였다.
* 이미 공유된 커밋이므로 `git reset` 대신 `git revert`를 사용하여 변경 사항을 취소하였다.

## 실수로 커밋한 코드
```python
if min_length < 0:
    return False
```

## 정상 코드 (수정본)
```python
if min_length < 0:
    raise ValueError("min_length는 0 이상이어야 합니다.")
```
### 수행 명령 또는 절차

```bash
git log --oneline
9cfeacf (origin/main, origin/docs/26, origin/HEAD,
14ab263 (origin/feat/19) Merge branch
'main' into
main) Merge pull request #23 from
codyssey-git/feat/19
feat/19
05db6e7 Merge pull request #18 from codyssey-git/feat/15
2697723 (origin/feat/15, feat/15) Merge branch
'main' into feat/15

git revert 9cfeacf

git log --oneline

vnkers948441@c6r6s5 B2-2 % git log --oneline
Idf150c Revert "Merge pull request #23 from codyssey-git/feat/19'
434dd75 refactor: 문자열 업데이트
9cfeacf (origin/main, origin/docs/26, origin/HEAD, main) Merge pull request #23 from codyssey-git/feat/19
```

### 결과

* 잘못된 변경 사항을 취소하는 새로운 커밋이 생성되었다.
* 기존 커밋 이력은 유지되었다.
* 협업 중인 저장소의 히스토리를 안전하게 보존하면서 문제를 해결할 수 있었다.

### 배운 점

* 이미 원격 저장소에 공유된 커밋은 `git reset`보다 `git revert`를 사용하는 것이 안전하다.
* `git revert`는 기존 커밋을 삭제하지 않고 취소 이력을 남기므로 협업 환경에 적합하다.
* 커밋을 되돌려야 하는 상황에서도 Git 히스토리를 보존할 수 있다.
----

### 시나리오: git revert 1 - 윤대영

- 종류: `git revert`
- 참여자: 윤대영

### 상황

- Git 트러블슈팅 실습 중 `docs/conflict-resolution.md` 파일에 이름을 추가하고 커밋했다.
- 커밋 후 현재 브랜치가 해당 작업을 진행해야 하는 브랜치가 아니라는 것을 확인했다.
- 이미 커밋이 생성된 상태였기 때문에, 커밋 기록을 삭제하지 않고 변경사항만 되돌리기 위해 `git revert`를 사용했다.

### 수행 명령 또는 절차

```bash
git add docs/conflict-resolution.md

git commit -m "docs: 충돌 해결 문서에 이름 추가"

git log --oneline

git revert 185b6fd
```

### 결과

- `docs/conflict-resolution.md`에 잘못 추가했던 이름이 제거되었다.
- 기존 커밋 `185b6fd`는 삭제되지 않고 유지되었다.
- 해당 커밋의 변경사항을 취소하는 새로운 revert 커밋이 생성되었다.

#### revert 이전

![revert 이전](../images/trouble-shooting/revert%20이전_윤대영.png)

#### revert 이후

![revert 이후](../images/trouble-shooting/revert%20이후_윤대영.png)

### 배운 점

- 이미 커밋한 변경사항은 `git revert`를 사용해 안전하게 되돌릴 수 있다.
- `git revert`는 기존 커밋을 삭제하는 것이 아니라, 반대 변경사항을 담은 새 커밋을 만든다.
- 협업 중 공유될 수 있는 커밋은 `reset`으로 기록을 지우기보다 `revert`로 되돌리는 것이 더 안전하다.
- 작업 전 현재 브랜치를 확인하는 습관이 중요하다.

---

## 시나리오: git stash / git stash pop

### 참여자

* bangahee

### 상황

* 작업 브랜치에서 문서 내용을 수정하던 중, 아직 커밋하기에는 완성되지 않은 상태였습니다.
* 하지만 최신 main 브랜치 내용을 먼저 확인하거나 다른 브랜치로 이동해야 하는 상황이 발생했습니다.
* 작업 중인 변경 사항을 잃지 않기 위해 `git stash`를 사용해 임시 저장했습니다.

### 시도한 명령/절차

```bash
git status
git stash
git status
git switch main
git pull origin main
git switch docs/25
git stash pop
```

### 결과

* 커밋하지 않은 작업 내용을 `git stash`로 임시 저장했습니다.
* 작업 디렉터리가 clean 상태가 되어 `main` 브랜치로 이동하고 최신 내용을 확인할 수 있었습니다.
* 다시 `docs/25` 브랜치로 돌아온 뒤 `git stash pop`을 사용하여 임시 저장했던 내용을 복원했습니다.

### 왜 이 방법을 선택했는가

* 아직 완성되지 않은 변경 사항을 불필요하게 커밋하지 않기 위해 사용했습니다.
* 작업 내용을 잃지 않으면서도 브랜치 이동과 최신 내용 확인을 진행할 수 있었기 때문입니다.

### 주의할 점

* `git stash`는 기본적으로 추적 중인 파일의 변경 사항만 저장합니다.
* 새로 생성된 untracked 파일까지 함께 저장하려면 `git stash -u`를 사용해야 합니다.
* `git stash pop` 이후 충돌이 발생할 수 있으므로 반드시 `git status`로 상태를 확인해야 합니다.

---

### 시나리오: git reset --soft HEAD~1

- 종류: `git reset --hard origin/main`, `git reset --soft HEAD~1`
- 참여자: 팀원 5

### 상황

- 로컬 `main` 브랜치에서 `git pull`을 실행했을 때 pull이 되지 않는 문제가 발생했다.
- `git status` 확인 결과, 로컬 `main`과 원격 `origin/main`의 커밋 히스토리가 서로 갈라진 상태였다.
```
➜  docs git:(main) git status
On branch main
Your branch and 'origin/main' have diverged,
and have 1 and 14 different commits each, respectively.
  (use "git pull" if you want to integrate the remote branch with yours)

nothing to commit, working tree clean
```
- 이는 로컬 `main`에는 원격에 없는 커밋 1개가 있고, 원격 `origin/main`에는 로컬에 없는 커밋 14개가 있다는 의미이다.
- 처음에는 마지막 로컬 커밋 1개를 취소하기 위해 `git reset --soft HEAD~1`을 사용할 수 있을지 검토했다.
- 하지만 이 상황의 목적은 마지막 커밋을 다시 작성하는 것이 아니라, 로컬 `main`을 원격 `origin/main`과 완전히 동일한 상태로 맞추는 것이었다.
- 따라서 `git reset --soft HEAD~1`과 `git reset --hard origin/main`의 차이를 비교한 뒤, 현재 상황에는 `git reset --hard origin/main`이 더 적절하다고 판단했다.


- 추가로 `git reset --soft HEAD~1`의 동작 방식을 확인하기 위해 문서 파일을 수정한 뒤 일부러 커밋을 생성했다.
- 이후 마지막 커밋을 취소하되, 커밋에 포함된 변경사항은 삭제하지 않고 유지되는지 확인해야 했다.
- 특히 커밋 메시지를 잘못 작성했거나, 마지막 커밋을 다시 작성해야 하는 상황에서 `git reset --soft HEAD~1`을 사용할 수 있는지 확인하고자 했다.
- 예를 들어 문서 수정 작업인데 커밋 메시지를 `fix` 타입으로 작성한 경우, 마지막 커밋을 취소하고 `docs` 타입으로 다시 커밋할 수 있다.

### 수행 명령 또는 절차
**git reset --hard**
```bash
git fetch origin
git reset --hard origin/main
```

**git reset --soft**
```bash
git add docs/troubleshooting-log.md 
git commit -m "fix: reset soft 내용 추가"
```

```bash
git reset --soft HEAD~1
```

```bash
git status 
git commit -m "docs: reset soft 트러블슈팅 추가"
```

### 결과

- `git reset --hard origin/main`을 실행한 결과, 로컬 `main` 브랜치가 원격 `origin/main`과 동일한 상태로 정리되었다.
- 로컬 `main`에만 있던 불필요한 커밋 1개가 제거되었고, 원격 `main`의 최신 커밋 14개를 기준으로 로컬 브랜치가 맞춰졌다.
- 로컬 `main`이 `origin/main`과 동일해져 더 이상 diverged 상태가 아니게 되었다.
- 이후 `git reset --soft HEAD~1`은 실제 `main` 문제가 해결된 뒤, 문서 작업 브랜치인 `docs/26`에서 별도로 테스트했다.
- 별도 테스트에서 `git reset --soft HEAD~1` 실행한 결과, 마지막 커밋은 취소되었지만 변경사항은 삭제되지 않고 staged 상태로 유지되었다.
- 따라서 `git add`를 다시 하지 않고도 올바른 커밋 메시지로 다시 커밋할 수 있었다.

```
➜  B2-2 git:(docs/26) git reset --soft HEAD~1
➜  B2-2 git:(docs/26) ✗ git status             
On branch docs/26
Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
        modified:   docs/troubleshooting-log.md

➜  B2-2 git:(docs/26) ✗ git commit -m "docs: reset soft 트러블슈팅 추가"
[docs/26 d9bc39b] docs: reset soft 트러블슈팅 추가
 1 file changed, 3 insertions(+), 3 deletions(-)
➜  B2-2 git:(docs/26) 
```


### 배운 점

- `git reset --soft HEAD~1`과 `git reset --hard origin/main`은 모두 `reset` 명령어를 사용하지만 목적과 결과가 다르다.
- `git reset --soft HEAD~1`은 마지막 로컬 커밋 1개를 취소하되, 해당 커밋에 포함된 변경사항은 staged 상태로 유지하는 명령어이다.
- 파일 변경사항을 잃지 않고 커밋만 다시 만들 수 있기 때문에, 커밋 메시지 수정이나 누락된 파일 추가에 적합하다.
- 반면 `git reset --hard origin/main`은 로컬 브랜치를 원격 브랜치인 `origin/main`과 완전히 동일한 상태로 맞춘다.
- `git reset --soft HEAD~1`은 변경사항을 보존하는 명령어이고, `git reset --hard origin/main`은 로컬 브랜치를 원격 브랜치 상태로 강제로 맞추는 명령어이다.
- 두 명령어는 목적이 다르므로 상황에 맞게 구분해서 사용해야 한다.

| 명령어                       | 커밋 기록       | Staging Area | Working Directory |
| ------------------------- | ----------- | ------------ | ----------------- |
| `git reset --soft HEAD~1` | 최근 커밋 1개 취소 | 변경사항 유지됨     | 변경사항 유지됨          |
| `git reset --hard origin/main` | 로컬 브랜치를 `origin/main`과 동일하게 맞춤 | 변경사항 삭제됨 | 변경사항 삭제됨 |

### 정리
- 이번 pull 실패 상황에서는 로컬 `main`과 원격 `origin/main`의 히스토리가 갈라져 있었다.
- 이때 `git reset --soft HEAD~1`을 사용하면 로컬 커밋 1개는 취소되지만, 그 커밋에 포함된 변경사항이 staged 상태로 남는다.
- staged 상태로 남은 변경사항 때문에 이후 git pull 과정에서 원격 변경사항과 충돌할 수 있다.
- 즉, soft reset은 커밋을 다시 만들기 위한 방법이지, 로컬 main을 원격 main과 완전히 동일하게 맞추는 방법은 아니다.
- 현재 상황에서는 로컬 커밋을 유지할 필요가 없었고, 원격 `main`을 기준으로 로컬 `main`을 정리하는 것이 목적이었다.
- 따라서 `git reset --hard origin/main`을 사용하는 것이 적절했다.

### 주의사항
- `git reset --hard origin/main`은 로컬 브랜치를 원격 브랜치 상태로 강제로 맞추는 명령어이다.
- 이 과정에서 로컬에만 있던 커밋이나 아직 커밋하지 않은 변경사항이 삭제될 수 있으므로, 실행 전에 반드시 현재 상태를 확인해야 한다.
    ```bash
    git status
    ```
- 필요한 변경사항이 남아 있다면 `git reset --hard origin/main`을 실행하기 전에 `git stash`로 임시 저장하거나 백업 브랜치를 만들어야 한다.
    ```bash
    git stash
    git branch backup/main-local-work
    ```
- `git reset --soft HEAD~1`은 마지막 커밋을 다시 작성해야 할 때 선택하고, `git reset --hard origin/main`은 로컬 브랜치를 원격 브랜치와 완전히 동일하게 맞춰야 할 때 선택한다.
    ```
    git reset --soft HEAD~1 : 마지막 커밋은 취소하되 변경사항을 유지해야 할 때 사용 
    git reset --hard origin/main : 로컬 변경사항을 버리고 원격 브랜치 기준으로 초기화해야 할 때 사용
    ```