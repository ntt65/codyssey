"""
================================================================================
budget_app/decorators.py - 부가 기능 처리용 데코레이터 정의 모듈 (Aspects)
================================================================================
본 모듈은 가계부 애플리케이션의 핵심 비즈니스 로직과 상호작용 경계에서 작동하는
데코레이터(로깅, 실행 시간 정밀 측정, 에러 처리 경계 관리)들을 정의합니다.

[주요 데코레이터]
1. catch_errors: 대화형 CLI 경계에서 발생하는 각종 예외를 우아하게 포착하여 힌트를 제공하고 셸 크래시를 방지
2. measure_time: 특정 비즈니스 연산의 수행 경과 시간을 ms 단 단위로 정밀하게 로그 기재
3. log_action: 메서드 실행 시작/완료 상태에 대해 로깅 처리 수행
================================================================================
"""

import time
import sys
import functools
from typing import Callable, Any

def catch_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    대화형 명령어 인터페이스 실행 도중 발생하는 예외 상황을 격리하고 원인과 해결 힌트를 출력하는 데코레이터입니다.
    이 데코레이터는 sys.exit()를 부르지 않고 처리함으로써 가계부 메인 셸의 무한 루프가 유지되도록 보호합니다.

    Args:
        func (Callable): 예외를 감시할 타겟 함수

    Returns:
        Callable: 예외 방어 처리가 적용된 래퍼 함수
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)                                      # 원본 함수 호출
        except ValueError as e:                                               # 입력 포맷 및 데이터 유효성 위반 에러 포착
            print(f"[오류] {e}", file=sys.stderr)                              # 에러 세부 내용 stderr 출력
            print("[힌트] 입력 형식을 확인하고 유효한 값을 입력해 주세요.", file=sys.stderr) # 사용자 대응 가이드 제공
        except FileNotFoundError as e:                                        # 지정 경로 파일 누락 시 예외 포착
            print(f"[오류] 파일을 찾을 수 없습니다: {e}", file=sys.stderr)
            print("[힌트] 파일 경로가 정확한지, 또는 파일이 실제로 존재하는지 확인해 주세요.", file=sys.stderr)
        except PermissionError as e:                                          # 읽기/쓰기 권한 거부 예외 포착
            print(f"[오류] 파일 접근 권한이 없습니다: {e}", file=sys.stderr)
            print("[힌트] 대상 파일 또는 폴더의 쓰기/읽기 권한을 확인해 주세요.", file=sys.stderr)
        except Exception as e:                                                # 예측하지 못한 치명적 예외 안전 방어
            print(f"[오류] 실행 중 예외가 발생했습니다: {e}", file=sys.stderr)
            print("[힌트] 입력 파라미터를 다시 확인하시거나 저장 데이터가 손상되지 않았는지 점검해 주세요.", file=sys.stderr)
    return wrapper

def measure_time(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    타겟 함수의 실행 소요 시간을 정밀 측정하여 로그를 stderr에 출력하는 데코레이터입니다.

    Args:
        func (Callable): 실행 시간을 측정하고자 하는 함수

    Returns:
        Callable: 시간 측정이 추가된 래퍼 함수
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()                                           # 고해상도 타이머 시작 지점 기록
        result = func(*args, **kwargs)                                        # 실제 본 함수 기능 수행
        elapsed = time.perf_counter() - start                                 # 경과 시간(초 단위) 계산
        print(f"[LOG] {func.__name__} 완료 - 경과 시간: {elapsed * 1000:.2f}ms", file=sys.stderr) # 밀리초 단위 포맷팅 로그 출력
        return result                                                         # 원래 실행 결과 반환
    return wrapper

def log_action(action_name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    특정 작업의 시작 및 완료 메시지를 기재하는 로깅 데코레이터 팩토리 함수입니다.

    Args:
        action_name (str): 로그에 기재될 동작의 명칭

    Returns:
        Callable: 데코레이터 함수
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            print(f"[LOG] '{action_name}' 작업 시작...", file=sys.stderr)       # 시작 로그 기록
            result = func(*args, **kwargs)                                    # 본체 함수 호출
            print(f"[LOG] '{action_name}' 작업 완료.", file=sys.stderr)         # 완료 로그 기록
            return result                                                     # 반환값 전달
        return wrapper
    return decorator
