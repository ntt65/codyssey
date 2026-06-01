import sys
import datetime
import unicodedata
import ctypes
import ctypes.util
from typing import List, Callable, Tuple, Optional

# Attempt to load readline for autocomplete
try:
    import readline
except ImportError:
    readline = None

from budget_app.models import Transaction, RecurringTemplate
from budget_app.service import BudgetService
from budget_app.repository import FileRepository
from budget_app.decorators import catch_errors, measure_time, log_action

# --- macOS Input Method (IME) Auto Switcher ---

def switch_to_english():
    """
    Programmatically switches the macOS input source to English (US).
    Uses ctypes to load CoreFoundation and Carbon frameworks to bypass pyobjc dependency.
    """
    try:
        cf_path = ctypes.util.find_library('CoreFoundation')
        if not cf_path:
            return False
        cf = ctypes.cdll.LoadLibrary(cf_path)
        
        carbon_path = ctypes.util.find_library('Carbon')
        if not carbon_path:
            return False
        carbon = ctypes.cdll.LoadLibrary(carbon_path)

        cf.CFStringCreateWithCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32]
        cf.CFStringCreateWithCString.restype = ctypes.c_void_p

        cf.CFRelease.argtypes = [ctypes.c_void_p]
        cf.CFRelease.restype = None

        carbon.TISCopyInputSourceForLanguage.argtypes = [ctypes.c_void_p]
        carbon.TISCopyInputSourceForLanguage.restype = ctypes.c_void_p

        carbon.TISSelectInputSource.argtypes = [ctypes.c_void_p]
        carbon.TISSelectInputSource.restype = ctypes.c_int32

        # kCFStringEncodingUTF8 = 0x08000100
        utf8_str = cf.CFStringCreateWithCString(None, b"en", 0x08000100)
        if not utf8_str:
            return False

        source = carbon.TISCopyInputSourceForLanguage(utf8_str)
        cf.CFRelease(utf8_str)

        if not source:
            return False

        status = carbon.TISSelectInputSource(source)
        cf.CFRelease(source)
        return status == 0
    except Exception:
        return False

# --- Auto-Complete (Readline) for Command Prompt ---

class CommandCompleter:
    def __init__(self, commands: List[str]):
        self.commands = commands

    def complete(self, text: str, state: int) -> Optional[str]:
        matches = [cmd for cmd in self.commands if cmd.lower().startswith(text.lower())]
        if state < len(matches):
            return matches[state]
        return None

# --- Raw Terminal Choice Prompt ---

def prompt_choices(prompt_text: str, choices: List[str], default_value: Optional[str] = None) -> str:
    """
    Prompts the user interactively with choices shown as (Item1 /Item2 /Item3 ).
    Captures character-by-character input to:
      1. Cycle through choices using Up/Down and Left/Right arrow keys in order.
      2. Autocomplete first-letter matches using Tab.
      3. Accept input via Enter.
      4. Fallback to normal input if tty/termios is unavailable (e.g. testing).
    """
    switch_to_english()
    
    # If no choices, fallback to standard input
    if not choices:
        prompt_suffix = f" [{default_value}]: " if default_value else ": "
        return input(prompt_text + prompt_suffix).strip()

    prompt_display = format_choices(choices)
    full_prompt = f"{prompt_text} {prompt_display}"
    if default_value:
        full_prompt += f" [{default_value}]"
    full_prompt += ": "

    # Verify if we can run in raw TTY mode
    if not sys.stdin.isatty():
        return input(full_prompt).strip()

    import tty
    import termios

    current_text = default_value if default_value else ""
    is_default_active = True if default_value else False
    current_index = -1

    sys.stdout.write(f"{full_prompt}{current_text}")
    sys.stdout.flush()

    def getch() -> str:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def get_key() -> str:
        ch = getch()
        if ch == '\x1b':
            ch2 = getch()
            if ch2 == '[':
                ch3 = getch()
                if ch3 == 'A': return 'up'
                elif ch3 == 'B': return 'down'
                elif ch3 == 'C': return 'right'
                elif ch3 == 'D': return 'left'
            return 'esc'
        elif ch == '\t': return 'tab'
        elif ch in ('\n', '\r'): return 'enter'
        elif ch in ('\x7f', '\x08'): return 'backspace'
        elif ch == '\x03': raise KeyboardInterrupt
        return ch

    def get_matches(text):
        return [c for c in choices if c.lower().startswith(text.lower())]

    while True:
        key = get_key()
        
        if key == 'enter':
            sys.stdout.write("\n")
            sys.stdout.flush()
            if not current_text and default_value:
                return default_value
            return current_text
            
        elif key == 'backspace':
            if is_default_active:
                current_text = ""
                is_default_active = False
            else:
                current_text = current_text[:-1]
            current_index = -1
            
        elif key == 'tab':
            if is_default_active:
                is_default_active = False
            elif not current_text and default_value:
                current_text = default_value
            else:
                m = get_matches(current_text)
                if m:
                    current_text = m[0]
                    current_index = choices.index(m[0])
                    
        elif key in ('down', 'right'):
            is_default_active = False
            matched_choice = None
            for c in choices:
                if c.lower() == current_text.lower():
                    matched_choice = c
                    break
            if matched_choice is not None:
                idx = choices.index(matched_choice)
                current_index = (idx + 1) % len(choices)
            else:
                m = get_matches(current_text)
                if m:
                    idx = choices.index(m[0])
                    current_index = idx
                else:
                    current_index = 0
            current_text = choices[current_index]
                
        elif key in ('up', 'left'):
            is_default_active = False
            matched_choice = None
            for c in choices:
                if c.lower() == current_text.lower():
                    matched_choice = c
                    break
            if matched_choice is not None:
                idx = choices.index(matched_choice)
                current_index = (idx - 1) % len(choices)
            else:
                m = get_matches(current_text)
                if m:
                    idx = choices.index(m[0])
                    current_index = (idx - 1) % len(choices)
                else:
                    current_index = len(choices) - 1
            current_text = choices[current_index]
                
        else:
            if len(key) == 1:
                if is_default_active:
                    current_text = key
                    is_default_active = False
                else:
                    current_text += key
                current_index = -1
                
        # Redraw
        sys.stdout.write(f"\r{full_prompt}{current_text}\x1b[K")
        sys.stdout.flush()

# --- Formatting Helpers ---

def format_choices(items: List[str]) -> str:
    """Formats list of choices to (Item1 /Item2 /Item3 ) style."""
    if not items:
        return ""
    return "(" + " /".join(items) + " )"

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
    
    col_count = len(headers)
    max_widths = [visual_len(h) for h in headers]
    for row in rows:
        for i in range(min(col_count, len(row))):
            max_widths[i] = max_widths[i], visual_len(row[i])
            # Max width logic check
            val_len = visual_len(row[i])
            if val_len > max_widths[i]:
                max_widths[i] = val_len

    # Print header line
    header_line = [pad_string(h, max_widths[i]) for i, h in enumerate(headers)]
    print(" | ".join(header_line))
    print("-+-".join("-" * w for w in max_widths))

    # Print rows
    for row in rows:
        formatted_row = []
        for i, val in enumerate(row):
            formatted_row.append(pad_string(val, max_widths[i]))
        print(" | ".join(formatted_row))

# --- Input Field Validators ---

def validate_date(val: str) -> Tuple[bool, str, str]:
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

def validate_month(val: str) -> Tuple[bool, str, str]:
    try:
        datetime.datetime.strptime(val, "%Y-%m")
        return True, "", ""
    except ValueError:
        return False, "월 형식이 올바르지 않습니다 (YYYY-MM).", "예: 2024-01"

def validate_yes_no(val: str) -> Tuple[bool, str, str]:
    if val.lower() not in ["y", "yes", "예", "n", "no", "아니오"]:
        return False, "y 또는 n을 입력해 주세요.", "예: y"
    return True, "", ""

# --- Argument Extraction Helpers ---

def get_id_from_args(args: List[str], prefix: str = "TX-") -> Optional[str]:
    if not args:
        return None
    if "--id" in args:
        idx = args.index("--id")
        if idx + 1 < len(args):
            return args[idx + 1]
    for arg in args:
        if arg.startswith(prefix):
            return arg
    return args[0]

def get_filepath_from_args(args: List[str], flag: str = "--from") -> Optional[str]:
    if not args:
        return None
    if flag in args:
        idx = args.index(flag)
        if idx + 1 < len(args):
            return args[idx + 1]
    filtered = [arg for arg in args if not arg.startswith("-")]
    return filtered[0] if filtered else args[0]

# --- Interactive Shell Class ---

class InteractiveShell:
    def __init__(self, service: BudgetService):
        self.service = service
        self.commands = [
            "help", "add", "list", "search", "summary", "budget", 
            "category", "update", "delete", "import", "export", 
            "backup", "recurring", "exit", "quit"
        ]
        # Setup command completer for main prompt
        if readline:
            self.completer = CommandCompleter(self.commands)
            readline.set_completer(self.completer.complete)
            if 'libedit' in readline.__doc__:
                readline.parse_and_bind("bind -e")
                readline.parse_and_bind("bind ^I rl_complete")
            else:
                readline.parse_and_bind("tab: complete")

    def prompt_main_command(self, prompt_text: str) -> str:
        """
        Interactive main command prompt using raw terminal keys.
        Up/Down arrow keys navigate command history.
        Left/Right arrow keys cycle through commands.
        Tab completes command matching the prefix.
        Enter accepts input.
        """
        if not sys.stdin.isatty():
            return input(prompt_text).strip()

        import tty
        import termios

        sys.stdout.write(prompt_text)
        sys.stdout.flush()

        current_text = ""
        history_index = len(self.history)
        temp_draft = ""
        choices = self.commands

        def getch() -> str:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch

        def get_key() -> str:
            ch = getch()
            if ch == '\x1b':
                ch2 = getch()
                if ch2 == '[':
                    ch3 = getch()
                    if ch3 == 'A': return 'up'
                    elif ch3 == 'B': return 'down'
                    elif ch3 == 'C': return 'right'
                    elif ch3 == 'D': return 'left'
                return 'esc'
            elif ch == '\t': return 'tab'
            elif ch in ('\n', '\r'): return 'enter'
            elif ch in ('\x7f', '\x08'): return 'backspace'
            elif ch == '\x03': raise KeyboardInterrupt
            return ch

        def get_matches(text):
            if not text:
                return choices
            return [c for c in choices if c.lower().startswith(text.lower())]

        while True:
            key = get_key()

            if key == 'enter':
                sys.stdout.write("\n")
                sys.stdout.flush()
                res = current_text.strip()
                if res:
                    if not self.history or self.history[-1] != res:
                        self.history.append(res)
                        if readline:
                            readline.add_history(res)
                return res

            elif key == 'backspace':
                current_text = current_text[:-1]
                history_index = len(self.history)
                temp_draft = current_text

            elif key == 'tab':
                parts = current_text.split()
                if not parts:
                    current_text = choices[0]
                else:
                    cmd_part = parts[0]
                    m = get_matches(cmd_part)
                    if m:
                        parts[0] = m[0]
                        current_text = " ".join(parts)
                history_index = len(self.history)
                temp_draft = current_text

            elif key in ('down', 'up'):
                if key == 'up':
                    if len(self.history) > 0 and history_index > 0:
                        if history_index == len(self.history):
                            temp_draft = current_text
                        history_index -= 1
                        current_text = self.history[history_index]
                elif key == 'down':
                    if history_index < len(self.history):
                        history_index += 1
                        if history_index == len(self.history):
                            current_text = temp_draft
                        else:
                            current_text = self.history[history_index]

            elif key in ('right', 'left'):
                parts = current_text.split()
                cmd_part = parts[0] if parts else ""
                
                matched_choice = None
                for c in choices:
                    if c.lower() == cmd_part.lower():
                        matched_choice = c
                        break
                
                if matched_choice is not None:
                    idx = choices.index(matched_choice)
                    if key == 'right':
                        next_idx = (idx + 1) % len(choices)
                    else:
                        next_idx = (idx - 1) % len(choices)
                    new_cmd = choices[next_idx]
                else:
                    m = get_matches(cmd_part)
                    if m:
                        idx = choices.index(m[0])
                        if key == 'right':
                            new_cmd = choices[idx]
                        else:
                            new_cmd = choices[(idx - 1) % len(choices)]
                    else:
                        if key == 'right':
                            new_cmd = choices[0]
                        else:
                            new_cmd = choices[-1]
                
                if not parts:
                    current_text = new_cmd
                else:
                    parts[0] = new_cmd
                    current_text = " ".join(parts)
                
                history_index = len(self.history)
                temp_draft = current_text

            else:
                if len(key) == 1:
                    current_text += key
                    history_index = len(self.history)
                    temp_draft = current_text

            sys.stdout.write(f"\r{prompt_text}{current_text}\x1b[K")
            sys.stdout.flush()

    def run(self):
        print("==================================================")
        print("   💰 대화형 파일 기반 가계부 (budget_app) v1.0 💰")
        print("   - 사용법 확인: help 입력")
        print("   - 프로그램 종료: exit 또는 quit 입력")
        print("==================================================")
        
        self.history = []
        if readline:
            history_len = readline.get_current_history_length()
            for i in range(1, history_len + 1):
                item = readline.get_history_item(i)
                if item:
                    self.history.append(item)
                    
        while True:
            try:
                # Force macOS input source to English (US)
                switch_to_english()
                
                user_input = self.prompt_main_command("budget_app> ").strip()
                if not user_input:
                    continue
                
                parts = user_input.split()
                command = parts[0].lower()
                args = parts[1:]
                
                if command in ["exit", "quit"]:
                    print("==================================================")
                    print("   이용해 주셔서 감사합니다. 가계부를 종료합니다! ")
                    print("==================================================")
                    break
                
                self.parse_and_execute(command, args)
                
            except KeyboardInterrupt:
                print("\n[정보] 입력이 취소되었습니다. 대기 상태로 복귀합니다.")
            except EOFError:
                print("\n==================================================")
                print("   이용해 주셔서 감사합니다. 가계부를 종료합니다! ")
                print("==================================================")
                break

    def parse_and_execute(self, command: str, args: List[str]):
        if command == "help":
            self.handle_help()
        elif command == "add":
            self.handle_add()
        elif command == "list":
            self.handle_list(args)
        elif command == "search":
            self.handle_search()
        elif command == "summary":
            self.handle_summary(args)
        elif command == "budget":
            self.handle_budget()
        elif command == "category":
            self.handle_category()
        elif command == "update":
            self.handle_update(args)
        elif command == "delete":
            self.handle_delete(args)
        elif command == "import":
            self.handle_import(args)
        elif command == "export":
            self.handle_export(args)
        elif command == "backup":
            self.handle_backup()
        elif command == "recurring":
            self.handle_recurring()
        else:
            print(f"[오류] 알 수 없는 명령어입니다: '{command}'")
            print("[힌트] 전체 명령어 목록을 확인하려면 'help'를 입력해 주세요.")

    # --- Suggestion Generator Helpers ---

    def get_all_transaction_ids(self) -> List[str]:
        ids = []
        for tx in self.service.repository.stream_transactions():
            ids.append(tx.id)
        ids.reverse()
        return ids

    def get_all_recurring_ids(self) -> List[str]:
        templates = self.service.load_recurring_templates()
        return [t.id for t in templates]

    # --- Universal Prompt Helpers ---

    def prompt_validated_input(self, prompt_text: str, validator: Callable[[str], Tuple[bool, str, str]], default_value: Optional[str] = None, suggestions: Optional[List[str]] = None) -> str:
        while True:
            val = prompt_choices(prompt_text, suggestions or [], default_value)
            is_valid, err, hint = validator(val)
            if is_valid:
                return val
            print(f"[오류] {err}")
            if hint:
                print(f"[힌트] {hint}")

    def prompt_category_interactive(self, current_val: Optional[str] = None) -> str:
        categories = self.service.list_categories()
        prompt_text = "- 카테고리"
        
        while True:
            val = prompt_choices(prompt_text, categories, current_val)
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
            ans = self.prompt_validated_input(f"       '{val}' 카테고리를 가계부에 새로 추가하고 진행하시겠습니까?", validate_yes_no, None, ["y", "n"])
            if ans.lower() in ['y', 'yes', '예']:
                self.service.add_category(val)
                print(f"[저장 완료] category={val}")
                return val

    # --- CLI Command Handlers ---

    def handle_help(self):
        print("\n[ 사용 가능한 명령어 목록 ]")
        print("--------------------------------------------------------------------------------")
        headers = ["명령어", "인자 형태", "한글 기능 설명"]
        rows = [
            ["help", "없음", "도움말 및 명령어 안내를 출력합니다."],
            ["add", "없음", "새로운 수입/지출 내역을 입력 루프로 등록합니다."],
            ["list", "[limit]", "최신 가계부 내역을 정렬 표 형식으로 출력합니다."],
            ["search", "없음", "조건별(기간, 카테고리 등) 대화형 검색을 수행합니다."],
            ["summary", "[YYYY-MM]", "지정한 월의 수지 통계 및 예산 소모를 분석합니다."],
            ["budget", "없음", "특정 월의 소비 한도 예산을 입력 설정합니다."],
            ["category", "없음", "카테고리 조회/추가/삭제 서브 메뉴로 진입합니다."],
            ["update", "[--id ID]", "특정 ID 거래 건을 대화식으로 수정합니다."],
            ["delete", "[--id ID]", "특정 ID 거래 건을 확인 절차를 거쳐 삭제합니다."],
            ["import", "[--from 파일]", "CSV 파일에서 데이터를 가계부로 가져옵니다."],
            ["export", "[--out 파일]", "조건에 맞는 가계부 데이터를 CSV로 추출합니다."],
            ["backup", "없음", "데이터베이스 전체를 zip 파일로 일괄 백업합니다."],
            ["recurring", "없음", "반복 거래(고정비) 템플릿 관리 및 생성으로 진입합니다."],
            ["exit / quit", "없음", "프로그램을 안전하게 세이브하고 종료합니다."]
        ]
        print_aligned_rows(headers, rows)
        print("--------------------------------------------------------------------------------\n")

    @catch_errors
    def handle_add(self):
        print("[새 거래 추가를 시작합니다]")
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        
        date = self.prompt_validated_input("- 날짜 (YYYY-MM-DD)", validate_date, today_str, [today_str])
        type_str = self.prompt_validated_input("- 타입", validate_type, None, ["income", "expense"])
        category = self.prompt_category_interactive()
        amount = int(self.prompt_validated_input("- 금액", validate_amount, None, ["10000", "30000", "50000"]))
        
        memo = self.prompt_validated_input("- 메모 (선택)", lambda x: (True, "", ""), "", ["점심", "저녁", "월세", "마트"])
        tags_input = self.prompt_validated_input("- 태그 (선택)", lambda x: (True, "", ""), "", ["식대", "생필품", "고정비", "교통"])
        tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []
        
        tx_id = self.service.add_transaction(date, type_str, category, amount, memo, tags)
        print(f"[저장 완료] id={tx_id}")

    @catch_errors
    def handle_list(self, args: List[str]):
        limit = 20
        if args:
            try:
                limit = int(args[0])
                if limit <= 0:
                    raise ValueError
            except ValueError:
                print("[오류] limit 개수는 양의 정수여야 합니다.")
                print("[힌트] 예: list 5")
                return

        txs = self.service.list_transactions(limit)
        if not txs:
            print("거래 내역이 없습니다.")
            return
            
        headers = ["id", "date", "type", "category", "amount", "memo", "tags"]
        rows = []
        for tx in txs:
            tags_str = ",".join(tx.tags) if tx.tags else ""
            rows.append([tx.id, tx.date, tx.type, tx.category, f"{tx.amount:,}원", tx.memo, tags_str])
        print_aligned_rows(headers, rows)

    @catch_errors
    def handle_search(self):
        print("[필터링 검색을 설정합니다. 건너뛰려면 엔터를 입력해 주세요]")
        categories = self.service.list_categories()
        
        from_date = self.prompt_validated_input("- 검색 시작일 (YYYY-MM-DD)", lambda x: (True, "", "") if not x else validate_date(x), "")
        to_date = self.prompt_validated_input("- 검색 종료일 (YYYY-MM-DD)", lambda x: (True, "", "") if not x else validate_date(x), "")
        type_str = self.prompt_validated_input("- 타입 필터", lambda x: (True, "", "") if not x else validate_type(x), "", ["income", "expense"])
        category = self.prompt_validated_input("- 카테고리 필터", lambda x: (True, "", "") if not x or x in categories else (False, f"존재하지 않는 카테고리: {x}", f"목록: {', '.join(categories)}"), "", categories)
        query = input("- 메모 검색어: ").strip()
        tag = self.prompt_validated_input("- 태그 필터", lambda x: (True, "", ""), "", ["식대", "생필품", "고정비", "교통"])

        txs = self.service.search_transactions(
            from_date=from_date if from_date else None,
            to_date=to_date if to_date else None,
            category=category if category else None,
            type_str=type_str if type_str else None,
            query=query if query else None,
            tag=tag if tag else None,
            limit=50
        )
        if not txs:
            print("검색 조건에 맞는 거래 내역이 없습니다.")
            return
            
        headers = ["id", "date", "type", "category", "amount", "memo", "tags"]
        rows = []
        for tx in txs:
            tags_str = ",".join(tx.tags) if tx.tags else ""
            rows.append([tx.id, tx.date, tx.type, tx.category, f"{tx.amount:,}원", tx.memo, tags_str])
        
        print("\n[검색 결과]")
        print_aligned_rows(headers, rows)

    @catch_errors
    def handle_summary(self, args: List[str]):
        month = ""
        if args:
            month = args[0]
            is_valid, err, hint = validate_month(month)
            if not is_valid:
                print(f"[오류] {err}")
                print(f"[힌트] {hint}")
                return
        else:
            this_month = datetime.date.today().strftime("%Y-%m")
            month = self.prompt_validated_input("- 요약할 대상 월 (YYYY-MM)", validate_month, this_month, [this_month])

        summary = self.service.get_monthly_summary(month, 3)
        if not summary["has_data"]:
            print("데이터 없음")
            return
            
        print("==================================================")
        print(f"   📊 {month} 재정 요약 리포트")
        print("==================================================")
        print(f"- 총 수입: {summary['total_income']:,}원")
        print(f"- 총 지출: {summary['total_expense']:,}원")
        print(f"- 잔액: {summary['balance']:,}원")
        
        budget = summary["budget"]
        if budget is not None:
            usage_rate = (summary["total_expense"] / budget) * 100 if budget > 0 else 0
            print(f"- 책정 예산: {budget:,}원 (사용률: {usage_rate:.1f}%)")
            if summary["total_expense"] > budget:
                over = summary["total_expense"] - budget
                print(f"⚠️ [경고] 이번 달 예산을 {over:,}원 초과해 지출했습니다!")
        
        print("\n[ 지출 TOP 3 카테고리 ]")
        total_exp = summary["total_expense"]
        for idx, (cat, amt) in enumerate(summary["top_categories"], 1):
            pct = (amt / total_exp) * 100 if total_exp > 0 else 0
            print(f"{idx}) {cat} : {amt:,}원 ({pct:.1f}%)")
        print("==================================================")

    @catch_errors
    def handle_budget(self):
        this_month = datetime.date.today().strftime("%Y-%m")
        month = self.prompt_validated_input("- 예산을 책정할 대상 월 (YYYY-MM)", validate_month, this_month, [this_month])
        amount = int(self.prompt_validated_input("- 한도 금액 (0 이상 정수)", validate_amount, None, ["500000", "1000000"]))
        
        self.service.set_budget(month, amount)
        print(f"[저장 완료] {month} 예산 {amount:,}원 설정 완료.")

    @catch_errors
    def handle_category(self):
        print("[카테고리 설정 관리]")
        print("1. 등록된 카테고리 목록 조회")
        print("2. 신규 카테고리 추가")
        print("3. 기존 카테고리 삭제")
        
        choice = self.prompt_validated_input("메뉴 선택", lambda x: (True, "", "") if x in ["1", "2", "3", ""] else (False, "1, 2, 3 중 선택해 주세요.", ""), "", ["1", "2", "3"])
        if not choice:
            return
            
        categories = self.service.list_categories()
        if choice == "1":
            for cat in categories:
                print(f"- {cat}")
        elif choice == "2":
            name = input("- 추가할 카테고리명: ").strip()
            if not name:
                print("[오류] 카테고리명을 입력해야 합니다.")
                return
            self.service.add_category(name)
            print(f"[저장 완료] category={name}")
        elif choice == "3":
            name = self.prompt_validated_input("- 삭제할 카테고리명", lambda x: (True, "", "") if x in categories else (False, "등록되지 않은 카테고리입니다.", ""), None, categories)
            if not name:
                return
            self.service.remove_category(name)
            print(f"[삭제 완료] 카테고리 '{name}'이 목록에서 안전하게 제거되었습니다.")

    @catch_errors
    def handle_update(self, args: List[str]):
        tx_id = get_id_from_args(args)
        existing_ids = self.get_all_transaction_ids()
        
        if not tx_id:
            tx_id = self.prompt_validated_input("- 수정할 거래 ID", lambda x: (True, "", "") if x in existing_ids else (False, "존재하지 않는 거래 ID입니다.", ""), None, existing_ids)
            if not tx_id:
                return

        # Find transaction
        target_tx = None
        for tx in self.service.repository.stream_transactions():
            if tx.id == tx_id:
                target_tx = tx
                break
                
        if not target_tx:
            print(f"[오류] 없는 데이터: ID가 '{tx_id}'인 거래를 찾을 수 없습니다.")
            return

        print("\n[기존 데이터를 로드했습니다. 수정을 원하지 않는 항목은 그대로 엔터를 누르세요]")
        
        date = self.prompt_validated_input("- 날짜 (YYYY-MM-DD)", validate_date, target_tx.date, [target_tx.date])
        type_str = self.prompt_validated_input("- 타입", validate_type, target_tx.type, ["income", "expense"])
        category = self.prompt_category_interactive(target_tx.category)
        amount = int(self.prompt_validated_input("- 금액 (양수)", validate_amount, str(target_tx.amount), [str(target_tx.amount)]))
        
        memo = self.prompt_validated_input("- 메모 (선택)", lambda x: (True, "", ""), target_tx.memo, ["점심", "저녁", "월세", "마트"])
        tags_input = self.prompt_validated_input("- 태그 (쉼표 구분)", lambda x: (True, "", ""), ",".join(target_tx.tags) if target_tx.tags else "", ["식대", "생필품", "고정비", "교통"])
        
        tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []

        success = self.service.update_transaction(tx_id, date, type_str, category, amount, memo, tags)
        if success:
            print(f"[수정 성공] id={tx_id}")
        else:
            print(f"[수정 실패] id={tx_id} 를 업데이트하지 못했습니다.")

    @catch_errors
    def handle_delete(self, args: List[str]):
        tx_id = get_id_from_args(args)
        existing_ids = self.get_all_transaction_ids()
        
        if not tx_id:
            tx_id = self.prompt_validated_input("- 삭제할 거래 ID", lambda x: (True, "", "") if x in existing_ids else (False, "존재하지 않는 거래 ID입니다.", ""), None, existing_ids)
            if not tx_id:
                return

        # Check existence
        found = False
        for tx in self.service.repository.stream_transactions():
            if tx.id == tx_id:
                found = True
                break
        if not found:
            print(f"[오류] 없는 데이터: ID가 '{tx_id}'인 거래를 찾을 수 없습니다.")
            return

        ans = self.prompt_validated_input(f"⚠️ 정말로 거래 ID '{tx_id}'를 영구 삭제하시겠습니까?", validate_yes_no, None, ["y", "n"])
        if ans.lower() in ['y', 'yes', '예']:
            success = self.service.delete_transaction(tx_id)
            if success:
                print(f"[삭제 성공] id={tx_id}")
            else:
                print(f"[삭제 실패] id={tx_id} 삭제 오류")
        else:
            print("[정보] 삭제가 취소되었습니다.")

    @catch_errors
    def handle_import(self, args: List[str]):
        filepath = get_filepath_from_args(args, "--from")
        if not filepath:
            import os
            csv_files = [f for f in os.listdir('.') if f.endswith('.csv') and os.path.isfile(f)]
            if csv_files:
                filepath = self.prompt_validated_input("- 가져올 CSV 파일 경로", lambda x: (True, "", "") if x else (False, "가져올 CSV 파일 경로가 필요합니다.", ""), None, csv_files)
            else:
                filepath = input("- 가져올 CSV 파일 경로 (예: data.csv): ").strip()
                if not filepath:
                    print("[오류] 가져올 CSV 파일 경로가 필요합니다.")
                    return

        print("[가져오기 진행 중...]")
        imported, skipped = self.service.import_from_csv(filepath)
        print(f"[완료] {filepath} 처리 완료 - 가져옴: {imported}건, 건너뜀(오류): {skipped}건")

    @catch_errors
    def handle_export(self, args: List[str]):
        filepath = get_filepath_from_args(args, "--out")
        if not filepath:
            filepath = self.prompt_validated_input("- 내보낼 CSV 파일 경로", lambda x: (True, "", "") if x else (False, "내보낼 CSV 파일 경로가 필요합니다.", ""), "backup.csv", ["backup.csv"])
            if not filepath:
                print("[오류] 내보낼 CSV 파일 경로가 필요합니다.")
                return

        choice = self.prompt_validated_input("- 필터 방식 선택", lambda x: (True, "", "") if x in ["1", "2", ""] else (False, "1 또는 2 중 선택해 주세요.", ""), "", ["1", "2"])
        
        month = None
        from_date = None
        to_date = None
        
        if choice == "1":
            this_month = datetime.date.today().strftime("%Y-%m")
            month = self.prompt_validated_input("내보낼 대상 월 (YYYY-MM)", validate_month, this_month, [this_month])
        elif choice == "2":
            from_date = self.prompt_validated_input("시작일 (YYYY-MM-DD)", validate_date)
            to_date = self.prompt_validated_input("종료일 (YYYY-MM-DD)", validate_date)
        
        print("[내보내기 진행 중...]")
        count = self.service.export_to_csv(filepath, month=month, from_date=from_date, to_date=to_date)
        print(f"[완료] {filepath} 파일로 {count}건의 기록을 성공적으로 추출 및 저장했습니다.")

    @catch_errors
    def handle_backup(self):
        print("[백업 진행 중...]")
        backup_path = self.service.create_backup()
        print(f"[백업 완료] 전체 데이터 백업이 안전하게 생성되었습니다: {backup_path}")

    @catch_errors
    def handle_recurring(self):
        print("[매월 반복 고정 거래 관리 메뉴]")
        print("1. 등록된 반복 템플릿 목록 조회")
        print("2. 신규 반복 템플릿 등록")
        print("3. 기존 반복 템플릿 삭제")
        print("4. 특정 월 반복 거래 일괄 생성")
        
        choice = self.prompt_validated_input("선택", lambda x: (True, "", "") if x in ["1", "2", "3", "4", ""] else (False, "1, 2, 3, 4 중 선택해 주세요.", ""), "", ["1", "2", "3", "4"])
        if not choice:
            return
            
        if choice == "1":
            templates = self.service.load_recurring_templates()
            if not templates:
                print("등록된 반복 내역이 없습니다.")
                return
            headers = ["id", "type", "category", "amount", "day", "memo", "tags"]
            rows = []
            for t in templates:
                tags_str = ",".join(t.tags) if t.tags else ""
                rows.append([t.id, t.type, t.category, f"{t.amount:,}원", f"매월 {t.day}일", t.memo, tags_str])
            print_aligned_rows(headers, rows)
            
        elif choice == "2":
            print("[신규 반복 템플릿 등록]")
            type_str = self.prompt_validated_input("- 타입", validate_type, None, ["income", "expense"])
            category = self.prompt_category_interactive()
            amount = int(self.prompt_validated_input("- 금액", validate_amount, None, ["10000", "30000", "50000"]))
            day = int(self.prompt_validated_input("- 매월 반복 일자 (1-31)", validate_day, None, ["25", "20", "10"]))
            memo = self.prompt_validated_input("- 메모 (선택)", lambda x: (True, "", ""), "", ["월세", "보험금", "기본급"])
            tags_input = self.prompt_validated_input("- 태그 (선택)", lambda x: (True, "", ""), "", ["고정비", "월세", "급여"])
            tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []
            
            new_id = self.service.add_recurring_template(type_str, category, amount, day, memo, tags)
            print(f"[저장 완료] template_id={new_id}")
            
        elif choice == "3":
            existing_rec_ids = self.get_all_recurring_ids()
            t_id = self.prompt_validated_input("- 삭제할 템플릿 ID (REC-XXXXXX)", lambda x: (True, "", "") if x in existing_rec_ids else (False, "존재하지 않는 템플릿 ID입니다.", ""), None, existing_rec_ids)
            if not t_id:
                return
            success = self.service.remove_recurring_template(t_id)
            if success:
                print(f"[삭제 성공] template_id={t_id}")
            else:
                print(f"[삭제 실패] template_id={t_id} 삭제 오류")
                
        elif choice == "4":
            this_month = datetime.date.today().strftime("%Y-%m")
            month = self.prompt_validated_input("- 자동 생성할 대상 월 (YYYY-MM)", validate_month, this_month, [this_month])
            print("[처리 진행 중...]")
            count = self.service.generate_recurring_transactions(month)
            print(f"[처리 완료] {month} 월에 총 {count}건의 반복 거래 내역을 가계부에 자동 추가했습니다.")
        else:
            print("[오류] 잘못된 선택입니다.")
