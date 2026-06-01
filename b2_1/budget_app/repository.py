import os
import json
import tempfile
from typing import Generator, List, Dict, Optional
from budget_app.models import Transaction, RecurringTemplate

class FileRepository:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.transactions_path = os.path.join(data_dir, "transactions.jsonl")
        self.categories_path = os.path.join(data_dir, "categories.jsonl")
        self.budgets_path = os.path.join(data_dir, "budgets.jsonl")
        self.recurring_path = os.path.join(data_dir, "recurring.jsonl")
        self._ensure_dir()

    def _ensure_dir(self):
        os.makedirs(self.data_dir, exist_ok=True)

    def stream_transactions(self) -> Generator[Transaction, None, None]:
        """Streams transactions from the JSONL file one by one using a generator."""
        if not os.path.exists(self.transactions_path):
            return
        with open(self.transactions_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    yield Transaction.from_dict(data)
                except (json.JSONDecodeError, KeyError):
                    continue

    def append_transaction(self, tx: Transaction):
        """Appends a single transaction to the end of the JSONL file."""
        with open(self.transactions_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(tx.to_dict(), ensure_ascii=False) + "\n")

    def update_or_delete_transaction(self, tx_id: str, updated_tx: Optional[Transaction]) -> bool:
        """
        Updates or deletes a transaction in the file.
        Uses write-to-temp-file and atomic rename (atomic exchange) for data safety.
        If updated_tx is None, the transaction is deleted.
        """
        found = False
        temp_fd, temp_path = tempfile.mkstemp(dir=self.data_dir, prefix="transactions_tmp_", suffix=".jsonl")
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as out_f:
                if os.path.exists(self.transactions_path):
                    with open(self.transactions_path, "r", encoding="utf-8") as in_f:
                        for line in in_f:
                            line = line.strip()
                            if not line:
                                continue
                            try:
                                data = json.loads(line)
                                if data.get("id") == tx_id:
                                    found = True
                                    if updated_tx is not None:
                                        out_f.write(json.dumps(updated_tx.to_dict(), ensure_ascii=False) + "\n")
                                else:
                                    out_f.write(line + "\n")
                            except (json.JSONDecodeError, KeyError):
                                out_f.write(line + "\n")
            if found:
                os.replace(temp_path, self.transactions_path)
            else:
                os.remove(temp_path)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e
        return found

    def load_categories(self) -> List[str]:
        """Loads categories from file. Auto-creates with defaults if empty or missing."""
        if not os.path.exists(self.categories_path):
            self.save_categories(self.get_default_categories())
            return self.get_default_categories()
        
        categories = []
        with open(self.categories_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    categories.append(data["name"])
                except (json.JSONDecodeError, KeyError):
                    continue
        if not categories:
            categories = self.get_default_categories()
            self.save_categories(categories)
        return categories

    def get_default_categories(self) -> List[str]:
        return ["food", "transport", "rent", "shopping", "health", "education", "salary", "allowance", "other"]

    def save_categories(self, categories: List[str]):
        """Saves categories to file. Uses atomic write with temp file and rename."""
        temp_fd, temp_path = tempfile.mkstemp(dir=self.data_dir, prefix="categories_tmp_", suffix=".jsonl")
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                for cat in categories:
                    f.write(json.dumps({"name": cat}, ensure_ascii=False) + "\n")
            os.replace(temp_path, self.categories_path)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e

    def load_budgets(self) -> Dict[str, int]:
        """Loads budgets as a dict of YYYY-MM -> amount."""
        budgets = {}
        if not os.path.exists(self.budgets_path):
            return budgets
        with open(self.budgets_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    budgets[data["month"]] = data["amount"]
                except (json.JSONDecodeError, KeyError):
                    continue
        return budgets

    def save_budgets(self, budgets: Dict[str, int]):
        """Saves budgets to file. Uses atomic write with temp file and rename."""
        temp_fd, temp_path = tempfile.mkstemp(dir=self.data_dir, prefix="budgets_tmp_", suffix=".jsonl")
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                for month, amount in budgets.items():
                    f.write(json.dumps({"month": month, "amount": amount}, ensure_ascii=False) + "\n")
            os.replace(temp_path, self.budgets_path)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e

    def get_next_transaction_id(self) -> str:
        """Finds the maximum numeric ID in transactions and returns the next incremented ID."""
        max_id = 0
        if os.path.exists(self.transactions_path):
            with open(self.transactions_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        tx_id = data.get("id", "")
                        if tx_id.startswith("TX-"):
                            val = int(tx_id.split("-")[1])
                            if val > max_id:
                                max_id = val
                    except (json.JSONDecodeError, ValueError, IndexError):
                        continue
        return f"TX-{max_id + 1:06d}"

    def get_next_recurring_id(self) -> str:
        """Finds the maximum numeric ID in recurring templates and returns the next ID."""
        max_id = 0
        if os.path.exists(self.recurring_path):
            with open(self.recurring_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        rec_id = data.get("id", "")
                        if rec_id.startswith("REC-"):
                            val = int(rec_id.split("-")[1])
                            if val > max_id:
                                max_id = val
                    except (json.JSONDecodeError, ValueError, IndexError):
                        continue
        return f"REC-{max_id + 1:06d}"
