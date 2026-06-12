"""
================================================================================
budget_app/models.py - 가계부 도메인 모델 정의 및 직렬화 계층
================================================================================
본 모듈은 가계부 프로그램 내부에서 통용되는 핵심 데이터 구조(거래 내역 및 반복 거래 템플릿)를
정의하고, 파일 저장과 네트워크 통신을 위한 JSON 직렬화/역직렬화 기능을 담당합니다.

[주요 클래스]
1. Transaction: 개별 수입/지출 내역의 구체적 구조 데이터 클래스
2. RecurringTemplate: 매월 자동 생성되는 수입/지출 반복 거래용 템플릿 구조 데이터 클래스
================================================================================
"""

from dataclasses import dataclass, field
from typing import List

@dataclass
class Transaction:
    """
    개별 가계부 거래 내역 정보를 나타내는 데이터 클래스입니다.
    """
    id: str                                                                   # 고유 거래 ID (예: TX-000001)
    type: str  # "income" or "expense"                                        # 거래 타입 ("income": 수입, "expense": 지출)
    date: str  # YYYY-MM-DD                                                   # 거래 날짜 (YYYY-MM-DD 포맷)
    amount: int  # positive integer                                           # 거래 금액 (양의 정수)
    category: str                                                             # 카테고리 명칭 (예: food, rent)
    memo: str = ""                                                            # 선택적 메모 문자열
    tags: List[str] = field(default_factory=list)                             # 쉼표 구분 선택적 태그 목록 리스트

    def to_dict(self) -> dict:
        """
        Transaction 객체의 데이터 필드들을 JSON 직렬화가 가능한 파이썬 딕셔너리로 변환합니다.

        Returns:
            dict: 직렬화된 형태의 거래 정보 딕셔너리
        """
        return {
            "id": self.id,                                                    # ID 필드 매핑
            "type": self.type,                                                # 타입 필드 매핑
            "date": self.date,                                                # 날짜 필드 매핑
            "amount": self.amount,                                            # 금액 필드 매핑
            "category": self.category,                                        # 카테고리 필드 매핑
            "memo": self.memo,                                                # 메모 필드 매핑
            "tags": self.tags,                                                # 태그 리스트 매핑
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Transaction':
        """
        직렬화 해제된 딕셔너리 데이터로부터 Transaction 객체를 재생성합니다.

        Args:
            data (dict): 역직렬화할 거래 데이터 딕셔너리

        Returns:
            Transaction: 생성된 Transaction 객체 인스턴스
        """
        return cls(
            id=data["id"],                                                    # ID 매핑
            type=data["type"],                                                # 타입 매핑
            date=data["date"],                                                # 날짜 매핑
            amount=data["amount"],                                            # 금액 매핑
            category=data["category"],                                        # 카테고리 매핑
            memo=data.get("memo", ""),                                        # 메모 기본값 설정 매핑
            tags=data.get("tags", []),                                        # 태그 기본값 리스트 설정 매핑
        )

@dataclass
class RecurringTemplate:
    """
    매달 고정적으로 발생하는 반복 거래의 템플릿 명세를 정의하는 데이터 클래스입니다.
    """
    id: str                                                                   # 고유 반복 거래 템플릿 ID (예: REC-000001)
    type: str  # "income" or "expense"                                        # 거래 타입 ("income": 수입, "expense": 지출)
    category: str                                                             # 카테고리 명칭
    amount: int                                                               # 반복 지출/수입 금액
    day: int  # 1-31                                                          # 매달 실행할 반복 일자 (1 ~ 31일)
    memo: str = ""                                                            # 선택적 메모 문자열
    tags: List[str] = field(default_factory=list)                             # 템플릿에 지정된 태그 목록 리스트

    def to_dict(self) -> dict:
        """
        RecurringTemplate 객체를 직렬화 가능한 딕셔너리로 변환합니다.

        Returns:
            dict: 직렬화된 형태의 템플릿 딕셔너리
        """
        return {
            "id": self.id,                                                    # ID 필드 매핑
            "type": self.type,                                                # 타입 필드 매핑
            "category": self.category,                                        # 카테고리 필드 매핑
            "amount": self.amount,                                            # 금액 필드 매핑
            "day": self.day,                                                  # 반복 일자 매핑
            "memo": self.memo,                                                # 메모 매핑
            "tags": self.tags,                                                # 태그 목록 매핑
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'RecurringTemplate':
        """
        딕셔너리 데이터로부터 RecurringTemplate 객체를 역직렬화 생성합니다.

        Args:
            data (dict): 역직렬화할 템플릿 데이터 딕셔너리

        Returns:
            RecurringTemplate: 생성된 RecurringTemplate 객체 인스턴스
        """
        return cls(
            id=data["id"],                                                    # ID 매핑
            type=data["type"],                                                # 타입 매핑
            category=data["category"],                                        # 카테고리 매핑
            amount=data["amount"],                                            # 금액 매핑
            day=data["day"],                                                  # 반복 일자 매핑
            memo=data.get("memo", ""),                                        # 메모 기본값 매핑
            tags=data.get("tags", []),                                        # 태그 목록 기본값 매핑
        )
