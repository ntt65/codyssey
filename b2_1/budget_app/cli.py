"""
================================================================================
budget_app/cli.py - 대화형 셸 사용자 인터페이스 (Interactive Console UI Layer)
================================================================================
본 모듈은 가계부 애플리케이션의 사용자 인터페이스(CLI)를 처리합니다. 
터미널 환경에서 직관적이고 편안한 UX를 제공하기 위해 다양하고 풍부한 유틸리티를 제공합니다.

[주요 기능적 특징]
1. macOS 한영 입력기 자동 강제 전환 (TIS API 이용, 영문 전환을 통한 오타 방지).
2. readline 및 raw input 모드를 사용한 키보드 입력 인터랙션:
   - 메인 프롬프트 및 선택지 프롬프트에서 방향키(Up/Down, Left/Right)를 활용한 옵션 선택 기능.
   - Tab 자동완성 및 히스토리(Up/Down) 연동.
   - Prefill (추천값 미리 입력 및 수정 시 백스페이스 덮어쓰기).
3. CJK(한글) 2바이트 너비 인식을 기반으로 한 터미널 화면 정렬 출력 테이블 포맷터 내장.
================================================================================
"""

import sys
import datetime
import unicodedata
import ctypes
import ctypes.util
from typing import List, Callable, Tuple, Optional

# readline 모듈 로드 시도 (자동완성 등 제어 목적)
try:
    import readline
except ImportError:
    readline = None                                                           # readline 미지원 OS일 시 None 처리

from budget_app.models import Transaction, RecurringTemplate
from budget_app.service import BudgetService
from budget_app.repository import FileRepository
from budget_app.decorators import catch_errors, measure_time, log_action

# --- macOS Input Method (IME) Auto Switcher ---

def switch_to_english():
    """
    macOS 환경의 입력 소스를 프로그래밍 방식으로 영어(US)로 강제 변환합니다.
    pyobjc 외부 모듈 종속성을 피하기 위해 ctypes로 CoreFoundation 및 Carbon 프레임워크를 동적으로 호출합니다.
    """
    try:
        cf_path = ctypes.util.find_library('CoreFoundation')                  # CF 라이브러리 경로 획득
        if not cf_path:
            return False
        cf = ctypes.cdll.LoadLibrary(cf_path)                                 # CoreFoundation 동적 로딩
        
        carbon_path = ctypes.util.find_library('Carbon')                      # Carbon 라이브러리 경로 획득
        if not carbon_path:
            return False
        carbon = ctypes.cdll.LoadLibrary(carbon_path)                         # Carbon 동적 로딩

        # TIS 관련 API 및 메모리 해제 함수 아규먼트/리턴 데이터 타입 매핑
        cf.CFStringCreateWithCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32]
        cf.CFStringCreateWithCString.restype = ctypes.c_void_p

        cf.CFRelease.argtypes = [ctypes.c_void_p]
        cf.CFRelease.restype = None

        carbon.TISCopyInputSourceForLanguage.argtypes = [ctypes.c_void_p]
        carbon.TISCopyInputSourceForLanguage.restype = ctypes.c_void_p

        carbon.TISSelectInputSource.argtypes = [ctypes.c_void_p]
        carbon.TISSelectInputSource.restype = ctypes.c_int32

        # 영문 언어 식별자 "en"용 CFString 문자열 생성 (kCFStringEncodingUTF8 = 0x08000100)
        utf8_str = cf.CFStringCreateWithCString(None, b"en", 0x08000100)
        if not utf8_str:
            return False

        source = carbon.TISCopyInputSourceForLanguage(utf8_str)               # 영문 입력 소스 포인터 복사
        cf.CFRelease(utf8_str)                                                # 사용 완료된 CFString 메모리 해제

        if not source:
            return False

        status = carbon.TISSelectInputSource(source)                          # 시스템 입력 소스를 영어로 선택 전환
        cf.CFRelease(source)                                                  # 소스 포인터 메모리 해제
        return status == 0                                                    # 전환 성공 유무 반환
    except Exception:
        return False                                                          # 오류 시 안전하게 실패 전환

# --- Auto-Complete (Readline) for Command Prompt ---

class CommandCompleter:
    """
    readline 모듈과 바인딩하여 명령어 후보군의 자동완성을 구현하는 completer 클래스입니다.
    """
    def __init__(self, commands: List[str]):
        """
        자동완성 대상 명령어 목록을 가지고 생성됩니다.

        Args:
            commands (List[str]): 셸에서 인식할 명령어 목록 리스트
        """
        self.commands = commands                                              # 매칭 시 후보가 될 명령어 보관

    def complete(self, text: str, state: int) -> Optional[str]:
        """
        사용자 입력 접두사와 매칭되는 명령어를 반환합니다.

        Args:
            text (str): 사용자가 현재 입력한 문자열
            state (int): 매칭된 목록 중 가져올 인덱스 상태값

        Returns:
            Optional[str]: 매칭된 완성 단어 (없을 시 None)
        """
        # 현재까지 타이핑한 문자로 시작하는 명령어들 매칭 수집 (대소문자 무시)
        matches = [cmd for cmd in self.commands if cmd.lower().startswith(text.lower())]
        if state < len(matches):
            return matches[state]                                             # 현재 순번의 완성어 반환
        return None

# --- Raw Terminal Choice Prompt ---

def prompt_choices(prompt_text: str, choices: List[str], default_value: Optional[str] = None) -> str:
    """
    방향키 순환 탐색, 첫 글자 Tab 완성 및 인라인 Prefill 수정 모드를 지원하는 향상된 대화식 프롬프트 함수입니다.

    Args:
        prompt_text (str): 사용자에게 출력할 프롬프트 질문 텍스트
        choices (List[str]): 방향키로 탐색 및 자동완성할 후보 목록
        default_value (Optional[str]): 입력 없이 엔터를 눌렀을 때 적용될 추천 기본값

    Returns:
        str: 최종적으로 확정된 입력값 문자열
    """
    switch_to_english()                                                       # 영문 오타 유발 방지를 위한 입력 소스 전환
    
    # 선택지 목록이 부재할 시 기존의 표준 내장 input 기능으로 대체 가동
    if not choices:
        prompt_suffix = f" [{default_value}]: " if default_value else ": "
        res = input(prompt_text + prompt_suffix).strip()
        if not res and default_value:
            return default_value
        return res

    # 디폴트 날짜 등 단일 후보에 대한 선택 형식일 때는 괄호 힌트 노출을 배제해 심플하게 구성
    if len(choices) == 1 and choices[0] == default_value:
        prompt_display = ""
    else:
        prompt_display = " " + format_choices(choices)                        # (선택지1 /선택지2) 목록으로 보기 쉽게 변환

    full_prompt = f"{prompt_text}{prompt_display}: "                         # 전체 프롬프트 문구 조합

    # 터미널 대화형 입력 환경(TTY)인지 확인하고 아닐 시 표준 인풋 사용 (테스트 코드 대응)
    if not sys.stdin.isatty():
        res = input(full_prompt).strip()
        if not res and default_value:
            return default_value
        return res

    import tty
    import termios

    current_text = default_value if default_value else ""                     # 출력에 기작성해 둘 텍스트
    is_default_active = True if default_value else False                      # 디폴트값 덮어쓰기 모드 유무 플래그
    current_index = -1                                                        # 현재 방향키로 선택된 선택지 인덱스

    sys.stdout.write(f"{full_prompt}{current_text}")                          # 프롬프트와 기본값 인라인 렌더링
    sys.stdout.flush()

    def getch() -> str:
        """단일 키 입력을 버퍼링 없이 즉각 가져오기 위해 터미널을 잠시 raw 모드로 설정해 1글자 읽어옵니다."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def get_key() -> str:
        """키 입력 부를 판독하여 방향키, 탭, 백스페이스, 엔터 등을 정형화된 약속 단어로 변환합니다."""
        ch = getch()
        if ch == '\x1b':                                                      # 이스케이프 시퀀스(방향키 등 특수키) 시작 판정
            ch2 = getch()
            if ch2 == '[':
                ch3 = getch()
                if ch3 == 'A': return 'up'
                elif ch3 == 'B': return 'down'
                elif ch3 == 'C': return 'right'
                elif ch3 == 'D': return 'left'
            return 'esc'
        elif ch == '\t': return 'tab'                                         # 탭 완성 키
        elif ch in ('\n', '\r'): return 'enter'                               # 최종 결정 엔터
        elif ch in ('\x7f', '\x08'): return 'backspace'                       # 글자 소거 백스페이스
        elif ch == '\x03': raise KeyboardInterrupt                            # Ctrl+C 인터럽트 감지 시 중단 예외
        return ch

    def get_matches(text):
        """현재까지 입력된 글자로 매칭되는 후보 항목 리스트 취득"""
        return [c for c in choices if c.lower().startswith(text.lower())]

    # 터미널 문자 탐색 무한 루프
    while True:
        key = get_key()
        
        if key == 'enter':                                                    # 결정 엔터
            sys.stdout.write("\n")
            sys.stdout.flush()
            if not current_text and default_value:
                return default_value                                          # 아무것도 안 치고 치면 기본값 탑재
            return current_text
            
        elif key == 'backspace':                                              # 글자 제거 백스페이스
            if is_default_active:                                             # 첫 타이핑 시 디폴트값이 통째로 지워지는 prefill 효과
                current_text = ""                                             # 텍스트 전체 공백
                is_default_active = False                                     # 기본값 덮어쓰기 모드 꺼짐
            else:
                current_text = current_text[:-1]                              # 한 글자 제거
            current_index = -1                                                # 방향키 인덱스 리셋
            
        elif key == 'tab':                                                    # 자동완성 탭
            if is_default_active:
                is_default_active = False
            elif not current_text and default_value:
                current_text = default_value                                  # 빈 칸 탭은 디폴트 작성
            else:
                m = get_matches(current_text)                                 # 접두 매치 후보 스캔
                if m:
                    current_text = m[0]                                       # 첫 번째 일치 항목 등록
                    current_index = choices.index(m[0])
                    
        elif key in ('down', 'right'):                                        # 정방향 순환 선택
            is_default_active = False
            matched_choice = None
            for c in choices:
                if c.lower() == current_text.lower():
                    matched_choice = c
                    break
            if matched_choice is not None:
                idx = choices.index(matched_choice)
                current_index = (idx + 1) % len(choices)                      # 인덱스 1 증가 (순환 순회)
            else:
                m = get_matches(current_text)
                if m:
                    idx = choices.index(m[0])
                    current_index = idx
                else:
                    current_index = 0
            current_text = choices[current_index]                             # 텍스트 교체
                
        elif key in ('up', 'left'):                                           # 역방향 순환 선택
            is_default_active = False
            matched_choice = None
            for c in choices:
                if c.lower() == current_text.lower():
                    matched_choice = c
                    break
            if matched_choice is not None:
                idx = choices.index(matched_choice)
                current_index = (idx - 1) % len(choices)                      # 인덱스 1 감소
            else:
                m = get_matches(current_text)
                if m:
                    idx = choices.index(m[0])
                    current_index = (idx - 1) % len(choices)
                else:
                    current_index = len(choices) - 1
            current_text = choices[current_index]                             # 텍스트 교체
                
        else:                                                                 # 일반 텍스트 문자 타이핑
            if len(key) == 1:
                if is_default_active:                                         # 디폴트 상태에서 첫 문자 기입 시 기존 기본 추천글 전부 덮어씀
                    current_text = key                                        # 새 글자로 전면 리셋 교체
                    is_default_active = False
                else:
                    current_text += key                                       # 글자 뒤에 결합
                current_index = -1
                
        # 터미널에 새로 구성된 텍스트 렌더링 (이전 글 지우고 출력)
        sys.stdout.write(f"\r{full_prompt}{current_text}\x1b[K")
        sys.stdout.flush()

# --- Formatting Helpers ---

def format_choices(items: List[str]) -> str:
    """
    선택지 목록을 보기 좋은 (항목1 /항목2 /항목3 ) 형태의 한 줄 문자열로 서식화합니다.

    Args:
        items (List[str]): 서식할 문자열 목록

    Returns:
        str: 가로 목록 괄호 문자열
    """
    if not items:
        return ""
    return "(" + " /".join(items) + " )"

def visual_len(s: str) -> int:
    """
    한글(더블바이트)과 영문(싱글바이트)의 문자 크기를 계산하여 
    터미널의 실제 시각적 가로 너비(폭)를 산출합니다.

    Args:
        s (str): 너비를 판별할 문자열

    Returns:
        int: 문자열의 가로 폭 정수 (한글은 글자당 2)
    """
    width = 0
    for char in s:
        # 동아시아 와이드 문자(W, F, A) 타입인 경우 터미널 가로폭 2로 계산
        if unicodedata.east_asian_width(char) in ('W', 'F', 'A'):
            width += 2
        else:
            width += 1
    return width

def pad_string(s: str, width: int) -> str:
    """
    시각적 폭 길이를 정확하게 맞추기 위해 뒷부분에 필요한 만큼 공백 문자를 패딩 삽입합니다.

    Args:
        s (str): 대상 원본 문자열
        width (int): 도달해야 하는 목표 너비 폭

    Returns:
        str: 뒤쪽 여백 공백이 삽입된 패딩 문자열
    """
    cur_width = visual_len(s)
    if cur_width >= width:
        return s
    return s + " " * (width - cur_width)                                      # 차액 너비만큼 스페이스 추가 기입

def print_aligned_rows(headers: List[str], rows: List[List[str]]):
    """
    동아시아 2바이트 한글 폰트의 가폭 깨짐 현상을 보정하여 
    파이썬 표준 라이브러리만으로도 표 형태 정렬 출력이 예쁘게 나오도록 렌더링하는 함수입니다.

    Args:
        headers (List[str]): 테이블 헤더 컬럼 목록 리스트
        rows (List[List[str]]): 테이블 바디 행 데이터 이중 리스트
    """
    if not rows:
        return
    
    col_count = len(headers)
    max_widths = [visual_len(h) for h in headers]                             # 열별 가로 너비 초깃값을 헤더 폭으로 구성
    for row in rows:
        for i in range(min(col_count, len(row))):
            val_len = visual_len(row[i])
            if val_len > max_widths[i]:
                max_widths[i] = val_len                                       # 최대 가로폭 수치 동적 업데이트

    # 헤더 행 데이터 출력 기입
    header_line = [pad_string(h, max_widths[i]) for i, h in enumerate(headers)]
    print(" | ".join(header_line))
    print("-+-".join("-" * w for w in max_widths))                             # 표 칸막이 구분 라인 렌더링

    # 본문 행 데이터 출력 기입
    for row in rows:
        formatted_row = []
        for i, val in enumerate(row):
            formatted_row.append(pad_string(val, max_widths[i]))              # 패딩 정렬 적용
        print(" | ".join(formatted_row))

# --- Input Field Validators ---

def validate_date(val: str) -> Tuple[bool, str, str]:
    """
    날짜 텍스트의 유효성 및 YYYY-MM-DD 포맷 여부를 체크합니다.
    """
    if not val:
        return False, "날짜를 입력해야 합니다.", "예: 2026-06-01"
    try:
        datetime.datetime.strptime(val, "%Y-%m-%d")
        return True, "", ""
    except ValueError:
        return False, "날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).", "예: 2026-06-01"

def validate_type(val: str) -> Tuple[bool, str, str]:
    """
    거래 타입(income, expense) 검증기
    """
    if val not in ["income", "expense"]:
        return False, "허용되지 않은 타입입니다.", "income 또는 expense 중 입력해 주세요."
    return True, "", ""

def validate_amount(val: str) -> Tuple[bool, str, str]:
    """
    금액(양수 정수) 검증기
    """
    try:
        num = int(val)
        if num <= 0:
            return False, "금액은 0보다 큰 양수여야 합니다.", "예: 15000"
        return True, "", ""
    except ValueError:
        return False, "금액은 숫자 형식이어야 합니다.", "예: 15000"

def validate_day(val: str) -> Tuple[bool, str, str]:
    """
    일수(1~31) 범위 검증기
    """
    try:
        num = int(val)
        if num < 1 or num > 31:
            return False, "일자(day)는 1에서 31 사이의 정수여야 합니다.", "예: 25"
        return True, "", ""
    except ValueError:
        return False, "일자(day)는 정수여야 합니다.", "예: 25"

def validate_month(val: str) -> Tuple[bool, str, str]:
    """
    월 표기 포맷(YYYY-MM) 검증기
    """
    try:
        datetime.datetime.strptime(val, "%Y-%m")
        return True, "", ""
    except ValueError:
        return False, "월 형식이 올바르지 않습니다 (YYYY-MM).", "예: 2026-06"

def validate_yes_no(val: str) -> Tuple[bool, str, str]:
    """
    컨펌 동의 여부(y/n) 대소문자 매칭 검증기
    """
    if val.lower() not in ["y", "yes", "예", "n", "no", "아니오"]:
        return False, "y 또는 n을 입력해 주세요.", "예: y"
    return True, "", ""

# --- Argument Extraction Helpers ---

def get_id_from_args(args: List[str], prefix: str = "TX-") -> Optional[str]:
    """
    커맨드에 연동되어 입력된 인자들로부터 고유 식별자(ID)를 식별 및 추출합니다.

    Args:
        args (List[str]): 공백 구분 전달 아규먼트 목록
        prefix (str): ID를 구분할 접두사 패턴 (기본값: 'TX-')

    Returns:
        Optional[str]: 분석 획득한 ID 값
    """
    if not args:
        return None
    if "--id" in args:
        idx = args.index("--id")
        if idx + 1 < len(args):
            return args[idx + 1]                                              # 플래그 뒤의 문자값 리턴
    for arg in args:
        if arg.startswith(prefix):
            return arg                                                        # 접두사 부합 문자값 리턴
    return args[0]                                                            # 조건 매칭 실패 시 첫 매개변수를 기본 반환

def get_filepath_from_args(args: List[str], flag: str = "--from") -> Optional[str]:
    """
    매개변수 리스트 목록에서 대상 파일 경로 인자를 발라냅니다.

    Args:
        args (List[str]): 아규먼트 목록
        flag (str): 파일 옵션 지정용 지시 플래그명 (기본값: '--from')

    Returns:
        Optional[str]: 식별된 파일 명칭 경로 문자열
    """
    if not args:
        return None
    if flag in args:
        idx = args.index(flag)
        if idx + 1 < len(args):
            return args[idx + 1]
    filtered = [arg for arg in args if not arg.startswith("-")]                # 옵션 플래그가 아닌 순수 매개값 추출
    return filtered[0] if filtered else args[0]                               # 인덱스 취득 및 실패 시 디폴트 반환

# --- Interactive Shell Class ---

class InteractiveShell:
    """
    대화형 가계부 프롬프트 셸 환경을 주관하는 프레젠테이션(UI) 계층 클래스입니다.
    사용자의 키 입력을 가로채 편리한 자동 선택 및 명령어 인터랙션을 연동합니다.
    """
    def __init__(self, service: BudgetService):
        """
        비즈니스 로직(서비스)을 연결받아 셸 객체를 초기화하고 자동완성 구성을 설정합니다.

        Args:
            service (BudgetService): 핵심 가계부 연산을 처리할 서비스 객체
        """
        self.service = service
        self.commands = [                                                     # 셸이 대응 및 인식할 명령어 배열 목록
            "help", "add", "list", "search", "summary", "budget", 
            "category", "update", "delete", "import", "export", 
            "backup", "recurring", "exit", "quit"
        ]
        # 지원 가능 터미널 환경인 경우 파이썬 기본 readline 자동완성 라이브러리 맵핑
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
        가계부 최상위 메인 명령어 전용 프롬프트 리더기입니다.
        이전 기록(Up/Down), 가로 명령어 순환 선택(Left/Right), Tab 완성 기능을 TTY 환경 하에 지원합니다.

        Args:
            prompt_text (str): 셸 기본 프롬프트 텍스트 (예: 'budget_app> ')

        Returns:
            str: 사용자가 최종 완수 기입한 커맨드 입력 라인
        """
        if not sys.stdin.isatty():                                            # 미지원 TTY 버퍼 환경 대응
            return input(prompt_text).strip()

        import tty
        import termios

        sys.stdout.write(prompt_text)
        sys.stdout.flush()

        current_text = ""                                                     # 현재까지 쳐진 버퍼 내용
        history_index = len(self.history)                                     # 이전 기록 탐색용 위치
        temp_draft = ""                                                       # 기입 도중 다른 기록 탐색 시 보관할 가 초안
        choices = self.commands                                               # 명령어 자동 완성 타겟 지정

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

            if key == 'enter':                                                # 최종 명령어 엔터 접수
                sys.stdout.write("\n")
                sys.stdout.flush()
                res = current_text.strip()
                if res:
                    # 히스토리 리스트 중복 누적 방지하여 추가 보관
                    if not self.history or self.history[-1] != res:
                        self.history.append(res)
                        if readline:
                            readline.add_history(res)
                return res

            elif key == 'backspace':                                          # 글자 단위 제거
                current_text = current_text[:-1]
                history_index = len(self.history)
                temp_draft = current_text                                     # 초안을 지우는 모드로 자동 업데이트

            elif key == 'tab':                                                # 접두 자동완성 트리거
                parts = current_text.split()                                  # 띄어쓰기로 첫 단어 분리
                if not parts:
                    current_text = choices[0]                                 # 빈 프롬프트 시 도움말 명령어 자동 선택
                else:
                    cmd_part = parts[0]
                    m = get_matches(cmd_part)                                 # 부분 탐색
                    if m:
                        parts[0] = m[0]                                       # 완성된 어휘 치환
                        current_text = " ".join(parts)                        # 뒤쪽 인자들과 문자 재결합
                history_index = len(self.history)
                temp_draft = current_text

            elif key in ('down', 'up'):                                       # 이전 커맨드 역사(History) 탐색
                if key == 'up':                                               # 과거로 탐색
                    if len(self.history) > 0 and history_index > 0:
                        if history_index == len(self.history):
                            temp_draft = current_text                         # 뒤로 되돌아올 때를 위한 초안 백업
                        history_index -= 1
                        current_text = self.history[history_index]            # 과거 기입 목록 추출
                elif key == 'down':                                           # 최근으로 복귀 탐색
                    if history_index < len(self.history):
                        history_index += 1
                        if history_index == len(self.history):
                            current_text = temp_draft                         # 마지막에는 작성하던 초안으로 롤백
                        else:
                            current_text = self.history[history_index]

            elif key in ('right', 'left'):                                    # 15가지 가계부 명령어 즉시 가로 순환 변경
                parts = current_text.split()                                  # 공백 분리
                cmd_part = parts[0] if parts else ""                          # 타겟 명령어 부분
                
                matched_choice = None
                for c in choices:
                    if c.lower() == cmd_part.lower():
                        matched_choice = c
                        break
                
                if matched_choice is not None:
                    idx = choices.index(matched_choice)
                    if key == 'right':
                        next_idx = (idx + 1) % len(choices)                    # 순방향 순환
                    else:
                        next_idx = (idx - 1) % len(choices)                    # 역방향 순환
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
                    current_text = " ".join(parts)                            # 결합 갱신
                
                history_index = len(self.history)
                temp_draft = current_text

            else:
                if len(key) == 1:
                    current_text += key                                       # 일반 키보드 기입 글자 덧붙임
                    history_index = len(self.history)
                    temp_draft = current_text

            # 터미널 한 줄 다시 그리기
            sys.stdout.write(f"\r{prompt_text}{current_text}\x1b[K")
            sys.stdout.flush()

    def run(self):
        """
        대화형 셸 구동 무한 루프를 활성화합니다. 
        사용자 입력 및 EOF(Ctrl+D) 처리 등을 관리하며, 데코레이터에서 걸러지지 못한 외부 인터럽트 등을 포착합니다.
        """
        print("==================================================")
        print("   💰 대화형 파일 기반 가계부 (budget_app) v1.0 💰")
        print("   - 사용법 확인: help 입력")
        print("   - 프로그램 종료: exit 또는 quit 입력")
        print("==================================================")
        
        self.history = []                                                     # 셸 세션 히스토리 보관함 초기화
        if readline:
            history_len = readline.get_current_history_length()               # 기존 내장 기록 수 취득
            for i in range(1, history_len + 1):
                item = readline.get_history_item(i)
                if item:
                    self.history.append(item)
                    
        while True:
            try:
                switch_to_english()                                           # 영어 소스 전환 실행
                
                user_input = self.prompt_main_command("budget_app> ").strip()  # 사용자 콘솔 한 줄 입력
                if not user_input:
                    continue
                
                parts = user_input.split()                                    # 어휘 단위 분리
                command = parts[0].lower()                                    # 소문자 변형 명령 구분명
                args = parts[1:]                                              # 명령어 뒤의 매개 인자 목록
                
                if command in ["exit", "quit"]:                               # 가계부 정상 종료 처리
                    print("==================================================")
                    print("   이용해 주셔서 감사합니다. 가계부를 종료합니다! ")
                    print("==================================================")
                    break
                
                self.parse_and_execute(command, args)                         # 명령어 라우팅 처리 함수 호출
                
            except KeyboardInterrupt:                                         # 대기 중에 Ctrl+C 입력 시 정상 종료가 아닌 셸 복구
                print("\n[정보] 입력이 취소되었습니다. 대기 상태로 복귀합니다.")
            except EOFError:                                                  # Ctrl+D 비정상 조작 대응
                print("\n==================================================")
                print("   이용해 주셔서 감사합니다. 가계부를 종료합니다! ")
                print("==================================================")
                break

    def parse_and_execute(self, command: str, args: List[str]):
        """
        분석 및 획득된 단어로 명령어 동작 함수(handle_*)를 호출 라우팅합니다.

        Args:
            command (str): 수행 명령어 단어
            args (List[str]): 연동 인자값
        """
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
        """
        수정/삭제 시 유효성 검사 후보가 되도록 파일 전체 거래 ID 리스트를 수집합니다.

        Returns:
            List[str]: 거래 ID 목록 (최신순 조회를 위해 역순 정렬)
        """
        ids = []
        for tx in self.service.repository.stream_transactions():
            ids.append(tx.id)
        ids.reverse()                                                         # 최신 데이터 ID를 상단 배치
        return ids

    def get_all_recurring_ids(self) -> List[str]:
        """
        반복 거래 템플릿의 전체 고유 ID 리스트 목록을 획득합니다.

        Returns:
            List[str]: 반복 거래 템플릿 ID 리스트
        """
        templates = self.service.load_recurring_templates()
        return [t.id for t in templates]

    # --- Universal Prompt Helpers ---

    def prompt_validated_input(self, prompt_text: str, validator: Callable[[str], Tuple[bool, str, str]], default_value: Optional[str] = None, suggestions: Optional[List[str]] = None) -> str:
        """
        올바른 입력이 들어올 때까지 예외를 안내하며 루프를 돌고 통과 시 값을 반환하는 검증 인풋 헬퍼입니다.

        Args:
            prompt_text (str): 프롬프트 출력 질문 명세
            validator (Callable): 유효성 유무 판별 함수
            default_value (Optional[str]): 디폴트 기입용 값
            suggestions (Optional[List[str]]): 자동완성 후보군 목록

        Returns:
            str: 유효성이 입증된 입력 완료 텍스트
        """
        while True:
            val = prompt_choices(prompt_text, suggestions or [], default_value) # raw 키 처리 프롬프트 호출
            is_valid, err, hint = validator(val)                              # 해당 값 검증 메서드 실행
            if is_valid:
                return val                                                    # 통과 시 값 반환 및 루프 종결
            print(f"[오류] {err}")                                             # 에러 세부 문장 출력
            if hint:
                print(f"[힌트] {hint}")                                        # 힌트 가이드 출력

    def prompt_category_interactive(self, current_val: Optional[str] = None) -> str:
        """
        카테고리 선택을 위한 전용 입력 프롬프트입니다.
        없는 카테고리를 기입하면 신규 생성 메뉴 추가 여부를 대화형으로 유연히 제안합니다.

        Args:
            current_val (Optional[str]): 초기 추천 혹은 기존 카테고리 값

        Returns:
            str: 매칭 혹은 신규 등록이 확인된 최종 카테고리 단어
        """
        categories = self.service.list_categories()                            # 카테고리 목록 적재
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
                return val                                                    # 기등록 리스트 중 존재 시 즉각 반환
                
            # 신규 추가 제안 분기
            print(f"[오류] 존재하지 않는 카테고리입니다: '{val}'")
            print(f"[힌트] 등록된 카테고리 목록: {', '.join(categories)}")
            ans = self.prompt_validated_input(f"       '{val}' 카테고리를 가계부에 새로 추가하고 진행하시겠습니까?", validate_yes_no, None, ["y", "n"])
            if ans.lower() in ['y', 'yes', '예']:
                self.service.add_category(val)                                # 카테고리 영속성 추가 수행
                print(f"[저장 완료] category={val}")
                return val

    # --- CLI Command Handlers ---

    def handle_help(self):
        """
        [help] 가계부 콘솔에서 사용이 허가된 전체 15개 커맨드의 요약 안내서를 표 서식화해 출력합니다.
        """
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
        print_aligned_rows(headers, rows)                                      # 정렬 렌더링 호출
        print("--------------------------------------------------------------------------------\n")

    @catch_errors
    def handle_add(self):
        """
        [add] 대화형 질문 흐름으로 신규 내역을 기입합니다.
        """
        print("[새 거래 추가를 시작합니다]")
        today_str = datetime.date.today().strftime("%Y-%m-%d")                # 오늘 날짜
        
        date = self.prompt_validated_input("- 날짜 (YYYY-MM-DD)", validate_date, today_str, [today_str])
        type_str = self.prompt_validated_input("- 타입", validate_type, "expense", ["income", "expense"])
        category = self.prompt_category_interactive("food")
        amount = int(self.prompt_validated_input("- 금액", validate_amount, "10000", ["10000", "30000", "50000"]))
        
        memo = self.prompt_validated_input("- 메모 (선택)", lambda x: (True, "", ""), "점심", ["점심", "저녁", "월세", "마트"])
        tags_input = self.prompt_validated_input("- 태그 (선택)", lambda x: (True, "", ""), "식대", ["식대", "생필품", "고정비", "교통"])
        tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []
        
        tx_id = self.service.add_transaction(date, type_str, category, amount, memo, tags) # 서비스 기입 호출
        print(f"[저장 완료] id={tx_id}")

    @catch_errors
    def handle_list(self, args: List[str]):
        """
        [list] 최신순 가계부 내역 테이블을 출력합니다.
        """
        limit = 20                                                            # 디폴트 개수 20선
        if args:
            try:
                limit = int(args[0])
                if limit <= 0:
                    raise ValueError
            except ValueError:
                print("[오류] limit 개수는 양의 정수여야 합니다.")
                print("[힌트] 예: list 5")
                return

        txs = self.service.list_transactions(limit)                           # 서비스 로드 수행
        if not txs:
            print("거래 내역이 없습니다.")
            return
            
        headers = ["id", "date", "type", "category", "amount", "memo", "tags"]
        rows = []
        for tx in txs:
            tags_str = ",".join(tx.tags) if tx.tags else ""
            rows.append([tx.id, tx.date, tx.type, tx.category, f"{tx.amount:,}원", tx.memo, tags_str])
        print_aligned_rows(headers, rows)                                      # 예쁜 표 출력

    @catch_errors
    def handle_search(self):
        """
        [search] 복합 다단계 대화식 필터를 통해 정밀 조회를 수행합니다.
        """
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
        """
        [summary] 특정 달의 총 수지 지표 및 예산 점검 리포트를 출력합니다.
        """
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
        """
        [budget] 특정 월의 소비 예산 책정치를 기록합니다.
        """
        this_month = datetime.date.today().strftime("%Y-%m")
        month = self.prompt_validated_input("- 예산을 책정할 대상 월 (YYYY-MM)", validate_month, this_month, [this_month])
        amount = int(self.prompt_validated_input("- 한도 금액 (0 이상 정수)", validate_amount, None, ["500000", "1000000"]))
        
        self.service.set_budget(month, amount)
        print(f"[저장 완료] {month} 예산 {amount:,}원 설정 완료.")

    @catch_errors
    def handle_category(self):
        """
        [category] 가계부 카테고리 서브 관리 메뉴
        """
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
        """
        [update] 특정 ID를 가진 거래의 수정 처리를 대화형으로 수행합니다.
        """
        tx_id = get_id_from_args(args)
        existing_ids = self.get_all_transaction_ids()
        
        if not tx_id:
            tx_id = self.prompt_validated_input("- 수정할 거래 ID", lambda x: (True, "", "") if x in existing_ids else (False, "존재하지 않는 거래 ID입니다.", ""), None, existing_ids)
            if not tx_id:
                return

        # 수정 대상 거래 내역 실시간 탐색
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
        """
        [delete] 특정 ID를 가진 거래 내역을 삭제합니다.
        """
        tx_id = get_id_from_args(args)
        existing_ids = self.get_all_transaction_ids()
        
        if not tx_id:
            tx_id = self.prompt_validated_input("- 삭제할 거래 ID", lambda x: (True, "", "") if x in existing_ids else (False, "존재하지 않는 거래 ID입니다.", ""), None, existing_ids)
            if not tx_id:
                return

        # 대상 존재 여부 체크
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
        """
        [import] 지정한 CSV 파일의 가계부 데이터를 거래 내역에 일괄 기입 기재합니다.
        """
        filepath = get_filepath_from_args(args, "--from")
        if not filepath:
            import os
            # 현재 작업 폴더 내 CSV 목록을 긁어와 자동완성 후보로 지원
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
        """
        [export] 추출 범위 조건에 맞는 내역을 특정 CSV 파일로 저장 내보내기합니다.
        """
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
        """
        [backup] 가계부 물리 파일 일체를 타임스탬프 zip 백업 파일로 압축 소장합니다.
        """
        print("[백업 진행 중...]")
        backup_path = self.service.create_backup()
        print(f"[백업 완료] 전체 데이터 백업이 안전하게 생성되었습니다: {backup_path}")

    @catch_errors
    def handle_recurring(self):
        """
        [recurring] 매월 반복 거래(고정비/고정수입)에 대한 일괄 설정 및 등록/해제 서브메뉴입니다.
        """
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
            type_str = self.prompt_validated_input("- 타입", validate_type, "expense", ["income", "expense"])
            category = self.prompt_category_interactive("food")
            amount = int(self.prompt_validated_input("- 금액", validate_amount, "10000", ["10000", "30000", "50000"]))
            day = int(self.prompt_validated_input("- 매월 반복 일자 (1-31)", validate_day, "25", ["25", "20", "10"]))
            memo = self.prompt_validated_input("- 메모 (선택)", lambda x: (True, "", ""), "월세", ["월세", "보험금", "기본급"])
            tags_input = self.prompt_validated_input("- 태그 (선택)", lambda x: (True, "", ""), "고정비", ["고정비", "월세", "급여"])
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
