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
    """
    명령줄 인자를 파싱하고 저장소, 서비스, 셸 객체를 초기화하여 가계부 프로그램을 시작합니다.
    """
    parser = argparse.ArgumentParser(                                         # ArgumentParser 객체를 생성하여 명령줄 인자를 처리할 준비를 합니다.
        description="파일 기반 가계부 콘솔 프로그램 (budget_app)",
        add_help=True
    )
    # 글로벌 옵션 지정
    parser.add_argument(                                                      # --data-dir 옵션을 추가하여 데이터 저장 폴더 경로를 지정할 수 있도록 합니다.
        "--data-dir",
        default="./data",
        help="데이터 저장 폴더 경로 (기본값: ./data)"
    )

    args, unknown = parser.parse_known_args()                                 # 명령줄 인자를 분석하여 args 객체에 저장합니다. (알 수 없는 인자는 무시)

    try:
        repo = FileRepository(args.data_dir)                                  # 데이터 액세스(저장소) 계층 생성
        service = BudgetService(repo)                                         # 비즈니스 로직(서비스) 계층 생성 및 저장소 주입
        shell = InteractiveShell(service)                                     # UI/명령어(셸) 계층 생성 및 서비스 주입
        shell.run()                                                           # 가계부 대화형 셸 루프 구동
    except Exception as e:
        print(f"[오류] 초기 구동 실패: {e}", file=sys.stderr)                   # 초기화 중 오류 stderr 출력
        print("[힌트] 데이터 저장 경로의 읽기/쓰기 권한을 확인해 주세요.", file=sys.stderr) # 문제 해결 힌트 출력
        sys.exit(1)                                                           # 프로그램 비정상 종료 (에러코드 1)

if __name__ == "__main__":
    main()                                                                    # 메인 함수 구동
