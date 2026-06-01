import time
import sys
import functools
from typing import Callable, Any

def catch_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to intercept exceptions at the interactive command boundary.
    It catches exceptions and prints the cause and a helpful hint to stderr,
    without calling sys.exit(), thereby keeping the main shell loop alive.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            print(f"[오류] {e}", file=sys.stderr)
            print("[힌트] 입력 형식을 확인하고 유효한 값을 입력해 주세요.", file=sys.stderr)
        except FileNotFoundError as e:
            print(f"[오류] 파일을 찾을 수 없습니다: {e}", file=sys.stderr)
            print("[힌트] 파일 경로가 정확한지, 또는 파일이 실제로 존재하는지 확인해 주세요.", file=sys.stderr)
        except PermissionError as e:
            print(f"[오류] 파일 접근 권한이 없습니다: {e}", file=sys.stderr)
            print("[힌트] 대상 파일 또는 폴더의 쓰기/읽기 권한을 확인해 주세요.", file=sys.stderr)
        except Exception as e:
            print(f"[오류] 실행 중 예외가 발생했습니다: {e}", file=sys.stderr)
            print("[힌트] 입력 파라미터를 다시 확인하시거나 저장 데이터가 손상되지 않았는지 점검해 주세요.", file=sys.stderr)
    return wrapper

def measure_time(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to measure the execution time of operations.
    Prints the execution time in milliseconds to stderr.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"[LOG] {func.__name__} 완료 - 경과 시간: {elapsed * 1000:.2f}ms", file=sys.stderr)
        return result
    return wrapper

def log_action(action_name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to log specific actions to stderr.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            print(f"[LOG] '{action_name}' 작업 시작...", file=sys.stderr)
            result = func(*args, **kwargs)
            print(f"[LOG] '{action_name}' 작업 완료.", file=sys.stderr)
            return result
        return wrapper
    return decorator
