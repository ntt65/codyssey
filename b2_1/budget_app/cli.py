import sys
import argparse
import unicodedata
from typing import List, Callable, Tuple, Optional
from budget_app.models import Transaction, RecurringTemplate
from budget_app.repository import FileRepository
from budget_app.service import BudgetService
from budget_app.decorators import catch_errors, measure_time, log_action

# --- Formatting Helpers ---

def visual_len(s: str) -> int:
    """Calculates the visual width of a string (taking double-width East Asian characters into account)."""
    width = 0
    for char in s:
        if unicodedata.east_asian_width(char) in ('W', 'F', 'A'):
            width += 2
        else:
            width += 1
    return width

def pad_string(s: str, width: int) -> str:
    """Pads string with trailing spaces to match the visual length."""
    cur_width = visual_len(s)
    if cur_width >= width:
        return s
    return s + " " * (width - cur_width)

def print_aligned_rows(headers: List[str], rows: List[List[str]]):
    """Prints rows aligned in columns separated by '|' using their visual lengths."""
    if not rows:
        return
    
    # Compute maximum width for each column
    col_count = len(headers)
    max_widths = [visual_len(h) for h in headers]
    for row in rows:
        for i in range(min(col_count, len(row))):
            max_widths[i] = max(max_widths[i], visual_len(row[i]))

    # Print rows formatted with calculated widths
    for row in rows:
        formatted_row = []
        for i, val in enumerate(row):
            formatted_row.append(pad_string(val, max_widths[i]))
        print(" | ".join(formatted_row))

# --- Interactive Prompts ---

def prompt_validated_input(prompt_text: str, validator: Callable[[str], Tuple[bool, str, str]]) -> str:
    while True:
        val = input(prompt_text).strip()
        is_valid, err, hint = validator(val)
        if is_valid:
            return val
        print(f"[오류] {err}")
        if hint:
            print(f"[힌트] {hint}")

def prompt_update_input(prompt_text: str, current_value: str, validator: Callable[[str], Tuple[bool, str, str]]) -> str:
    while True:
        val = input(f"{prompt_text} [{current_value}]: ").strip()
        if not val:
            return current_value
        is_valid, err, hint = validator(val)
        if is_valid:
            return val
        print(f"[오류] {err}")
        if hint:
            print(f"[힌트] {hint}")

# --- Individual Field Validators ---

def validate_date(val: str) -> Tuple[bool, str, str]:
    import datetime
    if not val:
        return False, "날짜를 입력해야 합니다.", "예: 2024-01-15"
    try:
        datetime.datetime.strptime(val, "%Y-%m-%d")
        return True, "", ""
    except ValueError:
        return False, "날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).", "예: 2024-01-15"

def validate_type(val: str) -> Tuple[bool, str, str]:
    if val not in ["income", "expense"]:
        return False, "허용되지 않은 타입입니다.", "income 또는 expense 중 입력해 주세요."
    return True, "", ""

def validate_amount(val: str) -> Tuple[bool, str, str]:
    try:
        num = int(val)
        if num <= 0:
            return False, "금액은 0보다 큰 양수여야 합니다.", "예: 15000"
        return True, "", ""
    except ValueError:
        return False, "금액은 숫자 형식이어야 합니다.", "예: 15000"

def validate_day(val: str) -> Tuple[bool, str, str]:
    try:
        num = int(val)
        if num < 1 or num > 31:
            return False, "일자(day)는 1에서 31 사이의 정수여야 합니다.", "예: 25"
        return True, "", ""
    except ValueError:
        return False, "일자(day)는 정수여야 합니다.", "예: 25"

def get_category_interactive(service: BudgetService, current_val: Optional[str] = None) -> str:
    categories = service.list_categories()
    prompt_text = "카테고리: " if current_val is None else f"카테고리 [{current_val}]: "
    
    while True:
        val = input(prompt_text).strip()
        if not val:
            if current_val is not None:
                return current_val
            print("[오류] 카테고리를 입력해야 합니다.")
            print(f"[힌트] 등록된 카테고리 목록: {', '.join(categories)}")
            continue
            
        if val in categories:
            return val
            
        print(f"[오류] 존재하지 않는 카테고리입니다: '{val}'")
        print(f"[힌트] 등록된 카테고리 목록: {', '.join(categories)}")
        ans = input(f"       '{val}' 카테고리를 새로 추가하고 진행하시겠습니까? (y/n): ").strip().lower()
        if ans in ['y', 'yes', '예']:
            service.add_category(val)
            print(f"[저장 완료] category={val}")
            return val
        else:
            print("[정보] 카테고리를 다시 입력하거나 새로 추가해 주세요.")

# --- Action Implementations ---

def handle_add(service: BudgetService):
    date = prompt_validated_input("날짜(YYYY-MM-DD): ", validate_date)
    type_str = prompt_validated_input("타입(income/expense): ", validate_type)
    category = get_category_interactive(service)
    amount = int(prompt_validated_input("금액(양수): ", validate_amount))
    
    memo = input("메모(선택): ").strip()
    tags_input = input("태그(쉼표로 구분, 없으면 엔터): ").strip()
    tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []
    
    tx_id = service.add_transaction(date, type_str, category, amount, memo, tags)
    print(f"[저장 완료] id={tx_id}")

def handle_list(service: BudgetService, limit: int):
    txs = service.list_transactions(limit)
    if not txs:
        print("거래 내역이 없습니다.")
        return
        
    headers = ["id", "date", "type", "category", "amount", "memo", "tags"]
    rows = []
    for tx in txs:
        tags_str = ",".join(tx.tags) if tx.tags else ""
        rows.append([
            tx.id,
            tx.date,
            tx.type,
            tx.category,
            str(tx.amount),
            tx.memo,
            tags_str
        ])
    print_aligned_rows(headers, rows)

def handle_search(service: BudgetService, args):
    txs = service.search_transactions(
        from_date=args.from_date,
        to_date=args.to_date,
        category=args.category,
        type_str=args.type,
        query=args.query,
        tag=args.tag,
        limit=50
    )
    if not txs:
        print("검색 조건에 맞는 거래 내역이 없습니다.")
        return
        
    headers = ["id", "date", "type", "category", "amount", "memo", "tags"]
    rows = []
    for tx in txs:
        tags_str = ",".join(tx.tags) if tx.tags else ""
        rows.append([
            tx.id,
            tx.date,
            tx.type,
            tx.category,
            str(tx.amount),
            tx.memo,
            tags_str
        ])
    print_aligned_rows(headers, rows)

def handle_summary(service: BudgetService, month: str, top_n: int):
    summary = service.get_monthly_summary(month, top_n)
    if not summary["has_data"]:
        print("데이터 없음")
        return
        
    print(f"총 수입: {summary['total_income']}원")
    print(f"총 지출: {summary['total_expense']}원")
    print(f"잔액: {summary['balance']}원")
    
    budget = summary["budget"]
    if budget is not None:
        usage_rate = (summary["total_expense"] / budget) * 100 if budget > 0 else 0
        print(f"예산: {budget}원 (사용률 {usage_rate:.1f}%)")
        if summary["total_expense"] > budget:
            over = summary["total_expense"] - budget
            print(f"[경고] 이번 달 예산을 {over}원 초과했습니다!")
    
    print(f"\n지출 TOP {top_n}")
    for idx, (cat, amt) in enumerate(summary["top_categories"], 1):
        print(f"{idx}) {cat} {amt}원")

def handle_budget_set(service: BudgetService, month: str, amount: int):
    service.set_budget(month, amount)
    print(f"[저장 완료] {month} 예산 {amount}원")

def handle_category(service: BudgetService, action: str):
    if action == "list":
        categories = service.list_categories()
        for cat in categories:
            print(f"- {cat}")
    elif action == "add":
        name = input("카테고리명: ").strip()
        if not name:
            print("[오류] 카테고리명을 입력해야 합니다.")
            return
        service.add_category(name)
        print(f"[저장 완료] category={name}")
    elif action == "remove":
        categories = service.list_categories()
        print(f"등록된 카테고리 목록: {', '.join(categories)}")
        name = input("삭제할 카테고리명: ").strip()
        if not name:
            print("[오류] 카테고리명을 입력해야 합니다.")
            return
        service.remove_category(name)
        print(f"[삭제 완료] category={name}")
    else:
        print("[오류] 잘못된 카테고리 작업입니다. (add/list/remove 중 선택)")

def handle_update(service: BudgetService, tx_id: str):
    # Find existing transaction
    txs = service.search_transactions(limit=1)
    # Stream transactions to find the target transaction
    target_tx = None
    for tx in service.repository.stream_transactions():
        if tx.id == tx_id:
            target_tx = tx
            break
            
    if not target_tx:
        print(f"[오류] 없는 데이터: ID가 '{tx_id}'인 거래를 찾을 수 없습니다.")
        print("[힌트] ID를 확인하거나 list 명령으로 올바른 ID를 검색해 주세요.")
        sys.exit(4)
        
    date = prompt_update_input("날짜(YYYY-MM-DD)", target_tx.date, validate_date)
    type_str = prompt_update_input("타입(income/expense)", target_tx.type, validate_type)
    category = get_category_interactive(service, target_tx.category)
    amount = int(prompt_update_input("금액(양수)", str(target_tx.amount), validate_amount))
    
    memo = input(f"메모(선택) [{target_tx.memo}]: ").strip()
    if not memo:
        memo = target_tx.memo
        
    curr_tags_str = ",".join(target_tx.tags) if target_tx.tags else ""
    tags_input = input(f"태그(쉼표로 구분, 없으면 엔터) [{curr_tags_str}]: ").strip()
    if not tags_input and tags_input != "":
        tags = target_tx.tags
    else:
        tags = [t.strip() for t in tags_input.split(",") if t.strip()]
        
    success = service.update_transaction(tx_id, date, type_str, category, amount, memo, tags)
    if success:
        print(f"[수정 성공] id={tx_id}")
    else:
        print(f"[수정 실패] id={tx_id} 를 찾을 수 없거나 반영되지 못했습니다.")

def handle_delete(service: BudgetService, tx_id: str):
    success = service.delete_transaction(tx_id)
    if success:
        print(f"[삭제 성공] id={tx_id}")
    else:
        print(f"[삭제 실패] 없는 데이터: ID가 '{tx_id}'인 거래를 찾을 수 없습니다.")
        print("[힌트] ID를 확인해 주십시오.")
        sys.exit(4)

def handle_import(service: BudgetService, filepath: str):
    imported, skipped = service.import_from_csv(filepath)
    print(f"[완료] imported={imported}, skipped={skipped}")

def handle_export(service: BudgetService, args):
    count = service.export_to_csv(
        filepath=args.out,
        month=args.month,
        from_date=args.from_date,
        to_date=args.to_date
    )
    print(f"[완료] {args.out} ({count} records)")

def handle_backup(service: BudgetService):
    backup_path = service.create_backup()
    print(f"[백업 완료] 백업 파일: {backup_path}")

def handle_recurring(service: BudgetService, action: str, args):
    if action == "list":
        templates = service.load_recurring_templates()
        if not templates:
            print("등록된 반복 내역이 없습니다.")
            return
        headers = ["id", "type", "category", "amount", "day", "memo", "tags"]
        rows = []
        for t in templates:
            tags_str = ",".join(t.tags) if t.tags else ""
            rows.append([
                t.id,
                t.type,
                t.category,
                str(t.amount),
                f"매월 {t.day}일",
                t.memo,
                tags_str
            ])
        print_aligned_rows(headers, rows)
    elif action == "add":
        type_str = prompt_validated_input("타입(income/expense): ", validate_type)
        category = get_category_interactive(service)
        amount = int(prompt_validated_input("금액(양수): ", validate_amount))
        day = int(prompt_validated_input("매월 반복 일자(1-31): ", validate_day))
        memo = input("메모(선택): ").strip()
        tags_input = input("태그(쉼표로 구분, 없으면 엔터): ").strip()
        tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []
        
        new_id = service.add_recurring_template(type_str, category, amount, day, memo, tags)
        print(f"[저장 완료] template_id={new_id}")
    elif action == "remove":
        success = service.remove_recurring_template(args.id)
        if success:
            print(f"[삭제 성공] template_id={args.id}")
        else:
            print(f"[삭제 실패] template_id={args.id} 를 찾을 수 없습니다.")
    elif action == "generate":
        count = service.generate_recurring_transactions(args.month)
        print(f"[생성 완료] {args.month}에 {count}건의 반복 거래 내역을 등록하였습니다.")
    else:
        print("[오류] 올바르지 않은 recurring 명령입니다. (add/list/remove/generate 중 선택)")

# --- Main CLI parsing ---

@catch_errors
def main():
    parser = argparse.ArgumentParser(
        description="파일 기반 가계부 콘솔 프로그램 (budget_app)",
        add_help=True
    )
    # Global options
    parser.add_argument(
        "--data-dir",
        default="./data",
        help="데이터 저장 폴더 경로 (기본값: ./data)"
    )

    subparsers = parser.add_subparsers(dest="command", help="실행할 명령")

    # add
    subparsers.add_parser("add", help="새 거래 내역 추가 (대화형)")

    # list
    list_parser = subparsers.add_parser("list", help="거래 내역 목록 조회")
    list_parser.add_argument("--limit", type=int, default=20, help="조회할 최대 거래 개수 (기본값: 20)")

    # search
    search_parser = subparsers.add_parser("search", help="조건별 거래 내역 검색")
    search_parser.add_argument("--from", dest="from_date", help="검색 시작일 (YYYY-MM-DD)")
    search_parser.add_argument("--to", dest="to_date", help="검색 종료일 (YYYY-MM-DD)")
    search_parser.add_argument("--category", help="검색 카테고리")
    search_parser.add_argument("--type", choices=["income", "expense"], help="검색 타입")
    search_parser.add_argument("-q", dest="query", help="메모 검색어")
    search_parser.add_argument("--tag", help="검색 태그")

    # summary
    summary_parser = subparsers.add_parser("summary", help="월별 요약 조회")
    summary_parser.add_argument("--month", required=True, help="조회 월 (YYYY-MM)")
    summary_parser.add_argument("--top", type=int, default=3, help="상위 지출 카테고리 수 (기본값: 3)")

    # budget
    budget_parser = subparsers.add_parser("budget", help="예산 설정")
    budget_sub = budget_parser.add_subparsers(dest="budget_action")
    budget_set = budget_sub.add_parser("set", help="월별 예산 설정")
    budget_set.add_argument("--month", required=True, help="예산 적용 월 (YYYY-MM)")
    budget_set.add_argument("--amount", type=int, required=True, help="예산 금액")

    # category
    category_parser = subparsers.add_parser("category", help="카테고리 관리")
    category_parser.add_argument("category_action", choices=["add", "list", "remove"], help="카테고리 동작")

    # update
    update_parser = subparsers.add_parser("update", help="거래 내역 수정 (대화형)")
    update_parser.add_argument("--id", required=True, help="수정할 거래 ID")

    # delete
    delete_parser = subparsers.add_parser("delete", help="거래 내역 삭제")
    delete_parser.add_argument("--id", required=True, help="삭제할 거래 ID")

    # import
    import_parser = subparsers.add_parser("import", help="CSV 파일에서 거래 가져오기")
    import_parser.add_argument("--from", dest="filepath", required=True, help="가져올 CSV 파일 경로")

    # export
    export_parser = subparsers.add_parser("export", help="거래 내역을 CSV 파일로 내보내기")
    export_parser.add_argument("--out", required=True, help="내보낼 CSV 파일 경로")
    export_parser.add_argument("--month", help="내보낼 월 (YYYY-MM)")
    export_parser.add_argument("--from", dest="from_date", help="내보낼 시작일 (YYYY-MM-DD)")
    export_parser.add_argument("--to", dest="to_date", help="내보낼 종료일 (YYYY-MM-DD)")

    # backup
    subparsers.add_parser("backup", help="데이터 백업 생성 (Zip 포맷)")

    # recurring
    recurring_parser = subparsers.add_parser("recurring", help="매월 반복 내역 관리")
    recurring_parser.add_argument("recurring_action", choices=["add", "list", "remove", "generate"], help="반복 내역 동작")
    recurring_parser.add_argument("--id", help="삭제할 반복 내역 ID (remove 시 필수)")
    recurring_parser.add_argument("--month", help="반복 내역을 생성할 대상 월 (generate 시 필수, YYYY-MM)")

    # If no arguments are passed, show help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    # We need to preprocess args to allow option parsing because --from matches --from-date or argparse dest='from'
    # Actually, argparse handles it, but let's parse
    args = parser.parse_args()

    # Initialize Repository and Service
    repo = FileRepository(args.data_dir)
    service = BudgetService(repo)

    # Route commands
    if args.command == "add":
        handle_add(service)
    elif args.command == "list":
        handle_list(service, args.limit)
    elif args.command == "search":
        handle_search(service, args)
    elif args.command == "summary":
        handle_summary(service, args.month, args.top)
    elif args.command == "budget":
        if args.budget_action == "set":
            handle_budget_set(service, args.month, args.amount)
        else:
            budget_parser.print_help()
    elif args.command == "category":
        handle_category(service, args.category_action)
    elif args.command == "update":
        handle_update(service, args.id)
    elif args.command == "delete":
        handle_delete(service, args.id)
    elif args.command == "import":
        handle_import(service, args.filepath)
    elif args.command == "export":
        handle_export(service, args)
    elif args.command == "backup":
        handle_backup(service)
    elif args.command == "recurring":
        if args.recurring_action == "remove" and not args.id:
            print("[오류] 삭제할 반복 내역의 ID가 필요합니다.")
            print("[힌트] --id <template_id> 옵션을 지정해 주세요.")
            sys.exit(1)
        if args.recurring_action == "generate" and not args.month:
            print("[오류] 반복 내역을 생성할 월이 필요합니다.")
            print("[힌트] --month YYYY-MM 옵션을 지정해 주세요.")
            sys.exit(1)
        handle_recurring(service, args.recurring_action, args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
