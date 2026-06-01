import os
import csv
import zipfile
import datetime
import calendar
import tempfile
import json
from typing import Generator, List, Dict, Tuple, Optional
from budget_app.models import Transaction, RecurringTemplate
from budget_app.repository import FileRepository

class BudgetService:
    def __init__(self, repository: FileRepository):
        self.repository = repository

    # --- Transaction CRUD ---

    def add_transaction(self, date: str, type_str: str, category: str, amount: int, memo: str, tags: List[str]) -> str:
        """Adds a new transaction after validating fields."""
        # Field validation
        self.validate_fields(date, type_str, category, amount)

        tx_id = self.repository.get_next_transaction_id()
        tx = Transaction(
            id=tx_id,
            type=type_str,
            date=date,
            amount=amount,
            category=category,
            memo=memo,
            tags=tags
        )
        self.repository.append_transaction(tx)
        return tx_id

    def list_transactions(self, limit: int) -> List[Transaction]:
        """
        Returns transactions sorted by date (newest first, then ID desc).
        Respects streaming constraints: processes records one-by-one and keeps only the top 'limit' in memory.
        """
        # Maintain a size-limited sorted list to keep memory footprint O(limit)
        top_txs: List[Transaction] = []
        for tx in self.repository.stream_transactions():
            # Insert in sorted order (newest first: date desc, id desc)
            inserted = False
            for i, existing in enumerate(top_txs):
                if tx.date > existing.date or (tx.date == existing.date and tx.id > existing.id):
                    top_txs.insert(i, tx)
                    inserted = True
                    break
            if not inserted:
                top_txs.append(tx)
            
            if len(top_txs) > limit:
                top_txs.pop() # Discard the oldest
                
        return top_txs

    def search_transactions(self, 
                            from_date: Optional[str] = None, 
                            to_date: Optional[str] = None, 
                            category: Optional[str] = None, 
                            type_str: Optional[str] = None, 
                            query: Optional[str] = None, 
                            tag: Optional[str] = None, 
                            limit: int = 50) -> List[Transaction]:
        """
        Searches and filters transactions based on criteria.
        Maintains streaming constraint by filtering items on the fly and holding only matching items up to limit.
        """
        top_txs: List[Transaction] = []
        
        for tx in self.repository.stream_transactions():
            # Check date range
            if from_date and tx.date < from_date:
                continue
            if to_date and tx.date > to_date:
                continue
            # Check category (exact match)
            if category and tx.category != category:
                continue
            # Check type (exact match)
            if type_str and tx.type != type_str:
                continue
            # Check memo query (case-insensitive substring)
            if query and query.lower() not in tx.memo.lower():
                continue
            # Check tag (exact match inside list)
            if tag and tag not in tx.tags:
                continue

            # Insert in sorted order (newest first)
            inserted = False
            for i, existing in enumerate(top_txs):
                if tx.date > existing.date or (tx.date == existing.date and tx.id > existing.id):
                    top_txs.insert(i, tx)
                    inserted = True
                    break
            if not inserted:
                top_txs.append(tx)

            if len(top_txs) > limit:
                top_txs.pop()

        return top_txs

    def update_transaction(self, tx_id: str, date: str, type_str: str, category: str, amount: int, memo: str, tags: List[str]) -> bool:
        """Updates a transaction if it exists."""
        self.validate_fields(date, type_str, category, amount)
        updated_tx = Transaction(
            id=tx_id,
            type=type_str,
            date=date,
            amount=amount,
            category=category,
            memo=memo,
            tags=tags
        )
        return self.repository.update_or_delete_transaction(tx_id, updated_tx)

    def delete_transaction(self, tx_id: str) -> bool:
        """Deletes a transaction if it exists."""
        return self.repository.update_or_delete_transaction(tx_id, None)

    # --- Category Management ---

    def add_category(self, name: str) -> bool:
        """Adds a category if it doesn't already exist."""
        name = name.strip()
        if not name:
            raise ValueError("카테고리 이름은 공백일 수 없습니다.")
        categories = self.repository.load_categories()
        if name in categories:
            raise ValueError(f"이미 존재하는 카테고리입니다: {name}")
        categories.append(name)
        self.repository.save_categories(categories)
        return True

    def list_categories(self) -> List[str]:
        """Lists all registered categories."""
        return self.repository.load_categories()

    def remove_category(self, name: str) -> bool:
        """Removes a category if it exists and is not in use by any transactions."""
        name = name.strip()
        categories = self.repository.load_categories()
        if name not in categories:
            raise ValueError(f"존재하지 않는 카테고리입니다: {name}")
        
        # Check if the category is used in any transactions
        if self.is_category_in_use(name):
            raise ValueError(f"카테고리 '{name}'을 사용하는 거래 내역이 존재하여 삭제할 수 없습니다.")

        categories.remove(name)
        self.repository.save_categories(categories)
        return True

    def is_category_in_use(self, category: str) -> bool:
        """Streams transactions to check if any transaction uses the category."""
        for tx in self.repository.stream_transactions():
            if tx.category == category:
                return True
        return False

    # --- Budget and Summary ---

    def set_budget(self, month: str, amount: int):
        """Sets budget for a specific month (YYYY-MM)."""
        self.validate_month_format(month)
        if amount < 0:
            raise ValueError("예산 금액은 0 이상이어야 합니다.")
        budgets = self.repository.load_budgets()
        budgets[month] = amount
        self.repository.save_budgets(budgets)

    def get_monthly_summary(self, month: str, top_n: int) -> dict:
        """
        Computes monthly summary using streaming:
        Totals income, expense, and category expenses without storing all records in memory.
        """
        self.validate_month_format(month)

        total_income = 0
        total_expense = 0
        category_expenses: Dict[str, int] = {}
        has_data = False

        for tx in self.repository.stream_transactions():
            if tx.date.startswith(month + "-"):
                has_data = True
                if tx.type == "income":
                    total_income += tx.amount
                elif tx.type == "expense":
                    total_expense += tx.amount
                    category_expenses[tx.category] = category_expenses.get(tx.category, 0) + tx.amount

        if not has_data:
            return {"has_data": False}

        # Sort category expenses to get TOP N
        sorted_categories = sorted(category_expenses.items(), key=lambda x: x[1], reverse=True)
        top_categories = sorted_categories[:top_n]

        # Fetch budget
        budgets = self.repository.load_budgets()
        budget = budgets.get(month)

        return {
            "has_data": True,
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "top_categories": top_categories,
            "budget": budget
        }

    # --- Import / Export ---

    def export_to_csv(self, filepath: str, month: Optional[str] = None, from_date: Optional[str] = None, to_date: Optional[str] = None) -> int:
        """Exports matching transactions to a CSV file. Memory efficient due to streaming."""
        if not month and not (from_date and to_date):
            raise ValueError("수출(export)하려면 --month 또는 --from/--to 날짜 범위 중 하나 이상을 지정해야 합니다.")

        if month:
            self.validate_month_format(month)
        if from_date:
            self.validate_date_format(from_date)
        if to_date:
            self.validate_date_format(to_date)

        count = 0
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "type", "category", "amount", "memo", "tags"])

            for tx in self.repository.stream_transactions():
                if month and not tx.date.startswith(month + "-"):
                    continue
                if from_date and tx.date < from_date:
                    continue
                if to_date and tx.date > to_date:
                    continue

                tags_str = ",".join(tx.tags) if tx.tags else ""
                writer.writerow([tx.date, tx.type, tx.category, tx.amount, tx.memo, tags_str])
                count += 1

        return count

    def import_from_csv(self, filepath: str) -> Tuple[int, int]:
        """Imports transactions from a CSV file. Skips invalid records and counts skipped/imported."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"가져올 CSV 파일이 존재하지 않습니다: {filepath}")

        imported = 0
        skipped = 0

        # Efficiently generate IDs sequentially
        next_id = self.repository.get_next_transaction_id()
        id_prefix, id_num_str = next_id.split("-")
        current_id_num = int(id_num_str)

        categories = self.repository.load_categories()

        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            # Field validations and processing
            headers = [h.strip() for h in reader.fieldnames] if reader.fieldnames else []
            required_headers = ["date", "type", "category", "amount"]
            for req in required_headers:
                if req not in headers:
                    raise ValueError(f"CSV 파일에 필수 헤더가 부족합니다: '{req}'")

            for row in reader:
                # Normalization
                clean_row = {k.strip(): v.strip() for k, v in row.items() if k is not None and v is not None}
                date_str = clean_row.get("date", "")
                type_str = clean_row.get("type", "")
                category_str = clean_row.get("category", "")
                amount_str = clean_row.get("amount", "")
                memo_str = clean_row.get("memo", "")
                tags_str = clean_row.get("tags", "")

                # Inline validation
                is_valid = True
                try:
                    self.validate_date_format(date_str)
                    if type_str not in ["income", "expense"]:
                        is_valid = False
                    if category_str not in categories:
                        is_valid = False
                    amount = int(amount_str)
                    if amount <= 0:
                        is_valid = False
                except Exception:
                    is_valid = False

                if not is_valid:
                    skipped += 1
                    continue

                tx_id = f"{id_prefix}-{current_id_num:06d}"
                current_id_num += 1

                tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
                tx = Transaction(
                    id=tx_id,
                    type=type_str,
                    date=date_str,
                    amount=int(amount_str),
                    category=category_str,
                    memo=memo_str,
                    tags=tags
                )
                self.repository.append_transaction(tx)
                imported += 1

        return imported, skipped

    # --- Backup (Bonus 1) ---

    def create_backup(self) -> str:
        """Backs up transactions, categories, budgets, and recurring data into a timestamped zip file."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(self.repository.data_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        backup_path = os.path.join(backup_dir, f"backup_{timestamp}.zip")

        files_to_backup = [
            self.repository.transactions_path,
            self.repository.categories_path,
            self.repository.budgets_path,
            self.repository.recurring_path
        ]

        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files_to_backup:
                if os.path.exists(file_path):
                    zipf.write(file_path, os.path.basename(file_path))

        return backup_path

    # --- Recurring Templates (Bonus 2) ---

    def load_recurring_templates(self) -> List[RecurringTemplate]:
        """Loads all recurring templates from file."""
        templates = []
        if not os.path.exists(self.repository.recurring_path):
            return templates
        with open(self.repository.recurring_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    templates.append(RecurringTemplate.from_dict(data))
                except (json.JSONDecodeError, KeyError):
                    continue
        return templates

    def save_recurring_templates(self, templates: List[RecurringTemplate]):
        """Saves templates to file using atomic replacement."""
        temp_fd, temp_path = tempfile.mkstemp(dir=self.repository.data_dir, prefix="recurring_tmp_", suffix=".jsonl")
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                for t in templates:
                    f.write(json.dumps(t.to_dict(), ensure_ascii=False) + "\n")
            os.replace(temp_path, self.repository.recurring_path)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e

    def add_recurring_template(self, type_str: str, category_str: str, amount: int, day: int, memo: str, tags: List[str]) -> str:
        """Creates a recurring template after validation."""
        categories = self.repository.load_categories()
        if type_str not in ["income", "expense"]:
            raise ValueError("타입은 'income' 또는 'expense'여야 합니다.")
        if category_str not in categories:
            raise ValueError(f"등록되지 않은 카테고리입니다: {category_str}")
        if day < 1 or day > 31:
            raise ValueError("반복 일자(day)는 1에서 31 사이의 정수여야 합니다.")
        if amount <= 0:
            raise ValueError("금액은 양수여야 합니다.")

        templates = self.load_recurring_templates()
        new_id = self.repository.get_next_recurring_id()
        new_t = RecurringTemplate(
            id=new_id,
            type=type_str,
            category=category_str,
            amount=amount,
            day=day,
            memo=memo,
            tags=tags
        )
        templates.append(new_t)
        self.save_recurring_templates(templates)
        return new_id

    def remove_recurring_template(self, template_id: str) -> bool:
        """Removes a recurring template."""
        templates = self.load_recurring_templates()
        filtered = [t for t in templates if t.id != template_id]
        if len(filtered) == len(templates):
            return False
        self.save_recurring_templates(filtered)
        return True

    def generate_recurring_transactions(self, month: str) -> int:
        """
        Generates actual transaction records for the given month from the recurring templates.
        Checks for duplicates (matching date, type, category, amount, memo, and 'recurring' tag)
        to prevent duplicate inserts if run multiple times.
        """
        self.validate_month_format(month)
        year_part, month_part = map(int, month.split("-"))
        last_day = calendar.monthrange(year_part, month_part)[1]

        templates = self.load_recurring_templates()
        if not templates:
            return 0

        # Load existing transactions in the target month to check for duplicates
        existing_txs = []
        for tx in self.repository.stream_transactions():
            if tx.date.startswith(month + "-"):
                existing_txs.append(tx)

        generated_count = 0
        next_id = self.repository.get_next_transaction_id()
        id_prefix, id_num_str = next_id.split("-")
        current_id_num = int(id_num_str)

        for t in templates:
            actual_day = min(t.day, last_day)
            date_str = f"{month}-{actual_day:02d}"

            # Duplicate prevention
            is_duplicate = False
            for etx in existing_txs:
                if (etx.date == date_str and
                    etx.type == t.type and
                    etx.category == t.category and
                    etx.amount == t.amount and
                    etx.memo == t.memo and
                    "recurring" in etx.tags):
                    is_duplicate = True
                    break

            if not is_duplicate:
                tx_id = f"{id_prefix}-{current_id_num:06d}"
                current_id_num += 1

                tags = list(t.tags)
                if "recurring" not in tags:
                    tags.append("recurring")

                new_tx = Transaction(
                    id=tx_id,
                    type=t.type,
                    date=date_str,
                    amount=t.amount,
                    category=t.category,
                    memo=t.memo,
                    tags=tags
                )
                self.repository.append_transaction(new_tx)
                generated_count += 1

        return generated_count

    # --- Input Validation Helpers ---

    def validate_fields(self, date: str, type_str: str, category: str, amount: int):
        self.validate_date_format(date)
        if type_str not in ["income", "expense"]:
            raise ValueError(f"허용되지 않은 타입입니다: {type_str}")
        categories = self.repository.load_categories()
        if category not in categories:
            raise ValueError(f"존재하지 않는 카테고리입니다: {category}")
        if amount <= 0:
            raise ValueError(f"금액은 양수여야 합니다: {amount}")

    def validate_date_format(self, date_str: str):
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"날짜 형식이 올바르지 않습니다 (YYYY-MM-DD): {date_str}")

    def validate_month_format(self, month_str: str):
        try:
            datetime.datetime.strptime(month_str, "%Y-%m")
        except ValueError:
            raise ValueError(f"월 형식이 올바르지 않습니다 (YYYY-MM): {month_str}")
