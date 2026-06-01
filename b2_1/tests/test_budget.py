import os
import shutil
import unittest
import unittest.mock
import tempfile
import csv
from typing import Generator
from budget_app.models import Transaction, RecurringTemplate
from budget_app.repository import FileRepository
from budget_app.service import BudgetService

class TestBudgetApp(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.repository = FileRepository(self.test_dir)
        self.service = BudgetService(self.repository)

    def tearDown(self):
        # Clean up files
        shutil.rmtree(self.test_dir)

    def test_default_categories(self):
        # Categories should be initialized with default list
        cats = self.service.list_categories()
        self.assertIn("food", cats)
        self.assertIn("transport", cats)
        self.assertIn("salary", cats)

    def test_add_and_list_transactions(self):
        # Add transactions
        tx_id1 = self.service.add_transaction(
            date="2024-01-15",
            type_str="expense",
            category="food",
            amount=15000,
            memo="점심",
            tags=["meal"]
        )
        self.assertEqual(tx_id1, "TX-000001")

        tx_id2 = self.service.add_transaction(
            date="2024-01-16",
            type_str="income",
            category="salary",
            amount=3000000,
            memo="월급",
            tags=["monthly"]
        )
        self.assertEqual(tx_id2, "TX-000002")

        # List transactions (limit 1) - newest first (TX-000002 has a later date and higher ID)
        txs = self.service.list_transactions(limit=1)
        self.assertEqual(len(txs), 1)
        self.assertEqual(txs[0].id, "TX-000002")

        # List all (limit 10)
        txs_all = self.service.list_transactions(limit=10)
        self.assertEqual(len(txs_all), 2)
        self.assertEqual(txs_all[0].id, "TX-000002")
        self.assertEqual(txs_all[1].id, "TX-000001")

    def test_search_transactions(self):
        self.service.add_transaction("2024-01-15", "expense", "food", 15000, "점심", ["meal"])
        self.service.add_transaction("2024-01-16", "income", "salary", 3000000, "월급", ["monthly"])
        self.service.add_transaction("2024-02-01", "expense", "rent", 500000, "월세", ["monthly", "home"])

        # Search by type
        expense_txs = self.service.search_transactions(type_str="expense")
        self.assertEqual(len(expense_txs), 2)

        # Search by tag
        monthly_txs = self.service.search_transactions(tag="monthly")
        self.assertEqual(len(monthly_txs), 2)

        # Search by date range
        january_txs = self.service.search_transactions(from_date="2024-01-01", to_date="2024-01-31")
        self.assertEqual(len(january_txs), 2)

        # Search by query string
        lunch_txs = self.service.search_transactions(query="점심")
        self.assertEqual(len(lunch_txs), 1)

    def test_update_and_delete_transaction(self):
        tx_id = self.service.add_transaction("2024-01-15", "expense", "food", 15000, "점심", ["meal"])
        
        # Update
        success = self.service.update_transaction(tx_id, "2024-01-15", "expense", "food", 16000, "점심(식대)", ["meal", "updated"])
        self.assertTrue(success)
        
        # Check if updated
        txs = self.service.list_transactions(1)
        self.assertEqual(txs[0].amount, 16000)
        self.assertEqual(txs[0].memo, "점심(식대)")
        self.assertIn("updated", txs[0].tags)

        # Delete
        success_del = self.service.delete_transaction(tx_id)
        self.assertTrue(success_del)

        txs_after = self.service.list_transactions(1)
        self.assertEqual(len(txs_after), 0)

    def test_category_validation_and_safety(self):
        # Adding invalid transaction category should raise ValueError
        with self.assertRaises(ValueError):
            self.service.add_transaction("2024-01-15", "expense", "invalid_cat", 1000, "", [])

        # Add category
        self.service.add_category("custom_cat")
        self.assertIn("custom_cat", self.service.list_categories())

        # Should be able to add transaction now
        tx_id = self.service.add_transaction("2024-01-15", "expense", "custom_cat", 1000, "", [])
        self.assertIsNotNone(tx_id)

        # Removing a category in use should fail
        with self.assertRaises(ValueError):
            self.service.remove_category("custom_cat")

        # Deleting the transaction using it should allow category removal
        self.service.delete_transaction(tx_id)
        success_remove = self.service.remove_category("custom_cat")
        self.assertTrue(success_remove)
        self.assertNotIn("custom_cat", self.service.list_categories())

    def test_monthly_summary_and_budget(self):
        # Monthly summary with no data
        summary_empty = self.service.get_monthly_summary("2024-01", 3)
        self.assertFalse(summary_empty["has_data"])

        # Add budget
        self.service.set_budget("2024-01", 20000)

        # Add transactions
        self.service.add_transaction("2024-01-10", "expense", "food", 15000, "점심", [])
        self.service.add_transaction("2024-01-11", "expense", "transport", 10000, "버스", [])
        self.service.add_transaction("2024-01-12", "income", "salary", 50000, "아르바이트", [])

        summary = self.service.get_monthly_summary("2024-01", 3)
        self.assertTrue(summary["has_data"])
        self.assertEqual(summary["total_income"], 50000)
        self.assertEqual(summary["total_expense"], 25000)
        self.assertEqual(summary["balance"], 25000)
        self.assertEqual(summary["budget"], 20000)
        
        # Check TOP categories sorting
        self.assertEqual(len(summary["top_categories"]), 2)
        self.assertEqual(summary["top_categories"][0][0], "food")
        self.assertEqual(summary["top_categories"][0][1], 15000)

    def test_csv_import_export(self):
        self.service.add_transaction("2024-01-15", "expense", "food", 15000, "점심", ["meal"])
        self.service.add_transaction("2024-01-16", "income", "salary", 3000000, "월급", ["monthly"])

        csv_path = os.path.join(self.test_dir, "export.csv")
        
        # Export
        count = self.service.export_to_csv(csv_path, month="2024-01")
        self.assertEqual(count, 2)
        
        # Verify CSV content
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(header, ["date", "type", "category", "amount", "memo", "tags"])
            
            row1 = next(reader)
            # In exported output, order depends on streaming order (chronological, so TX-000001 then TX-000002)
            self.assertEqual(row1, ["2024-01-15", "expense", "food", "15000", "점심", "meal"])

        # Import CSV
        new_test_dir = tempfile.mkdtemp()
        try:
            new_repo = FileRepository(new_test_dir)
            new_service = BudgetService(new_repo)
            
            imported, skipped = new_service.import_from_csv(csv_path)
            self.assertEqual(imported, 2)
            self.assertEqual(skipped, 0)
            
            new_txs = new_service.list_transactions(5)
            self.assertEqual(len(new_txs), 2)
        finally:
            shutil.rmtree(new_test_dir)

    def test_recurring_transactions(self):
        # Add templates
        t_id1 = self.service.add_recurring_template(
            type_str="expense",
            category_str="rent",
            amount=500000,
            day=25,
            memo="월세",
            tags=["home"]
        )
        self.assertEqual(t_id1, "REC-000001")

        t_id2 = self.service.add_recurring_template(
            type_str="income",
            category_str="salary",
            amount=3000000,
            day=20,
            memo="기본급",
            tags=["monthly"]
        )
        self.assertEqual(t_id2, "REC-000002")

        # Generate recurring for month 2024-01
        count = self.service.generate_recurring_transactions("2024-01")
        self.assertEqual(count, 2)

        # Check transactions are generated
        txs = self.service.list_transactions(10)
        self.assertEqual(len(txs), 2)
        # Should be ordered newest first (rent on 25th, then salary on 20th)
        self.assertEqual(txs[0].category, "rent")
        self.assertEqual(txs[0].date, "2024-01-25")
        self.assertEqual(txs[1].category, "salary")
        self.assertEqual(txs[1].date, "2024-01-20")

        # Running again for same month should generate 0 (due to duplicate prevention)
        count_dup = self.service.generate_recurring_transactions("2024-01")
        self.assertEqual(count_dup, 0)

        # Generate for different month (2024-02) should work
        count_next = self.service.generate_recurring_transactions("2024-02")
        self.assertEqual(count_next, 2)

    @unittest.mock.patch('sys.stdin.isatty', return_value=True)
    @unittest.mock.patch('sys.stdin.fileno', return_value=0)
    @unittest.mock.patch('termios.tcgetattr', return_value=[1, 2, 3, 4, 5, 6, 7])
    @unittest.mock.patch('termios.tcsetattr', return_value=None)
    @unittest.mock.patch('tty.setraw', return_value=None)
    def test_prompt_choices_arrow_cycling(self, mock_setraw, mock_tcsetattr, mock_tcgetattr, mock_fileno, mock_isatty):
        import unittest.mock
        from budget_app.cli import prompt_choices

        choices = ["food", "transport", "rent"]

        # Case 1: Empty -> Right -> Right -> Enter (should return "transport")
        seq1 = ['\x1b', '[', 'C', '\x1b', '[', 'C', '\n']
        with unittest.mock.patch('sys.stdin.read', side_effect=lambda n: seq1.pop(0)), \
             unittest.mock.patch('sys.stdout.write'):
            self.assertEqual(prompt_choices("Prompt: ", choices), "transport")

        # Case 2: Empty -> Left -> Left -> Enter (should return "transport" from rent -> transport)
        seq2 = ['\x1b', '[', 'D', '\x1b', '[', 'D', '\n']
        with unittest.mock.patch('sys.stdin.read', side_effect=lambda n: seq2.pop(0)), \
             unittest.mock.patch('sys.stdout.write'):
            self.assertEqual(prompt_choices("Prompt: ", choices), "transport")

        # Case 3: Type 'f' -> Right -> Enter (should return "food")
        seq3 = ['f', '\x1b', '[', 'C', '\n']
        with unittest.mock.patch('sys.stdin.read', side_effect=lambda n: seq3.pop(0)), \
             unittest.mock.patch('sys.stdout.write'):
            self.assertEqual(prompt_choices("Prompt: ", choices), "food")

        # Case 4: Type 'f' -> Left -> Enter (should return "rent" because cycling backward from 'food')
        seq4 = ['f', '\x1b', '[', 'D', '\n']
        with unittest.mock.patch('sys.stdin.read', side_effect=lambda n: seq4.pop(0)), \
             unittest.mock.patch('sys.stdout.write'):
            self.assertEqual(prompt_choices("Prompt: ", choices), "rent")

        # Case 5: Type 'f' -> Tab -> Enter (should return "food")
        seq5 = ['f', '\t', '\n']
        with unittest.mock.patch('sys.stdin.read', side_effect=lambda n: seq5.pop(0)), \
             unittest.mock.patch('sys.stdout.write'):
            self.assertEqual(prompt_choices("Prompt: ", choices), "food")

        # Case 6: Type 'xyz' -> Right -> Enter (no match -> defaults to 'food')
        seq6 = ['x', 'y', 'z', '\x1b', '[', 'C', '\n']
        with unittest.mock.patch('sys.stdin.read', side_effect=lambda n: seq6.pop(0)), \
             unittest.mock.patch('sys.stdout.write'):
            self.assertEqual(prompt_choices("Prompt: ", choices), "food")

    @unittest.mock.patch('sys.stdin.isatty', return_value=True)
    @unittest.mock.patch('sys.stdin.fileno', return_value=0)
    @unittest.mock.patch('termios.tcgetattr', return_value=[1, 2, 3, 4, 5, 6, 7])
    @unittest.mock.patch('termios.tcsetattr', return_value=None)
    @unittest.mock.patch('tty.setraw', return_value=None)
    def test_prompt_choices_default_prefill(self, mock_setraw, mock_tcsetattr, mock_tcgetattr, mock_fileno, mock_isatty):
        import unittest.mock
        from budget_app.cli import prompt_choices

        choices = ["food", "transport", "rent"]

        # Case 1: Default is "food" -> Enter immediately -> returns "food"
        seq1 = ['\n']
        with unittest.mock.patch('sys.stdin.read', side_effect=lambda n: seq1.pop(0)), \
             unittest.mock.patch('sys.stdout.write'):
            self.assertEqual(prompt_choices("Prompt: ", choices, default_value="food"), "food")

        # Case 2: Default is "food" -> Type "r" -> should clear default and write "r" -> Tab -> Enter (should return "rent")
        seq2 = ['r', '\t', '\n']
        with unittest.mock.patch('sys.stdin.read', side_effect=lambda n: seq2.pop(0)), \
             unittest.mock.patch('sys.stdout.write'):
            self.assertEqual(prompt_choices("Prompt: ", choices, default_value="food"), "rent")

        # Case 3: Default is "food" -> Backspace (clears completely) -> Type "t" -> Tab -> Enter (should return "transport")
        seq3 = ['\x7f', 't', '\t', '\n']
        with unittest.mock.patch('sys.stdin.read', side_effect=lambda n: seq3.pop(0)), \
             unittest.mock.patch('sys.stdout.write'):
            self.assertEqual(prompt_choices("Prompt: ", choices, default_value="food"), "transport")

    @unittest.mock.patch('sys.stdin.isatty', return_value=True)
    @unittest.mock.patch('sys.stdin.fileno', return_value=0)
    @unittest.mock.patch('termios.tcgetattr', return_value=[1, 2, 3, 4, 5, 6, 7])
    @unittest.mock.patch('termios.tcsetattr', return_value=None)
    @unittest.mock.patch('tty.setraw', return_value=None)
    def test_prompt_main_command_cycling_and_history(self, mock_setraw, mock_tcsetattr, mock_tcgetattr, mock_fileno, mock_isatty):
        import unittest.mock
        from budget_app.cli import InteractiveShell
        
        shell = InteractiveShell(self.service)
        shell.commands = ["add", "list", "exit"]
        shell.history = ["help", "list 5"]
        
        # Scenario 1: Empty -> Right (should go to first choice "add") -> Right (should go to "list") -> Enter
        seq1 = ['\x1b', '[', 'C', '\x1b', '[', 'C', '\n']
        with unittest.mock.patch('sys.stdin.read', side_effect=lambda n: seq1.pop(0)), \
             unittest.mock.patch('sys.stdout.write'):
            self.assertEqual(shell.prompt_main_command("budget_app> "), "list")
            
        # The prompt will automatically append "list" to history
        self.assertEqual(shell.history[-1], "list")
        
        # Scenario 2: Up (should browse history "list") -> Up (should browse "list 5") -> Up (should browse "help") -> Enter
        seq2 = ['\x1b', '[', 'A', '\x1b', '[', 'A', '\x1b', '[', 'A', '\n']
        with unittest.mock.patch('sys.stdin.read', side_effect=lambda n: seq2.pop(0)), \
             unittest.mock.patch('sys.stdout.write'):
            self.assertEqual(shell.prompt_main_command("budget_app> "), "help")

if __name__ == "__main__":
    unittest.main()
