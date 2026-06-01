import time
import sys
import functools
from typing import Callable, Any

def catch_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to intercept exceptions at the CLI boundary.
    It catches exceptions and prints the cause and a helpful hint to stderr,
    exiting with a non-zero code instead of printing a raw Python stacktrace.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            print("\n[오류] 사용자에 의해 프로그램 실행이 중단되었습니다.", file=sys.stderr)
            print("[힌트] 명령을 다시 실행해 주세요.", file=sys.stderr)
            sys.exit(130)
        except ValueError as e:
            print(f"[오류] 잘못된 입력값 또는 형식: {e}", file=sys.stderr)
            print("[힌트] 입력 형식을 확인하고 유효한 값을 입력해 주세요.", file=sys.stderr)
            sys.exit(1)
        except FileNotFoundError as e:
            print(f"[오류] 파일을 찾을 수 없습니다: {e}", file=sys.stderr)
            print("[힌트] 파일 경로가 정확한지, 또는 파일이 실제로 존재하는지 확인해 주세요.", file=sys.stderr)
            sys.exit(2)
        except PermissionError as e:
            print(f"[오류] 파일 접근 권한이 없습니다: {e}", file=sys.stderr)
            print("[힌트] 대상 파일 또는 폴더의 쓰기/읽기 권한을 확인해 주세요.", file=sys.stderr)
            sys.exit(3)
        except Exception as e:
            print(f"[오류] 실행 중 예외가 발생했습니다: {e}", file=sys.stderr)
            print("[힌트] 입력 파라미터를 다시 확인하시거나 저장 데이터가 손상되지 않았는지 점검해 주세요.", file=sys.stderr)
            sys.exit(5)
    return wrapper

def measure_time(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to measure the execution time of operations.
    Prints the execution time in milliseconds to stderr (so it doesn't pollute stdout output).
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
    Logs when an operation starts and ends.
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
