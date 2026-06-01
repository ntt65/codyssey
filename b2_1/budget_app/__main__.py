import argparse
import sys
from budget_app.repository import FileRepository
from budget_app.service import BudgetService
from budget_app.cli import InteractiveShell

def main():
    parser = argparse.ArgumentParser(
        description="파일 기반 가계부 콘솔 프로그램 (budget_app)",
        add_help=True
    )
    # Global option
    parser.add_argument(
        "--data-dir",
        default="./data",
        help="데이터 저장 폴더 경로 (기본값: ./data)"
    )

    args, unknown = parser.parse_known_args()

    try:
        repo = FileRepository(args.data_dir)
        service = BudgetService(repo)
        shell = InteractiveShell(service)
        shell.run()
    except Exception as e:
        print(f"[오류] 초기 구동 실패: {e}", file=sys.stderr)
        print("[힌트] 데이터 저장 경로의 읽기/쓰기 권한을 확인해 주세요.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
