import io
import os
import unittest
import tempfile
import openpyxl
from decimal import Decimal

from thpay.db.connection import get_db
from thpay.db.migrations import run_migrations
from thpay.admission.service import AdmissionService
from thpay.admission.models import AdmissionRowStatus, BatchStatus
from thpay.esocial.client import ESocialAdmissionClient
from thpay.api.auth import AuthService
from thpay.pipelines.monthly import process_monthly_payroll
from thpay.domain.employee_repository import EmployeeRepository
from thpay.engine.context import CalculationContext

# Gerador de CPFs validos para o teste de 50 colaboradores
def generate_valid_cpf(base_num: int) -> str:
    n = f"{base_num:09d}"
    s1 = sum(int(n[i]) * (10 - i) for i in range(9))
    d1 = 11 - (s1 % 11)
    d1 = 0 if d1 >= 10 else d1
    s2 = sum(int(n[i]) * (11 - i) for i in range(9)) + d1 * 2
    d2 = 11 - (s2 % 11)
    d2 = 0 if d2 >= 10 else d2
    return f"{n}{d1}{d2}"

class TestAdmissionBatch50EndToEnd(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_batch50.db")
        run_migrations(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_complete_50_admissions_scenario(self):
        with get_db(self.db_path) as db:
            company = db.fetchone("SELECT id FROM companies LIMIT 1;")
            user = db.fetchone("SELECT id, email, role FROM users WHERE role = 'RH_OPERADOR' LIMIT 1;")

            # 1. RH cria o lote de 50 admissoes
            batch = AdmissionService.create_batch(
                db=db,
                company_id=company["id"],
                name="Turma Engenharia 50 Contratações - Outubro 2026",
                target_start_date="2026-10-05",
                expected_count=50,
                responsible_user_id=user["id"],
                notes="Admissões em massa do time de tecnologia"
            )
            batch_id = batch["id"]
            self.assertEqual(batch["expected_count"], 50)

            # 2. Gerar planilha XLSX com 50 colaboradores (47 validos e 3 com erros intencionais)
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "COLABORADORES"
            headers = [
                "Nome Completo", "CPF", "Data Nascimento", "E-mail", "Celular",
                "CEP", "Logradouro", "Número", "Bairro", "Cidade", "UF",
                "Cargo", "Salário Base", "Departamento", "Data de Admissão"
            ]
            ws.append(headers)

            for i in range(1, 51):
                cpf = generate_valid_cpf(100000000 + i)
                salary = f"{5000 + (i * 100):.2f}"
                birth = "1994-05-12"

                # 3 Erros intencionais nas linhas 10, 25 e 40:
                if i == 10:
                    cpf = "00000000000" # CPF invalido
                elif i == 25:
                    salary = "-1500,00" # Salario negativo
                elif i == 40:
                    birth = "data_invalida" # Data invalida

                ws.append([
                    f"Colaborador {i:02d} da Silva",
                    cpf,
                    birth,
                    f"colab{i:02d}@techsolutions.com.br",
                    "(11) 98765-4321",
                    "01310-100",
                    "Avenida Paulista",
                    str(1000 + i),
                    "Bela Vista",
                    "São Paulo",
                    "SP",
                    "Engenheiro de Software",
                    salary,
                    "Engenharia de Software",
                    "2026-10-05"
                ])

            xlsx_buffer = io.BytesIO()
            wb.save(xlsx_buffer)
            xlsx_bytes = xlsx_buffer.getvalue()

            # 3. Upload do arquivo XLSX
            upload_res = AdmissionService.upload_spreadsheet(
                db=db,
                batch_id=batch_id,
                filename="turma_50_engenharia.xlsx",
                content_bytes=xlsx_bytes,
                uploaded_by_user_id=user["id"]
            )
            self.assertEqual(upload_res["row_count"], 50)
            self.assertIsNotNone(upload_res["sha256"])

            # 4. Validacao inicial -> Deve detectar exatamente os 3 erros bloqueantes
            val_1 = AdmissionService.validate_batch(db, batch_id)
            self.assertEqual(val_1["status"], BatchStatus.HAS_ERRORS.value)
            self.assertEqual(val_1["total_errors"], 3)

            # 5. Localizar e corrigir os 3 erros inline diretamente no sistema
            rows = AdmissionService.get_batch_rows(db, batch_id, limit=60)
            blocked_rows = [r for r in rows if r["status"] == "bloqueado"]
            self.assertEqual(len(blocked_rows), 3)

            # Correcao da linha 10 (CPF)
            row_10 = [r for r in blocked_rows if "Colaborador 10" in r["parsed"]["full_name"]][0]
            AdmissionService.update_row_data(db, batch_id, row_10["id"], {"cpf": generate_valid_cpf(100000010)})

            # Correcao da linha 25 (Salario)
            row_25 = [r for r in blocked_rows if "Colaborador 25" in r["parsed"]["full_name"]][0]
            AdmissionService.update_row_data(db, batch_id, row_25["id"], {"base_salary": "7500.00"})

            # Correcao da linha 40 (Data de Nascimento)
            row_40 = [r for r in blocked_rows if "Colaborador 40" in r["parsed"]["full_name"]][0]
            AdmissionService.update_row_data(db, batch_id, row_40["id"], {"birth_date": "1992-08-15"})

            # 6. Revalidacao apos correcoes -> 100% de conformidade!
            val_2 = AdmissionService.validate_batch(db, batch_id)
            self.assertEqual(val_2["status"], BatchStatus.READY_FOR_REVIEW.value)
            self.assertEqual(val_2["total_errors"], 0)

            # 7. Aplicar template de contratacao corporativo ao lote
            AdmissionService.apply_batch_template(
                db=db,
                batch_id=batch_id,
                template_values={
                    "contract_type": "CLT",
                    "work_schedule": "40h semanais",
                    "va_split": 50,
                    "bank_name": "Banco do Brasil",
                    "agency": "1234",
                    "account_number": "98765-0"
                }
            )

            # 8. Efetuar commit de todas as 50 linhas para a entidade Admissions
            committed = AdmissionService.commit_batch_to_admissions(db, batch_id, actor_user_id=user["id"])
            self.assertEqual(len(committed), 50)

            # 9. Transmitir eSocial S-2200 para os 50 colaboradores
            admissions = db.fetchall("SELECT id FROM admissions WHERE batch_id = ?;", (batch_id,))
            for adm in admissions:
                esoc_res = ESocialAdmissionClient.submit_s2200(db, adm["id"], actor_user_id=user["id"])
                self.assertEqual(esoc_res["status"], "ACCEPTED")

            # 10. Ativar as 50 admissoes e liberar acessos individuais
            for adm in admissions:
                act_res = AdmissionService.activate_admission(db, adm["id"], actor_user_id=user["id"])
                self.assertEqual(act_res["status"], "admitido")

            # 11. Validar resultados no banco de dados
            batch_summary = AdmissionService.get_batch(db, batch_id)
            self.assertEqual(batch_summary["admitted_count"], 50)

            # 50 colaboradores criados + 5 colaboradores do seed inicial = 55 colaboradores
            total_employees = db.fetchone("SELECT count(*) as c FROM employees WHERE status = 'ACTIVE';")["c"]
            self.assertEqual(total_employees, 55)

            # 50 novos usuarios criados com perfil COLABORADOR_SELF_SERVICE
            colab_users = db.fetchall("SELECT * FROM users WHERE role = 'COLABORADOR_SELF_SERVICE';")
            self.assertEqual(len(colab_users), 55)

            # Verificar que qualquer um dos novos 50 colaboradores consegue efetuar login
            auth_test = AuthService.authenticate(
                db, email="colab01@techsolutions.com.br", password="ThPay@2026"
            )
            self.assertIsNotNone(auth_test)
            logged_user, token = auth_test
            self.assertEqual(logged_user["full_name"], "Colaborador 01 da Silva")
            self.assertEqual(logged_user["role"], "COLABORADOR_SELF_SERVICE")

            # 12. Executar calculo de folha mensal com o motor DAG integrado e verificar que os novos 50 colaboradores sao processados
            contracts = db.fetchall("SELECT id FROM employment_contracts WHERE is_active = 1;")
            self.assertEqual(len(contracts), 55)

            ctx = CalculationContext(competence="2026-10")
            calculated_count = 0
            for c in contracts:
                engine_contract = EmployeeRepository.to_engine_contract(db, c["id"])
                payslip = process_monthly_payroll(engine_contract, ctx)
                self.assertGreater(payslip.net_total, Decimal("0.00"))
                self.assertIsNotNone(payslip.hash_lock)
                calculated_count += 1

            self.assertEqual(calculated_count, 55)

if __name__ == "__main__":
    unittest.main()
