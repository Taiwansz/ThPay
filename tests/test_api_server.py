import json
import os
import threading
import unittest
import tempfile
import urllib.request
import urllib.error
from http.server import HTTPServer

from thpay.db.connection import get_db, DatabaseConnection
from thpay.db.migrations import run_migrations
from thpay.api.server import ThPayRequestHandler

class TestAPIServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.temp_dir.name, "test_api.db")
        run_migrations(cls.db_path)
        os.environ["DATABASE_PATH"] = cls.db_path

        cls.server = HTTPServer(("127.0.0.1", 0), ThPayRequestHandler)
        cls.port = cls.server.server_port
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.temp_dir.cleanup()

    def make_request(self, method: str, path: str, data: dict = None, token: str = None):
        url = f"{self.base_url}{path}"
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        body = json.dumps(data).encode("utf-8") if data else None
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.status
                raw = resp.read().decode("utf-8")
                return status, json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8")
            return e.code, json.loads(raw) if raw else None

    def test_health_check(self):
        status, data = self.make_request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "ok")

    def test_auth_and_protected_endpoints(self):
        # 1. Login
        status, login_res = self.make_request("POST", "/api/v1/auth/login", {
            "email": "dp@techsolutions.com.br",
            "password": "ThPay@2026"
        })
        self.assertEqual(status, 200)
        self.assertIn("token", login_res)
        token = login_res["token"]

        # 2. Obter usuario logado /auth/me
        status, me_res = self.make_request("GET", "/api/v1/auth/me", token=token)
        self.assertEqual(status, 200)
        self.assertEqual(me_res["user"]["email"], "dp@techsolutions.com.br")

        # 3. Listar colaboradores
        status, emps = self.make_request("GET", "/api/v1/employees", token=token)
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(emps), 5)

        # 4. Criar lote de admissao via API
        status, batch = self.make_request("POST", "/api/v1/admission-batches", {
            "name": "Turma API Teste",
            "target_start_date": "2026-11-01",
            "expected_count": 10
        }, token=token)
        self.assertEqual(status, 201)
        self.assertEqual(batch["name"], "Turma API Teste")

        # 5. Listar lotes de admissao
        status, batches = self.make_request("GET", "/api/v1/admission-batches", token=token)
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(batches), 1)

        # 6. Executar calculo de folha mensal via API
        status, payroll_res = self.make_request("POST", "/api/v1/payroll/calculate", {
            "competence": "2026-09"
        }, token=token)
        self.assertEqual(status, 200)
        self.assertEqual(payroll_res["status"], "CALCULATED")
        self.assertGreater(payroll_res["total_gross"], 0)

        # 7. Consultar trilha de auditoria
        status, audit = self.make_request("GET", "/api/v1/audit-trail", token=token)
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(audit), 1)

if __name__ == "__main__":
    unittest.main()
