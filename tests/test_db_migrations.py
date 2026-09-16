import os
import unittest
import tempfile
import sqlite3
from thpay.db.connection import get_db, DatabaseConnection
from thpay.db.migrations import run_migrations, hash_password

class TestDatabaseMigrations(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_thpay.db")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_migrations_applied_successfully(self):
        applied = run_migrations(self.db_path)
        self.assertEqual(len(applied), 4)
        self.assertIn("2026.09.01_base_schema", applied)
        self.assertIn("2026.09.02_seed_rbac", applied)
        self.assertIn("2026.09.03_seed_org_and_users", applied)
        self.assertIn("2026.09.04_seed_initial_employees", applied)

        # Rodar novamente nao deve re-aplicar nada (idempotencia)
        second_run = run_migrations(self.db_path)
        self.assertEqual(len(second_run), 0)

        # Verificar tabelas criadas e integridade de dados
        with get_db(self.db_path) as db:
            companies = db.fetchall("SELECT * FROM companies;")
            self.assertEqual(len(companies), 1)
            self.assertEqual(companies[0]["corporate_name"], "Tech Solutions Brasil Ltda")

            branches = db.fetchall("SELECT * FROM branches WHERE company_id = ?;", (companies[0]["id"],))
            self.assertEqual(len(branches), 1)
            self.assertEqual(branches[0]["code"], "0001")

            users = db.fetchall("SELECT * FROM users;")
            self.assertGreaterEqual(len(users), 8)

            roles = db.fetchall("SELECT * FROM roles;")
            self.assertEqual(len(roles), 7)

            contracts = db.fetchall("SELECT * FROM employment_contracts WHERE is_active = 1;")
            self.assertEqual(len(contracts), 5)

if __name__ == "__main__":
    unittest.main()
