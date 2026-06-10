import argparse
import sys
from budget_app.repository import FileRepository
from budget_app.service import BudgetService
from budget_app.cli import InteractiveShell

def main():
    parser = argparse.ArgumentParser(    #ArgumentParser 객체를 생성하여 명령줄 인자를 처리할 준비를 합니다.
        description="파일 기반 가계부 콘솔 프로그램 (budget_app)",
        add_help=True
    )
    # Global option
    parser.add_argument(   #--data-dir 옵션을 추가하여 데이터 저장 폴더 경로를 지정할 수 있도록 합니다. 기본값은 "./data"입니다.
        "--data-dir",
        default="./data",
        help="데이터 저장 폴더 경로 (기본값: ./data)"
    )

    args, unknown = parser.parse_known_args()   #명령줄 인자를 파싱하여 args 객체에 저장합니다. unknown 변수에는 알 수 없는 인자가 저장됩니다.

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
