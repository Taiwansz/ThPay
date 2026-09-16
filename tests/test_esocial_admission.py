import os
import unittest
import tempfile
from thpay.db.connection import get_db
from thpay.db.migrations import run_migrations
from thpay.admission.service import AdmissionService
from thpay.esocial.client import ESocialAdmissionClient
from thpay.esocial.v1_3.s2190 import EventoS2190_v1_3
from thpay.esocial.v1_3.s2200 import EventoS2200_v1_3

class TestESocialAdmission(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_esocial.db")
        run_migrations(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_s2190_event_generation(self):
        evt = EventoS2190_v1_3.generate(
            cnpj_empregador="12.345.678/0001-90",
            cpf="529.982.247-25",
            data_nascimento="1995-04-12",
            data_admissao="2026-10-01",
            matricula="MAT-725X",
            salario_base=8500.00
        )
        self.assertEqual(evt["event_type"], "S-2190")
        self.assertEqual(evt["version"], "v1_3")
        self.assertIn("<cpfTrab>52998224725</cpfTrab>", evt["xml_payload"])
        self.assertIn("<dtAdm>2026-10-01</dtAdm>", evt["xml_payload"])
        self.assertIn("8500.00", evt["xml_payload"])

    def test_s2200_event_generation(self):
        evt = EventoS2200_v1_3.generate(
            cnpj_empregador="12.345.678/0001-90",
            cpf="529.982.247-25",
            nome="Gabriel Fernandes Santos",
            data_nascimento="1992-06-18",
            data_admissao="2026-10-01",
            matricula="MAT-725X",
            cargo="Engenheiro de Software Sênior",
            cbo="2124-05",
            salario_base=14500.00,
            logradouro="Avenida Paulista",
            numero="1000",
            bairro="Bela Vista",
            cep="01310-100",
            cidade="São Paulo",
            uf="SP"
        )
        self.assertEqual(evt["event_type"], "S-2200")
        self.assertEqual(evt["version"], "v1_3")
        self.assertIn("<cpfTrab>52998224725</cpfTrab>", evt["xml_payload"])
        self.assertIn("<nmTrab>Gabriel Fernandes Santos</nmTrab>", evt["xml_payload"])
        self.assertIn("<cbo>2124-05</cbo>", evt["xml_payload"])
        self.assertIn("14500.00", evt["xml_payload"])

    def test_esocial_submission_gateway(self):
        with get_db(self.db_path) as db:
            company = db.fetchone("SELECT id FROM companies LIMIT 1;")
            user = db.fetchone("SELECT id FROM users WHERE role = 'DP_GESTOR' LIMIT 1;")

            # Criar lote e admissao para teste
            batch = AdmissionService.create_batch(
                db=db,
                company_id=company["id"],
                name="Lote eSocial Teste",
                target_start_date="2026-10-01"
            )
            
            # Linha valida
            csv_data = "Nome Completo;CPF;Data Nascimento;Salario;Cargo;Data Admissao;Email\nMariana Lima;52998224725;1995-04-12;9000,00;Engenheiro de Software;2026-10-01;mariana@test.com"
            AdmissionService.upload_spreadsheet(db, batch["id"], "teste.csv", csv_data.encode("utf-8"))
            AdmissionService.validate_batch(db, batch["id"])
            admissions = AdmissionService.commit_batch_to_admissions(db, batch["id"])
            adm_id = admissions[0]["id"]

            # 1. Transmissao S-2190
            res_2190 = ESocialAdmissionClient.submit_s2190(db, adm_id, actor_user_id=user["id"])
            self.assertEqual(res_2190["event_type"], "S-2190")
            self.assertEqual(res_2190["status"], "ACCEPTED")
            self.assertTrue(res_2190["protocol"].startswith("1.2."))
            self.assertTrue(res_2190["receipt"].endswith("-01"))

            # 2. Transmissao S-2200
            res_2200 = ESocialAdmissionClient.submit_s2200(db, adm_id, actor_user_id=user["id"])
            self.assertEqual(res_2200["event_type"], "S-2200")
            self.assertEqual(res_2200["status"], "ACCEPTED")
            self.assertTrue(res_2200["receipt"].endswith("-02"))

            # Verificar persistencia em esocial_events
            events = db.fetchall("SELECT * FROM esocial_events WHERE admission_id = ? ORDER BY event_type;", (adm_id,))
            self.assertEqual(len(events), 2)
            self.assertEqual(events[0]["status"], "ACCEPTED")
            self.assertEqual(events[1]["status"], "ACCEPTED")

if __name__ == "__main__":
    unittest.main()
