import os
import unittest
import tempfile
from decimal import Decimal

from thpay.db.connection import get_db
from thpay.db.migrations import run_migrations
from thpay.admission.parser import SpreadsheetParser
from thpay.admission.mapper import ColumnMapper
from thpay.admission.validator import AdmissionValidator, validate_cpf, format_cpf
from thpay.admission.service import AdmissionService
from thpay.admission.template_generator import AdmissionTemplateGenerator
from thpay.admission.models import AdmissionRowStatus

class TestAdmissionEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_admission.db")
        run_migrations(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cpf_validation_algorithm(self):
        # Validos
        self.assertTrue(validate_cpf("52998224725"))
        self.assertTrue(validate_cpf("529.982.247-25"))
        self.assertTrue(validate_cpf("11144477735"))
        # Invalidos
        self.assertFalse(validate_cpf("11111111111"))
        self.assertFalse(validate_cpf("12345678901"))
        self.assertFalse(validate_cpf("00000000000"))

    def test_spreadsheet_parsing_and_mapping(self):
        csv_content = """Nome Completo;CPF;Data Nascimento;Salario;Cargo;Data Admissao;Email
Juliana Rocha Prado;52998224725;1995-04-12;7500,00;Engenheiro de Software Pleno;2026-10-01;juliana@test.com
Rodrigo Silveira;11144477735;1990-08-22;6200.00;Analista de Sistemas;2026-10-01;rodrigo@test.com
"""
        headers, rows = SpreadsheetParser.parse("teste.csv", csv_content.encode("utf-8"))
        self.assertEqual(len(headers), 7)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["Nome Completo"], "Juliana Rocha Prado")

        # Auto-mapeamento
        mapping = ColumnMapper.suggest_mapping(headers)
        self.assertEqual(mapping["Nome Completo"], "full_name")
        self.assertEqual(mapping["CPF"], "cpf")
        self.assertEqual(mapping["Data Nascimento"], "birth_date")
        self.assertEqual(mapping["Salario"], "base_salary")
        self.assertEqual(mapping["Cargo"], "position_title")
        self.assertEqual(mapping["Data Admissao"], "hire_date")

    def test_admission_batch_lifecycle_and_in_place_editing(self):
        with get_db(self.db_path) as db:
            company = db.fetchone("SELECT id FROM companies LIMIT 1;")
            user = db.fetchone("SELECT id FROM users WHERE role = 'RH_OPERADOR' LIMIT 1;")

            # 1. Criar Lote
            batch = AdmissionService.create_batch(
                db=db,
                company_id=company["id"],
                name="Turma Engenharia Outubro 2026",
                target_start_date="2026-10-01",
                expected_count=2,
                responsible_user_id=user["id"]
            )
            batch_id = batch["id"]
            self.assertEqual(batch["status"], "DRAFT")

            # 2. Upload com 1 linha valida e 1 linha com erro de CPF para teste de correcao
            csv_data = """Nome Completo;CPF;Data Nascimento;Salario;Cargo;Data Admissao;Email
Ana Carolina Lima;52998224725;1996-05-10;8500,00;Engenheiro de Software;2026-10-01;ana.lima@test.com
Bruno Mendonça;00000000000;1992-11-15;7000,00;Analista de Dados;2026-10-01;bruno@test.com
"""
            upload_res = AdmissionService.upload_spreadsheet(
                db=db,
                batch_id=batch_id,
                filename="turma.csv",
                content_bytes=csv_data.encode("utf-8"),
                uploaded_by_user_id=user["id"]
            )
            self.assertEqual(upload_res["row_count"], 2)

            # 3. Validar Lote
            val_res = AdmissionService.validate_batch(db, batch_id)
            self.assertEqual(val_res["status"], "HAS_ERRORS")
            self.assertEqual(val_res["total_errors"], 1) # Bruno com CPF 00000000000

            # Verificar linhas
            rows = AdmissionService.get_batch_rows(db, batch_id)
            self.assertEqual(len(rows), 2)
            row_bruno = [r for r in rows if "Bruno" in r["parsed"]["full_name"]][0]
            self.assertEqual(row_bruno["status"], "bloqueado")
            self.assertEqual(len(row_bruno["issues"]), 1)
            self.assertEqual(row_bruno["issues"][0]["error_code"], "INVALID_CPF")

            # 4. Correcao inline diretamente no sistema sem re-upload
            fix_res = AdmissionService.update_row_data(
                db=db,
                batch_id=batch_id,
                row_id=row_bruno["id"],
                updated_fields={"cpf": "11144477735"} # CPF valido
            )
            self.assertIn(fix_res["status"], ["pronto para pré-admissão", "pronto para eSocial", "com alerta"])
            self.assertEqual(fix_res["error_count"], 0)

            # 5. Revalidar lote todo
            val_res2 = AdmissionService.validate_batch(db, batch_id)
            self.assertEqual(val_res2["status"], "READY_FOR_REVIEW")
            self.assertEqual(val_res2["total_errors"], 0)

            # 6. Commit para Admissoes
            committed = AdmissionService.commit_batch_to_admissions(db, batch_id, actor_user_id=user["id"])
            self.assertEqual(len(committed), 2)

            # 7. Gerar Convite de Pre-Admissao para Ana
            admissions = db.fetchall("SELECT * FROM admissions WHERE batch_id = ?;", (batch_id,))
            adm_ana = [a for a in admissions if "Ana" in a["candidate_name"]][0]
            invite = AdmissionService.generate_pre_admission_invite(db, adm_ana["id"], actor_user_id=user["id"])
            self.assertIsNotNone(invite["token"])
            self.assertIn("/portal/pre-admissao?token=", invite["invite_link"])

            # 8. Candidato preenche dados via Portal de Pre-Admissao
            submit_res = AdmissionService.submit_pre_admission_self_service(
                db,
                token=invite["token"],
                self_service_data={
                    "street": "Rua Augusta",
                    "number": "500",
                    "zip_code": "01305-000",
                    "city": "São Paulo",
                    "state": "SP",
                    "bank_name": "Itaú Unibanco",
                    "agency": "4321",
                    "account_number": "12345-6",
                    "va_split": 60
                }
            )
            self.assertEqual(submit_res["status"], "pronto para eSocial")

            # 9. Ativar Admissao
            act_res = AdmissionService.activate_admission(db, adm_ana["id"], actor_user_id=user["id"])
            self.assertEqual(act_res["status"], "admitido")
            self.assertIsNotNone(act_res["employee_id"])
            self.assertIsNotNone(act_res["contract_id"])

            # Verificar se colaborador agora esta ativo e possui usuario provisionado
            emp = db.fetchone("SELECT * FROM employees WHERE id = ?;", (act_res["employee_id"],))
            self.assertEqual(emp["status"], "ACTIVE")
            self.assertEqual(emp["full_name"], "Ana Carolina Lima")

            usr = db.fetchone("SELECT * FROM users WHERE employee_id = ?;", (act_res["employee_id"],))
            self.assertIsNotNone(usr)
            self.assertEqual(usr["role"], "COLABORADOR_SELF_SERVICE")

            tasks = db.fetchall("SELECT * FROM admission_tasks WHERE admission_id = ?;", (adm_ana["id"],))
            self.assertGreaterEqual(len(tasks), 4)

if __name__ == "__main__":
    unittest.main()
