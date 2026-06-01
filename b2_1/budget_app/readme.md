# 가계부 애플리케이션(budget_app) 구현 결과 보고서

본 보고서는 `/Users/mpeg46551/git/codyssey/b2_1/` 경로에 완성된 **파일 기반 가계부 콘솔 프로그램(budget_app)**의 구현 구조와 주요 기술적 해결 방안을 상세히 설명합니다.

---
### 작업 요약                                                                                                                       
                                                                                                                                      
  1. 계층형 설계 구조 구현 ( budget_app/ ):                                                                                           
      • models.py: 데이터 구조 및 직렬화                                                                                         
      • repository.py: JSONL 파일 저장 및 읽기, 원자성 보장 파일 교체 알고리즘                                                       
      • service.py: 데이터 검증, 예산 계산, 반복 거래 생성 및 백업 등 비즈니스 로직                                               
      • decorators.py: 예외 처리( @catch_errors ), 시간 측정, 활동 로깅                                                              
      • cli.py:  argparse  서브커맨드 처리, 한글 폰트 폭 보정 테이블 정렬기                                                   
  2. 제약사항 만족:                                                                                                                   
      • 대용량 파일도 처리 가능한  yield  제너레이터 기반 파일 스트리밍. 조회                                                          
      • 외부 라이브러리 설치 없이 파이썬 표준 라이브러리( json ,  csv ,  zipfile ,  tempfile ,  unittest )만 활용                     
      • 상세한 타입 힌트와 코드 모듈화 적용                                                                                           
  3. 보너스 기능 추가:                                                                                                                
      • 데이터 백업 기능 ( backup )                                                                                                   
      • 월세/월급 자동 등록용 반복 내역 생성 기능 ( recurring )                                                                       
      • 문자열 및 한글 정렬로 컬럼을 이쁘게 맞춰주는 테이블 포맷터 ( cli.py  내  print_aligned_rows )                                 
      • 임시 파일 수정 후 덮어쓰는 원자적 안전 저장 로직 ( os.replace )                                                               
  4. 검증:                                                                                                                            
      • test_budget.py에 작성된 8개의 모든 핵심 기능 단위/통합 테스트 슈트 성공 통과                                                  
      • 상세 설명과 스키마 명세를 정리한 README.md 생성                                                                          
                                                                                                                                      
  ──────                                                                                                                              
  ### 실행 예시                                                                                                                       
                                                                                                                                      
   /Users/mpeg46551/git/codyssey/b2_1  폴더로 이동한 뒤 다음과 같이 프로그램을 실행해 볼 수 있습니다:                                 
                                                                                                                                      
    # 1. 전체 도움말 확인                                                                                                             
    python3 -m budget_app --help                                                                                                      
                                                                                                                                      
    # 2. 거래 추가 (대화형 실행)                                                                                                      
    python3 -m budget_app add
  
    # 3. 거래 내역 목록 조회
    python3 -m budget_app list --limit 5
  
    # 4. 테스트 슈트 실행
    PYTHONPATH=. python3 -m unittest tests/test_budget.py


## 1. 프로젝트 파일 목록 및 경로 링크

전체 구현 파일들은 아래와 같이 기능적 책임에 따라 분리되었습니다. 

| 파일명 | 기능 및 역할 |
| :--- | :--- |
| [models.py](file:///Users/mpeg46551/git/codyssey/b2_1/budget_app/models.py) | `Transaction`, `RecurringTemplate` 등의 데이터 규격 정의 및 직렬화/역직렬화 구현 |
| [repository.py](file:///Users/mpeg46551/git/codyssey/b2_1/budget_app/repository.py) | JSONL 파일 CRUD, 제너레이터 스트리밍, ID 채번 및 원자적 쓰기(Atomic Write) 구현 |
| [service.py](file:///Users/mpeg46551/git/codyssey/b2_1/budget_app/service.py) | 데이터 검증, 예산 대비 소모율 계산, 중복 검사, 백업 압축 등 비즈니스 로직 처리 |
| [decorators.py](file:///Users/mpeg46551/git/codyssey/b2_1/budget_app/decorators.py) | CLI 경계 예외 처리(`@catch_errors`), 시간 측정(`@measure_time`), 작업 로깅(`@log_action`) 데코레이터 |
| [cli.py](file:///Users/mpeg46551/git/codyssey/b2_1/budget_app/cli.py) | `argparse` 기반 명령어 파싱, 대화형 추가/수정 흐름 및 정렬 테이블 렌더링 |
| [\_\_main\_\_.py](file:///Users/mpeg46551/git/codyssey/b2_1/budget_app/__main__.py) | CLI 실행 패키지 진입점 (`python3 -m budget_app`) |
| [\_\_init\_\_.py](file:///Users/mpeg46551/git/codyssey/b2_1/budget_app/__init__.py) | 패키지 초기화 파일 |
| [test_budget.py](file:///Users/mpeg46551/git/codyssey/b2_1/tests/test_budget.py) | 8개의 통합/단위 테스트 케이스를 포함한 테스트 슈트 |
| [README.md](file:///Users/mpeg46551/git/codyssey/b2_1/README.md) | 상세 설치, 실행, 기능 설명, CSV 스키마 및 기술 요약이 담긴 안내서 |

---

## 2. 주요 기능 및 제약 조건 해결 요약

### 2.1 제너레이터 기반 대용량 파일 스트리밍 처리 (`repository.py`, `service.py`)
- **요구사항**: 저장 파일을 한 번에 로드하지 않고 제너레이터 기반 스트리밍 처리로 구현.
- **해결**: `stream_transactions()` 함수에서 한 번에 한 줄씩 읽는 `yield` 기반 제너레이터를 구현하여 대용량 데이터 조회 시의 메모리 사용량을 최소화했습니다.
- **$O(limit)$ 정렬 및 필터링**: `list` 및 `search` 시에 최신순(신규 데이터가 마지막에 추가되므로) 조회를 위해 **크기가 `limit`으로 제한된 버퍼**를 스트리밍 중에 실시간으로 유지하고 갱신하는 방식을 활용하여, 전체 목록을 메모리에 적재하지 않고 오직 요청한 `limit` 개수만큼의 트랜잭션 데이터만 메모리에 올라가도록 극적으로 최적화했습니다.

### 2.2 데코레이터를 통한 횡단 관심사(Cross-cutting Concerns) 분리 (`decorators.py`)
- **요구사항**: 예외 처리/로그/시간 측정 데코레이터 분리 구조 설계 및 실제 적용.
- **해결**: 
  - `@catch_errors`: 예외 발생 시 스택 트레이스 출력을 숨기고 명확한 **원인(Cause)** 및 **해결 힌트(Hint)**를 stderr로 상세히 출력하며, 정상 종료 시 `0`, 비정상 종료 시 `0`이 아닌 적합한 상태 코드(예: `1`, `2`, `4` 등)를 리턴합니다.
  - `@measure_time`: 함수 실행 완료 시 걸린 시간(ms)을 stderr에 로깅합니다.
  - `@log_action`: 비즈니스 로직 시작과 끝을 표기합니다.

### 2.3 데이터 수정/삭제의 원자성(Atomicity) 강화 (`repository.py`)
- **요구사항**: `update`/`delete` 시 저장소 신뢰성 확보.
- **해결**: 원본 데이터에 바로 덮어쓰지 않고, 임시 파일(`tempfile.mkstemp`)을 생성하여 작업을 순차적으로 기록한 뒤, 작업이 성공적으로 완료되었을 때만 OS 수준의 `os.replace` 원자적 파일 치환 연산을 사용해 덮어씌움으로써 도중 장애 발생 시에도 데이터 정합성이 깨지지 않도록 하였습니다.

### 2.4 카테고리 관리 및 동적 예외 처리 (`service.py`, `cli.py`)
- **요구사항**: 존재하지 않는 카테고리 등록 제한 및 삭제 시 기존 거래 내역 존재 여부 검사.
- **해결**:
  - `add` 또는 `update` 도중 존재하지 않는 카테고리명이 입력되면, 기등록 카테고리 목록을 보여주며 즉시 추가하고 진행할 것인지 묻는 스마트 흐름(y/n)을 CLI에 내장해 사용성을 높였습니다.
  - `category remove` 명령 시 전체 트랜잭션을 스트리밍하여 해당 카테고리가 1번이라도 활용 중인지 검증하고, 있을 경우 에러와 함께 삭제를 완전히 차단합니다.

### 2.5 보너스 과제 전체 반영
1. **데이터 백업 기능 (`backup`)**: 전체 가계부 관련 데이터 파일을 타임스탬프가 포함된 단일 Zip 파일로 압축하여 백업하는 `backup` 서브명령 구현.
2. **반복 거래 내역 자동 관리 (`recurring`)**: 월급/월세 등의 반복 일자 템플릿을 등록하고, 특정 월에 일괄 생성해 주는 `recurring generate` 기능 구현. 중복 삽입 방지 로직(동일 날짜, 카테고리, 금액, 메모, `recurring` 태그 기준)이 철저하게 포함되어 있습니다.
3. **가독성 개선 정렬 테이블 (`cli.py`)**: 외부 라이브러리 없이 한글(2칸 폭)과 영어/숫자(1칸 폭)의 넓이를 정확하게 구분해 주는 한글 폰트 보정 테이블 정렬 출력기 구현.
4. **저장 원자성 강화**: `repository.py` 내의 모든 갱신 및 파일 재생성 메서드에 임시 파일 생성 + rename 전략을 일괄 적용.

---

## 3. 테스트 코드 결과 검증

작성된 [test_budget.py](file:///Users/mpeg46551/git/codyssey/b2_1/tests/test_budget.py)를 실행하여 모든 핵심 동작과 예외 규칙이 완벽히 작동하는 것을 검증하였습니다.

```bash
$ PYTHONPATH=. python3 -m unittest tests/test_budget.py
........
----------------------------------------------------------------------
Ran 8 tests in 0.017s

OK
```

모든 테스트 케이스가 성공적으로 검증을 마쳤으며, 제약 사항인 외부 라이브러리 미사용 조건(표준 라이브러리인 `unittest`, `json`, `csv`, `zipfile`, `tempfile` 만으로 구동) 역시 성공적으로 충족되었습니다.
