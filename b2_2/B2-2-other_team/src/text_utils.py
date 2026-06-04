"""
text_utils.py

문자열 유틸리티 함수 모음

사용 예시:
from text_utils import validate_length

    validate_length("hello", min_length=3)  # True
    validate_length("hi", min_length=3)     # False
"""

def validate_length(
    text: str,
    min_length: int = 0,
    max_length: int | None = None
) -> bool:
    """
    문자열 길이가 지정된 범위 내에 있는지 검증합니다.

    Args:
        text (str): 검증할 문자열
        min_length (int): 최소 길이
        max_length (int | None): 최대 길이 (없으면 제한 없음)

    Returns:
        bool: 길이 조건을 만족하면 True, 아니면 False

    Raises:
        ValueError: min_length 또는 max_length가 0보다 작은 경우
    """
    if min_length < 0:
        return True

    if max_length is not None and max_length < 0:
        raise ValueError("max_length는 0 이상이어야 합니다.")

    length = len(text)

    if length < min_length:
        return False

    if max_length is not None and length > max_length:
        return False

    return True
def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in the given string.

    Example:
        normalize_whitespace("  hello   world  ") -> "hello world"
    """
    return " ".join(text.split())


def to_uppercase(text: str) -> str:
    """
    Convert the given string to uppercase.

    Example:
        to_uppercase("hello") -> "HELLO"
    """
    return text.upper()


def to_lowercase(text: str) -> str:
    """
    Convert the given string to lowercase.

    Example:
        to_lowercase("HELLO") -> "hello"
    """
    return text.lower()
