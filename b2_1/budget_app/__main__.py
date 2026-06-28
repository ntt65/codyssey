"""
================================================================================
budget_app/__main__.py - 가계부 애플리케이션 실행 메인 진입점 (Entry Point)
================================================================================
본 스크립트는 `python3 -m budget_app` 명령으로 프로그램 기동 시 직접 실행되는 
패키지 실행의 최외곽 진입 지점입니다. 

[주요 책임]
1. 명령줄 인자 파싱: argparse를 통해 데이터 저장 디렉터리 경로를 파싱합니다.
2. 객체 의존성 조합: FileRepository -> BudgetService -> InteractiveShell 객체를 순차 
   생성하며 의존성 주입(Dependency Injection)을 완료합니다.
3. 예외 전파 차단 및 오류 힌트 제공: 초기화 과정 실패 시 깨끗한 오류 문구를 출력하고 종료합니다.
================================================================================
"""

import argparse
import sys
from budget_app.repository import FileRepository
from budget_app.service import BudgetService
from budget_app.cli import InteractiveShell

def main():
    # 1. 메인 파서 생성
    parser = argparse.ArgumentParser(
        description="파일 기반 가계부 콘솔 프로그램 (budget_app)",
        add_help=True
    )
    
    # 전역 옵션 설정
    parser.add_argument(
        "--data-dir", default="./data",
        help="데이터 저장 폴더 경로 (기본값: ./data)"
    )

    # 2. 서브커맨드(Subparsers) 등록
    # dest="command"를 통해 어떤 명령어가 입력되었는지 식별합니다.
    subparsers = parser.add_subparsers(title="사용 가능한 명령어", dest="command")

    # [명령어 1] add
    parser_add = subparsers.add_parser("add", help="새로운 거래 내역을 추가합니다 (대화형)")

    # [명령어 2] list
    parser_list = subparsers.add_parser("list", help="거래 내역 목록을 조회합니다")
    parser_list.add_argument("--limit", type=int, default=10, help="출력할 최대 건수 (기본값: 10)")

    # [명령어 3] search
    parser_search = subparsers.add_parser("search", help="조건에 맞는 거래 내역을 검색합니다")
    parser_search.add_argument("--from", dest="from_date", help="시작 날짜 (YYYY-MM-DD)")
    parser_search.add_argument("--to", dest="to_date", help="종료 날짜 (YYYY-MM-DD)")
    parser_search.add_argument("--category", help="검색할 카테고리명")
    parser_search.add_argument("--type", choices=["income", "expense"], help="수입/지출 여부")
    parser_search.add_argument("--q", help="메모 검색어")
    parser_search.add_argument("--tag", help="검색할 태그")

     # [명령어 4] summary
    parser_summary = subparsers.add_parser("summary", help="해당 월의 요약을 출력합니다")
    parser_summary.add_argument("--month", help="요약할 월 (YYYY-MM)")
    parser_summary.add_argument("--top", type=int, default=3, help="지출 상위 카테고리 개수 (기본값: 3)")

    # [명령어 5] budget (set 서브커맨드 포함)
    parser_budget = subparsers.add_parser("budget", help="월별 예산을 설정합니다")
    budget_subs = parser_budget.add_subparsers(dest="subcommand")
    budget_set = budget_subs.add_parser("set", help="월 예산을 등록합니다")
    budget_set.add_argument("--month", help="예산 월 (YYYY-MM)")
    budget_set.add_argument("--amount", type=int, help="예산 금액")

    # [명령어 6] category (add/list/remove 서브커맨드 포함)
    parser_category = subparsers.add_parser("category", help="카테고리를 관리합니다")
    category_subs = parser_category.add_subparsers(dest="subcommand")
    category_subs.add_parser("list", help="카테고리 목록을 조회합니다")
    category_add = category_subs.add_parser("add", help="새 카테고리를 추가합니다")
    category_add.add_argument("name", nargs="?", help="추가할 카테고리명")
    category_remove = category_subs.add_parser("remove", help="기존 카테고리를 삭제합니다")
    category_remove.add_argument("name", nargs="?", help="삭제할 카테고리명")

    # [명령어 7] update
    parser_update = subparsers.add_parser("update", help="기존 거래 내역을 수정합니다 (대화형)")
    parser_update.add_argument("--id", help="수정할 거래 ID")

    # [명령어 8] delete
    parser_delete = subparsers.add_parser("delete", help="특정 거래 내역을 삭제합니다")
    parser_delete.add_argument("--id", help="삭제할 거래 ID")

    # [명령어 9] import
    parser_import = subparsers.add_parser("import", help="CSV 파일에서 거래를 일괄 등록합니다")
    parser_import.add_argument("--from", dest="filepath", help="가져올 CSV 파일 경로")

    # [명령어 10] export
    parser_export = subparsers.add_parser("export", help="조건에 맞는 거래를 CSV로 내보냅니다")
    parser_export.add_argument("--out", help="저장할 CSV 파일 경로")
    parser_export.add_argument("--month", help="내보낼 월 (YYYY-MM)")
    parser_export.add_argument("--from", dest="from_date", help="시작 날짜 (YYYY-MM-DD)")
    parser_export.add_argument("--to", dest="to_date", help="종료 날짜 (YYYY-MM-DD)")

    # [보너스 1] backup
    parser_backup = subparsers.add_parser("backup", help="가계부 데이터를 zip 파일로 백업합니다")

    # [보너스 2] recurring (add/list/generate 서브커맨드 포함)
    parser_recurring = subparsers.add_parser("recurring", help="정기 반복 내역을 관리합니다")
    recurring_subs = parser_recurring.add_subparsers(dest="subcommand")
    recurring_subs.add_parser("list", help="반복 내역 목록을 조회합니다")
    recurring_subs.add_parser("add", help="반복 내역을 등록합니다")
    recurring_gen = recurring_subs.add_parser("generate", help="특정 월에 반복 내역을 일괄 자동 생성합니다")
    recurring_gen.add_argument("--month", help="생성할 월 (YYYY-MM)")


    # 3. 인자 파싱
    args = parser.parse_args()

    # 4. 의존성 주입 및 실행
    try:
        repo = FileRepository(data_dir=args.data_dir)
        service = BudgetService(repository=repo)
        shell = InteractiveShell(service=service)
    except Exception as e:
        print(f"[오류] 초기 구동 실패: {e}", file=sys.stderr)
        print("[힌트] 데이터 저장 경로의 읽기/쓰기 권한을 확인해 주세요.", file=sys.stderr)
        sys.exit(1)

    if args.command:
        shell.execute_command(args.command, args)
    else:
        shell.run()

if __name__ == "__main__":
    main()
                                                                 # 메인 함수 구동
