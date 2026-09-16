import os
import unittest
import tempfile
from thpay.db.connection import get_db
from thpay.db.migrations import run_migrations
from thpay.api.auth import AuthService
from thpay.api.rbac import RBACManager

class TestAuthAndRBAC(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_auth.db")
        run_migrations(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_authentication_flow(self):
        with get_db(self.db_path) as db:
            # 1. Login com senha correta
            res = AuthService.authenticate(db, "dp@techsolutions.com.br", "ThPay@2026", ip_address="127.0.0.1")
            self.assertIsNotNone(res)
            user, token = res
            self.assertEqual(user["email"], "dp@techsolutions.com.br")
            self.assertEqual(user["role"], "DP_GESTOR")
            self.assertIn("employee.*", user["permissions"])

            # 2. Login com senha errada
            fail = AuthService.authenticate(db, "dp@techsolutions.com.br", "WrongPassword")
            self.assertIsNone(fail)

            # 3. Validacao de token ativo
            verified_user = AuthService.verify_token(db, token)
            self.assertIsNotNone(verified_user)
            self.assertEqual(verified_user["id"], user["id"])

            # 4. Logout revoga sessao
            AuthService.logout(db, token)
            revoked = AuthService.verify_token(db, token)
            self.assertIsNone(revoked)

    def test_rbac_permissions(self):
        # Super admin
        super_user = {"role": "SUPER_ADMIN", "permissions": ["*"]}
        self.assertTrue(RBACManager.has_permission(super_user, "anything"))

        # DP Gestor com wildcard employee.*
        dp_user = {"role": "DP_GESTOR", "permissions": ["employee.*", "payroll.*"]}
        self.assertTrue(RBACManager.has_permission(dp_user, "employee.read"))
        self.assertTrue(RBACManager.has_permission(dp_user, "employee.create"))
        self.assertTrue(RBACManager.has_permission(dp_user, "payroll.calculate"))
        self.assertFalse(RBACManager.has_permission(dp_user, "audit.export"))

        # Colaborador Self-service
        colab_user = {"role": "COLABORADOR_SELF_SERVICE", "employee_id": "emp-001", "permissions": ["self.read"]}
        self.assertFalse(RBACManager.has_permission(colab_user, "payroll.calculate"))

        # Enforce Scope
        self.assertTrue(RBACManager.enforce_employee_scope(colab_user, "emp-001"))
        self.assertFalse(RBACManager.enforce_employee_scope(colab_user, "emp-002"))
        self.assertTrue(RBACManager.enforce_employee_scope(dp_user, "emp-002"))

if __name__ == "__main__":
    unittest.main()
