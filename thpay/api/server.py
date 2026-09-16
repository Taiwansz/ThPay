import io
import os
import re
import json
import uuid
import base64
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Callable, Dict, List, Optional, Tuple

from thpay.db.connection import get_db
from thpay.db.migrations import run_migrations
from thpay.api.auth import AuthService
from thpay.api.rbac import RBACManager
from thpay.domain.organization import OrganizationService
from thpay.domain.employee_repository import EmployeeRepository
from thpay.admission.service import AdmissionService
from thpay.admission.template_generator import AdmissionTemplateGenerator
from thpay.esocial.client import ESocialAdmissionClient
from thpay.audit.logger import AuditLogger
from thpay.pipelines.monthly import process_monthly_payroll
from thpay.engine.context import CalculationContext

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ui")

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class ThPayRequestHandler(BaseHTTPRequestHandler):
    def send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, default=str, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Correlation-ID")
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message: str, status: int = 400):
        self.send_json({"error": message, "status": status}, status=status)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Correlation-ID")
        self.end_headers()

    def get_auth_user(self, db) -> Optional[Dict[str, Any]]:
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            raw_token = auth_header[7:].strip()
            return AuthService.verify_token(db, raw_token)
        return None

    def read_json_body(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            raw = self.rfile.read(content_length)
            return json.loads(raw.decode("utf-8"))
        return {}

    def serve_static(self, path: str):
        safe_path = path.lstrip("/") or "index.html"
        full_path = os.path.join(STATIC_DIR, safe_path)
        if not os.path.exists(full_path) or os.path.isdir(full_path):
            full_path = os.path.join(STATIC_DIR, "index.html")

        content_type = "text/html; charset=utf-8"
        if full_path.endswith(".css"):
            content_type = "text/css; charset=utf-8"
        elif full_path.endswith(".js"):
            content_type = "application/javascript; charset=utf-8"
        elif full_path.endswith(".svg"):
            content_type = "image/svg+xml"
        elif full_path.endswith(".png"):
            content_type = "image/png"
        elif full_path.endswith(".json"):
            content_type = "application/json"

        with open(full_path, "rb") as f:
            content = f.read()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if not path.startswith("/api/"):
            self.serve_static(path)
            return

        with get_db() as db:
            user = self.get_auth_user(db)

            # Health check
            if path == "/api/health":
                self.send_json({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat(), "service": "ThPay API v1"})
                return

            # Download template oficial de admissao
            if path == "/api/v1/admission-template/download":
                fmt = query.get("format", ["xlsx"])[0].lower()
                if fmt == "csv":
                    csv_data = AdmissionTemplateGenerator.generate_csv()
                    body = csv_data.encode("utf-8-sig")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/csv; charset=utf-8")
                    self.send_header("Content-Disposition", 'attachment; filename="thpay_admissoes_v1.0.csv"')
                    self.send_header("Content-Length", str(len(body)))
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(body)
                else:
                    xlsx_bytes = AdmissionTemplateGenerator.generate_xlsx()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    self.send_header("Content-Disposition", 'attachment; filename="thpay_admissoes_v1.0.xlsx"')
                    self.send_header("Content-Length", str(len(xlsx_bytes)))
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(xlsx_bytes)
                return

            # Pre-admissao publica pelo token do candidato
            match_pre = re.match(r"^/api/v1/pre-admission/([^/]+)$", path)
            if match_pre:
                token = match_pre.group(1)
                now_str = datetime.now(timezone.utc).isoformat()
                adm = db.fetchone(
                    "SELECT * FROM admissions WHERE pre_admission_token = ? AND pre_admission_token_expires_at > ?;",
                    (token, now_str)
                )
                if not adm:
                    self.send_error_json("Link de pré-admissão inválido ou expirado.", 404)
                    return
                row_data = {}
                if adm.get("row_id"):
                    row = db.fetchone("SELECT parsed_data_json FROM admission_rows WHERE id = ?;", (adm["row_id"],))
                    if row:
                        row_data = json.loads(row["parsed_data_json"])
                self.send_json({
                    "admission_id": adm["id"],
                    "candidate_name": adm["candidate_name"],
                    "candidate_cpf": adm["candidate_cpf"],
                    "candidate_email": adm["candidate_email"],
                    "current_data": row_data
                })
                return

            # Rotas autenticadas
            if not user:
                self.send_error_json("Não autenticado. Forneça o token Bearer.", 401)
                return

            # Auth ME
            if path == "/api/v1/auth/me":
                comp = OrganizationService.get_company(db, user["company_id"]) if user.get("company_id") else None
                self.send_json({"user": user, "company": comp})
                return

            # Organizacao
            if path == "/api/v1/companies":
                comps = OrganizationService.list_companies(db, user.get("tenant_id"))
                self.send_json(comps)
                return

            if path == "/api/v1/branches":
                branches = OrganizationService.list_branches(db, user["company_id"])
                self.send_json(branches)
                return

            if path == "/api/v1/departments":
                depts = OrganizationService.list_departments(db, user["company_id"])
                self.send_json(depts)
                return

            if path == "/api/v1/cost-centers":
                ccs = OrganizationService.list_cost_centers(db, user["company_id"])
                self.send_json(ccs)
                return

            if path == "/api/v1/positions":
                positions = OrganizationService.list_positions(db, user["company_id"])
                self.send_json(positions)
                return

            # Colaboradores
            if path == "/api/v1/employees":
                if not RBACManager.has_permission(user, "employee.read"):
                    self.send_error_json("Acesso não autorizado.", 403)
                    return
                search = query.get("search", [None])[0]
                status_filter = query.get("status", [None])[0]
                limit = int(query.get("limit", [50])[0])
                offset = int(query.get("offset", [0])[0])
                emps = EmployeeRepository.list_employees(
                    db, user["company_id"], search=search, status=status_filter, limit=limit, offset=offset
                )
                self.send_json(emps)
                return

            match_emp = re.match(r"^/api/v1/employees/([^/]+)$", path)
            if match_emp:
                emp_id = match_emp.group(1)
                if not RBACManager.enforce_employee_scope(user, emp_id):
                    self.send_error_json("Acesso negado aos dados de outro colaborador.", 403)
                    return
                emp_detail = EmployeeRepository.get_employee_detail(db, emp_id)
                if not emp_detail:
                    self.send_error_json("Colaborador não encontrado.", 404)
                    return
                self.send_json(emp_detail)
                return

            # Lotes de Admissao
            if path == "/api/v1/admission-batches":
                if not RBACManager.has_permission(user, "admission.manage"):
                    self.send_error_json("Acesso não autorizado ao módulo de admissão.", 403)
                    return
                batches = AdmissionService.list_batches(db, user["company_id"])
                self.send_json(batches)
                return

            match_batch = re.match(r"^/api/v1/admission-batches/([^/]+)$", path)
            if match_batch:
                batch_id = match_batch.group(1)
                batch = AdmissionService.get_batch(db, batch_id)
                if not batch:
                    self.send_error_json("Lote não encontrado.", 404)
                    return
                self.send_json(batch)
                return

            match_batch_rows = re.match(r"^/api/v1/admission-batches/([^/]+)/rows$", path)
            if match_batch_rows:
                batch_id = match_batch_rows.group(1)
                status_filter = query.get("status", [None])[0]
                limit = int(query.get("limit", [100])[0])
                offset = int(query.get("offset", [0])[0])
                rows = AdmissionService.get_batch_rows(db, batch_id, status_filter=status_filter, limit=limit, offset=offset)
                self.send_json(rows)
                return

            # Trilha de Auditoria
            if path == "/api/v1/audit-trail":
                if not RBACManager.has_permission(user, "audit.read"):
                    self.send_error_json("Acesso não autorizado à auditoria.", 403)
                    return
                entity_type = query.get("entity_type", [None])[0]
                action = query.get("action", [None])[0]
                limit = int(query.get("limit", [50])[0])
                offset = int(query.get("offset", [0])[0])
                events = AuditLogger.query(db, entity_type=entity_type, action=action, company_id=user.get("company_id"), limit=limit, offset=offset)
                self.send_json(events)
                return

            # Folha de Pagamento - Historico e holerites
            if path == "/api/v1/payroll/runs":
                runs = db.fetchall(
                    "SELECT * FROM payroll_runs WHERE company_id = ? ORDER BY competence DESC;",
                    (user["company_id"],)
                )
                self.send_json(runs)
                return

            match_payslip = re.match(r"^/api/v1/payroll/payslips/([^/]+)$", path)
            if match_payslip:
                target_emp_id = match_payslip.group(1)
                if not RBACManager.enforce_employee_scope(user, target_emp_id):
                    self.send_error_json("Acesso negado ao holerite de outro colaborador.", 403)
                    return
                payslips = db.fetchall(
                    "SELECT * FROM payslips WHERE employee_id = ? ORDER BY competence DESC;",
                    (target_emp_id,)
                )
                for p in payslips:
                    p["items"] = json.loads(p["items_json"])
                self.send_json(payslips)
                return

            self.send_error_json("Rota não encontrada.", 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.read_json_body()

        with get_db() as db:
            user = self.get_auth_user(db)

            # 1. Login
            if path == "/api/v1/auth/login":
                email = body.get("email", "")
                password = body.get("password", "")
                auth_res = AuthService.authenticate(
                    db, email=email, password=password, ip_address=self.client_address[0]
                )
                if not auth_res:
                    self.send_error_json("Credenciais corporativas inválidas.", 401)
                    return
                user_dict, token = auth_res
                AuditLogger.record(
                    db=db,
                    actor_user_id=user_dict["id"],
                    actor_email=user_dict["email"],
                    actor_role=user_dict["role"],
                    company_id=user_dict.get("company_id"),
                    tenant_id=user_dict.get("tenant_id"),
                    action="auth.login",
                    entity_type="user",
                    entity_id=user_dict["id"],
                    ip_address=self.client_address[0],
                    reason="Login autenticado com sucesso"
                )
                self.send_json({"token": token, "user": user_dict})
                return

            # 2. Submissao publica de Pre-Admissao (candidato)
            match_pre_submit = re.match(r"^/api/v1/pre-admission/([^/]+)/submit$", path)
            if match_pre_submit:
                token = match_pre_submit.group(1)
                try:
                    res = AdmissionService.submit_pre_admission_self_service(db, token, body)
                    self.send_json(res)
                except Exception as e:
                    self.send_error_json(str(e), 400)
                return

            # Demais rotas exigem usuario autenticado
            if not user:
                self.send_error_json("Não autenticado.", 401)
                return

            # Logout
            if path == "/api/v1/auth/logout":
                auth_header = self.headers.get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    AuthService.logout(db, auth_header[7:].strip())
                self.send_json({"success": True, "message": "Sessão encerrada com sucesso."})
                return

            # Criar Lote de Admissao
            if path == "/api/v1/admission-batches":
                if not RBACManager.has_permission(user, "admission.manage"):
                    self.send_error_json("Acesso não autorizado.", 403)
                    return
                name = body.get("name")
                target_date = body.get("target_start_date")
                if not name or not target_date:
                    self.send_error_json("Nome do lote e data de início são obrigatórios.", 400)
                    return
                batch = AdmissionService.create_batch(
                    db=db,
                    company_id=user["company_id"],
                    name=name,
                    target_start_date=target_date,
                    branch_id=body.get("branch_id"),
                    expected_count=int(body.get("expected_count", 1)),
                    responsible_user_id=user["id"],
                    notes=body.get("notes")
                )
                self.send_json(batch, status=201)
                return

            # Upload de Planilha no Lote
            match_upload = re.match(r"^/api/v1/admission-batches/([^/]+)/upload$", path)
            if match_upload:
                batch_id = match_upload.group(1)
                filename = body.get("filename", "admissoes.xlsx")
                file_b64 = body.get("file_base64", "")
                raw_text = body.get("csv_text", "")
                
                if file_b64:
                    content_bytes = base64.b64decode(file_b64)
                elif raw_text:
                    content_bytes = raw_text.encode("utf-8")
                else:
                    self.send_error_json("Arquivo não enviado (file_base64 ou csv_text obrigatório).", 400)
                    return

                res = AdmissionService.upload_spreadsheet(
                    db=db,
                    batch_id=batch_id,
                    filename=filename,
                    content_bytes=content_bytes,
                    uploaded_by_user_id=user["id"]
                )
                self.send_json(res)
                return

            # Salvar Mapeamento de Colunas
            match_map = re.match(r"^/api/v1/admission-batches/([^/]+)/map-columns$", path)
            if match_map:
                batch_id = match_map.group(1)
                mapping = body.get("mapping", {})
                defaults = body.get("defaults", {})
                AdmissionService.update_column_mapping(db, batch_id, mapping, defaults)
                self.send_json({"success": True, "message": "Mapeamento atualizado com sucesso."})
                return

            # Aplicar Template ao Lote
            match_tmpl = re.match(r"^/api/v1/admission-batches/([^/]+)/apply-template$", path)
            if match_tmpl:
                batch_id = match_tmpl.group(1)
                AdmissionService.apply_batch_template(db, batch_id, body.get("template_values", {}))
                self.send_json({"success": True, "message": "Template aplicado com sucesso ao lote."})
                return

            # Validar Lote de Admissao
            match_val = re.match(r"^/api/v1/admission-batches/([^/]+)/validate$", path)
            if match_val:
                batch_id = match_val.group(1)
                res = AdmissionService.validate_batch(db, batch_id)
                self.send_json(res)
                return

            # Commit de Linhas Validas para Admissoes
            match_commit = re.match(r"^/api/v1/admission-batches/([^/]+)/commit$", path)
            if match_commit:
                batch_id = match_commit.group(1)
                created = AdmissionService.commit_batch_to_admissions(db, batch_id, actor_user_id=user["id"])
                self.send_json({"committed_count": len(created), "admissions": created})
                return

            # Gerar Convite de Pre-Admissao
            match_invite = re.match(r"^/api/v1/admissions/([^/]+)/invite$", path)
            if match_invite:
                adm_id = match_invite.group(1)
                invite = AdmissionService.generate_pre_admission_invite(db, adm_id, actor_user_id=user["id"])
                self.send_json(invite)
                return

            # eSocial S-2190 Preliminar
            match_s2190 = re.match(r"^/api/v1/admissions/([^/]+)/submit-s2190$", path)
            if match_s2190:
                adm_id = match_s2190.group(1)
                res = ESocialAdmissionClient.submit_s2190(db, adm_id, actor_user_id=user["id"])
                self.send_json(res)
                return

            # eSocial S-2200 Admissao Completa
            match_s2200 = re.match(r"^/api/v1/admissions/([^/]+)/submit-s2200$", path)
            if match_s2200:
                adm_id = match_s2200.group(1)
                res = ESocialAdmissionClient.submit_s2200(db, adm_id, actor_user_id=user["id"])
                self.send_json(res)
                return

            # Ativacao e Efetivacao da Admissao
            match_activate = re.match(r"^/api/v1/admissions/([^/]+)/activate$", path)
            if match_activate:
                adm_id = match_activate.group(1)
                res = AdmissionService.activate_admission(db, adm_id, actor_user_id=user["id"])
                self.send_json(res)
                return

            # Execucao do Calculo de Folha Mensal
            if path == "/api/v1/payroll/calculate":
                if not RBACManager.has_permission(user, "payroll.calculate"):
                    self.send_error_json("Acesso não autorizado ao cálculo de folha.", 403)
                    return
                competence = body.get("competence", datetime.now(timezone.utc).strftime("%Y-%m"))
                
                # Buscar todos os contratos ativos da empresa
                contracts_rows = db.fetchall("""
                    SELECT id, employee_id FROM employment_contracts
                    WHERE company_id = ? AND is_active = 1;
                """, (user["company_id"],))
                
                if not contracts_rows:
                    self.send_error_json("Nenhum contrato ativo encontrado para esta empresa.", 400)
                    return

                payroll_run_id = f"run-{uuid.uuid4()}"
                db.execute("""
                    INSERT OR REPLACE INTO payroll_runs (id, company_id, competence, status)
                    VALUES (?, ?, ?, 'CALCULATING');
                """, (payroll_run_id, user["company_id"], competence))

                calculated_payslips = []
                total_gross = Decimal("0.00")
                total_net = Decimal("0.00")
                total_fgts = Decimal("0.00")

                ctx = CalculationContext(competence=competence)

                for crow in contracts_rows:
                    engine_contract = EmployeeRepository.to_engine_contract(db, crow["id"])
                    if not engine_contract:
                        continue
                    payslip = process_monthly_payroll(engine_contract, ctx)
                    total_gross += payslip.gross_total
                    total_net += payslip.net_total
                    total_fgts += payslip.fgts_amount

                    items_list = [
                        {
                            "code": it.rubric_code,
                            "name": it.rubric_name,
                            "type": it.rubric_type.value,
                            "amount": float(it.amount),
                            "reference": float(it.reference) if it.reference else None
                        }
                        for it in payslip.items
                    ]

                    # Gravar holerite no banco
                    payslip_id = f"ps-{uuid.uuid4()}"
                    db.execute("""
                        INSERT OR REPLACE INTO payslips (
                            id, payroll_run_id, contract_id, employee_id, competence,
                            gross_total, discounts_total, net_total, inss_base, irrf_base,
                            fgts_base, fgts_amount, hash_lock, items_json
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """, (
                        payslip_id, payroll_run_id, crow["id"], crow["employee_id"],
                        competence, float(payslip.gross_total), float(payslip.discounts_total),
                        float(payslip.net_total), float(payslip.inss_base), float(payslip.irrf_base),
                        float(payslip.fgts_base), float(payslip.fgts_amount), payslip.hash_lock,
                        json.dumps(items_list, ensure_ascii=False)
                    ))

                    calculated_payslips.append({
                        "contract_id": crow["id"],
                        "employee_name": engine_contract.employee.full_name,
                        "gross": float(payslip.gross_total),
                        "net": float(payslip.net_total),
                        "hash": payslip.hash_lock
                    })

                db.execute("""
                    UPDATE payroll_runs
                    SET status = 'CALCULATED', total_gross = ?, total_net = ?, total_fgts = ?, calculated_at = CURRENT_TIMESTAMP
                    WHERE id = ?;
                """, (float(total_gross), float(total_net), float(total_fgts), payroll_run_id))

                AuditLogger.record(
                    db=db,
                    actor_user_id=user["id"],
                    actor_email=user["email"],
                    actor_role=user["role"],
                    company_id=user["company_id"],
                    action="payroll.calculate",
                    entity_type="payroll_run",
                    entity_id=payroll_run_id,
                    after={"competence": competence, "contracts_count": len(calculated_payslips)},
                    reason="Cálculo integral da folha mensal via motor de cálculo DAG Python"
                )

                self.send_json({
                    "payroll_run_id": payroll_run_id,
                    "competence": competence,
                    "status": "CALCULATED",
                    "total_contracts": len(calculated_payslips),
                    "total_gross": float(total_gross),
                    "total_net": float(total_net),
                    "total_fgts": float(total_fgts),
                    "payslips": calculated_payslips
                })
                return

            self.send_error_json("Rota não encontrada.", 404)

    def do_PATCH(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self.read_json_body()

        with get_db() as db:
            user = self.get_auth_user(db)
            if not user:
                self.send_error_json("Não autenticado.", 401)
                return

            # Correcao em tempo real de celulas na linha de admissao
            match_row = re.match(r"^/api/v1/admission-batches/([^/]+)/rows/([^/]+)$", path)
            if match_row:
                batch_id = match_row.group(1)
                row_id = match_row.group(2)
                try:
                    res = AdmissionService.update_row_data(db, batch_id, row_id, body.get("fields", {}))
                    self.send_json(res)
                except Exception as e:
                    self.send_error_json(str(e), 400)
                return

            self.send_error_json("Rota não encontrada.", 404)

def run_server(port: int = 8000):
    run_migrations()
    server_address = ("", port)
    httpd = ThreadedHTTPServer(server_address, ThPayRequestHandler)
    print(f"ThPay Core API Server running on port {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()

if __name__ == "__main__":
    run_server()
