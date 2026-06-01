from dataclasses import dataclass, field
from typing import List

@dataclass
class Transaction:
    id: str
    type: str  # "income" or "expense"
    date: str  # YYYY-MM-DD
    amount: int  # positive integer
    category: str
    memo: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "date": self.date,
            "amount": self.amount,
            "category": self.category,
            "memo": self.memo,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Transaction':
        return cls(
            id=data["id"],
            type=data["type"],
            date=data["date"],
            amount=data["amount"],
            category=data["category"],
            memo=data.get("memo", ""),
            tags=data.get("tags", []),
        )

@dataclass
class RecurringTemplate:
    id: str
    type: str  # "income" or "expense"
    category: str
    amount: int
    day: int  # 1-31
    memo: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "category": self.category,
            "amount": self.amount,
            "day": self.day,
            "memo": self.memo,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'RecurringTemplate':
        return cls(
            id=data["id"],
            type=data["type"],
            category=data["category"],
            amount=data["amount"],
            day=data["day"],
            memo=data.get("memo", ""),
            tags=data.get("tags", []),
        )
