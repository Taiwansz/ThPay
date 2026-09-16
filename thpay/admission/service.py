import json
import uuid
import secrets
import hashlib
from datetime import datetime, timedelta, date, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set, Tuple

from thpay.admission.models import AdmissionRowStatus, BatchStatus, IssueSeverity, ValidationIssue
from thpay.admission.parser import SpreadsheetParser
from thpay.admission.mapper import ColumnMapper, normalize_text
from thpay.admission.validator import AdmissionValidator, clean_digits, format_cpf
from thpay.audit.logger import AuditLogger
from thpay.storage.manager import StorageManager

def compute_row_fingerprint(tenant_id: str, cpf: str, hire_date: str, company_id: str) -> str:
    raw = f"{tenant_id}:{company_id}:{clean_digits(cpf)}:{hire_date}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

class AdmissionService:
    @staticmethod
    def create_batch(
        db,
        company_id: str,
        name: str,
        target_start_date: str,
        branch_id: Optional[str] = None,
        expected_count: int = 1,
        responsible_user_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        batch_id = f"batch-{uuid.uuid4()}"
        code_suffix = secrets.token_hex(3).upper()
        batch_code = f"ADM-{datetime.strptime(target_start_date, '%Y-%m-%d').strftime('%Y%m%d')}-{code_suffix}"
        
        db.execute("""
            INSERT INTO admission_batches (
                id, company_id, batch_code, name, target_start_date,
                branch_id, expected_count, responsible_user_id, status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'DRAFT', ?);
        """, (
            batch_id, company_id, batch_code, name, target_start_date,
            branch_id, expected_count, responsible_user_id, notes
        ))
        
        return db.fetchone("SELECT * FROM admission_batches WHERE id = ?;", (batch_id,))

    @staticmethod
    def get_batch(db, batch_id: str) -> Optional[Dict[str, Any]]:
        batch = db.fetchone("SELECT * FROM admission_batches WHERE id = ?;", (batch_id,))
        if not batch:
            return None
            
        summary = dict(batch)
        # Estatisticas agregadas de linhas
        rows_stats = db.fetchall("""
            SELECT status, count(*) as cnt
            FROM admission_rows
            WHERE batch_id = ?
            GROUP BY status;
        """, (batch_id,))
        
        stats_dict = {s["status"]: s["cnt"] for s in rows_stats}
        summary["total_rows"] = sum(stats_dict.values())
        summary["counts"] = stats_dict
        summary["valid_count"] = stats_dict.get(AdmissionRowStatus.READY_ESOCIAL.value, 0)
        summary["blocked_count"] = stats_dict.get(AdmissionRowStatus.BLOCKED.value, 0)
        summary["warning_count"] = stats_dict.get(AdmissionRowStatus.HAS_WARNING.value, 0)
        summary["pre_admission_count"] = stats_dict.get(AdmissionRowStatus.READY_PRE_ADMISSION.value, 0) + stats_dict.get(AdmissionRowStatus.AWAITING_DOCUMENTS.value, 0)
        summary["admitted_count"] = stats_dict.get(AdmissionRowStatus.ADMITTED.value, 0)
        
        return summary

    @staticmethod
    def list_batches(db, company_id: str) -> List[Dict[str, Any]]:
        batches = db.fetchall(
            "SELECT * FROM admission_batches WHERE company_id = ? ORDER BY created_at DESC;",
            (company_id,)
        )
        result = []
        for b in batches:
            result.append(AdmissionService.get_batch(db, b["id"]))
        return result

    @staticmethod
    def upload_spreadsheet(
        db,
        batch_id: str,
        filename: str,
        content_bytes: bytes,
        uploaded_by_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        batch = db.fetchone("SELECT * FROM admission_batches WHERE id = ?;", (batch_id,))
        if not batch:
            raise ValueError("Lote de admissão inexistente.")

        storage = StorageManager()
        mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if filename.lower().endswith(".xlsx") else "text/csv"
        
        doc_record = storage.store_file(
            content_bytes=content_bytes,
            original_name=filename,
            company_id=batch["company_id"],
            entity_type="admission_batch",
            entity_id=batch_id,
            document_type="ADMISSION_SPREADSHEET",
            mime_type=mime_type,
            uploaded_by_user_id=uploaded_by_user_id,
            db_context=db
        )

        headers, raw_rows = SpreadsheetParser.parse(filename, content_bytes)
        
        # Salvar registro do arquivo
        file_id = f"imp-{uuid.uuid4()}"
        db.execute("""
            INSERT INTO admission_import_files (
                id, batch_id, file_name, file_size, mime_type,
                file_hash_sha256, storage_path, row_count, uploaded_by_user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            file_id, batch_id, filename, len(content_bytes),
            mime_type, doc_record["sha256_hash"], doc_record["storage_path"],
            len(raw_rows), uploaded_by_user_id
        ))

        # Sugerir mapeamento de colunas
        suggested_mapping = ColumnMapper.suggest_mapping(headers)
        
        # Salvar mapeamento sugerido no banco
        db.execute("DELETE FROM admission_column_mappings WHERE batch_id = ?;", (batch_id,))
        for col_name, target in suggested_mapping.items():
            db.execute("""
                INSERT INTO admission_column_mappings (id, batch_id, source_column, target_field)
                VALUES (?, ?, ?, ?);
            """, (f"map-{uuid.uuid4()}", batch_id, col_name, target or "IGNORE"))

        # Limpar linhas anteriores caso o lote esteja sendo reiniciado
        db.execute("DELETE FROM admission_rows WHERE batch_id = ?;", (batch_id,))

        # Inserir linhas cruas como IMPORTED
        for idx, row in enumerate(raw_rows, start=1):
            row_id = f"row-{uuid.uuid4()}"
            mapped = ColumnMapper.apply_mapping(row, suggested_mapping)
            raw_json = json.dumps(row, ensure_ascii=False)
            parsed_json = json.dumps(mapped, ensure_ascii=False)
            fingerprint = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()
            
            db.execute("""
                INSERT INTO admission_rows (
                    id, batch_id, row_number, raw_data_json,
                    parsed_data_json, status, fingerprint
                ) VALUES (?, ?, ?, ?, ?, 'importado', ?);
            """, (row_id, batch_id, idx, raw_json, parsed_json, fingerprint))

        db.execute("UPDATE admission_batches SET status = 'IMPORTING' WHERE id = ?;", (batch_id,))
        
        return {
            "file_id": file_id,
            "filename": filename,
            "row_count": len(raw_rows),
            "headers": headers,
            "suggested_mapping": suggested_mapping,
            "sha256": doc_record["sha256_hash"]
        }

    @staticmethod
    def update_column_mapping(
        db,
        batch_id: str,
        mapping: Dict[str, str],
        default_values: Optional[Dict[str, Any]] = None
    ):
        db.execute("DELETE FROM admission_column_mappings WHERE batch_id = ?;", (batch_id,))
        for src, target in mapping.items():
            db.execute("""
                INSERT INTO admission_column_mappings (id, batch_id, source_column, target_field)
                VALUES (?, ?, ?, ?);
            """, (f"map-{uuid.uuid4()}", batch_id, src, target or "IGNORE"))

        # Reaplicar mapeamento a todas as linhas cruas
        rows = db.fetchall("SELECT id, raw_data_json FROM admission_rows WHERE batch_id = ?;", (batch_id,))
        for r in rows:
            raw = json.loads(r["raw_data_json"])
            mapped = ColumnMapper.apply_mapping(raw, mapping, default_values)
            db.execute(
                "UPDATE admission_rows SET parsed_data_json = ? WHERE id = ?;",
                (json.dumps(mapped, ensure_ascii=False), r["id"])
            )

    @staticmethod
    def apply_batch_template(
        db,
        batch_id: str,
        template_values: Dict[str, Any]
    ):
        """
        Aplica valores padrao do lote (empresa, filial, departamento, sindicato, beneficios)
        a todas as linhas sem sobrescrever campos explicitamente definidos na planilha.
        """
        rows = db.fetchall("SELECT id, parsed_data_json FROM admission_rows WHERE batch_id = ?;", (batch_id,))
        for r in rows:
            parsed = json.loads(r["parsed_data_json"])
            for k, v in template_values.items():
                if not parsed.get(k):
                    parsed[k] = v
            db.execute(
                "UPDATE admission_rows SET parsed_data_json = ? WHERE id = ?;",
                (json.dumps(parsed, ensure_ascii=False), r["id"])
            )

    @staticmethod
    def validate_batch(db, batch_id: str) -> Dict[str, Any]:
        batch = db.fetchone("SELECT * FROM admission_batches WHERE id = ?;", (batch_id,))
        if not batch:
            raise ValueError("Lote não encontrado.")

        # Buscar CPFs existentes no banco de dados para a empresa
        existing_cpfs_rows = db.fetchall("SELECT cpf FROM employees WHERE company_id = ?;", (batch["company_id"],))
        existing_cpfs = {clean_digits(r["cpf"]) for r in existing_cpfs_rows}
        seen_batch_cpfs: Set[str] = set()

        rows = db.fetchall(
            "SELECT id, row_number, parsed_data_json FROM admission_rows WHERE batch_id = ? ORDER BY row_number ASC;",
            (batch_id,)
        )

        db.execute("DELETE FROM admission_validation_issues WHERE batch_id = ?;", (batch_id,))
        
        total_errors = 0
        total_warnings = 0

        for r in rows:
            data = json.loads(r["parsed_data_json"])
            status, issues, normalized = AdmissionValidator.validate_row(
                row_data=data,
                row_number=r["row_number"],
                seen_cpfs_in_batch=seen_batch_cpfs,
                existing_cpfs_in_db=existing_cpfs
            )

            error_count = sum(1 for i in issues if i.severity == IssueSeverity.ERROR)
            warning_count = sum(1 for i in issues if i.severity == IssueSeverity.WARNING)
            total_errors += error_count
            total_warnings += warning_count

            # Gravar problemas de validacao
            for issue in issues:
                db.execute("""
                    INSERT INTO admission_validation_issues (
                        id, row_id, batch_id, severity, field_name,
                        error_code, message, suggested_action
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    f"iss-{uuid.uuid4()}", r["id"], batch_id,
                    issue.severity.value, issue.field_name,
                    issue.error_code, issue.message, issue.suggested_action
                ))

            # Atualizar linha
            db.execute("""
                UPDATE admission_rows
                SET parsed_data_json = ?, status = ?, error_count = ?, warning_count = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?;
            """, (json.dumps(normalized, ensure_ascii=False), status.value, error_count, warning_count, r["id"]))

        new_batch_status = BatchStatus.HAS_ERRORS.value if total_errors > 0 else BatchStatus.READY_FOR_REVIEW.value
        db.execute("UPDATE admission_batches SET status = ? WHERE id = ?;", (new_batch_status, batch_id))

        return {
            "batch_id": batch_id,
            "status": new_batch_status,
            "total_rows": len(rows),
            "total_errors": total_errors,
            "total_warnings": total_warnings
        }

    @staticmethod
    def get_batch_rows(
        db,
        batch_id: str,
        status_filter: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        conditions = ["batch_id = ?"]
        params = [batch_id]
        if status_filter:
            conditions.append("status = ?")
            params.append(status_filter)

        where_clause = " AND ".join(conditions)
        rows = db.fetchall(f"""
            SELECT id, batch_id, row_number, raw_data_json, parsed_data_json,
                   status, error_count, warning_count, fingerprint, created_at, updated_at
            FROM admission_rows
            WHERE {where_clause}
            ORDER BY row_number ASC
            LIMIT ? OFFSET ?;
        """, tuple(params + [limit, offset]))

        result = []
        for r in rows:
            row_dict = dict(r)
            row_dict["parsed"] = json.loads(r["parsed_data_json"])
            row_dict["issues"] = db.fetchall(
                "SELECT * FROM admission_validation_issues WHERE row_id = ? ORDER BY severity DESC, field_name;",
                (r["id"],)
            )
            result.append(row_dict)
        return result

    @staticmethod
    def update_row_data(
        db,
        batch_id: str,
        row_id: str,
        updated_fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        row = db.fetchone("SELECT * FROM admission_rows WHERE id = ? AND batch_id = ?;", (row_id, batch_id))
        if not row:
            raise ValueError("Linha não encontrada.")

        current = json.loads(row["parsed_data_json"])
        current.update(updated_fields)

        # Buscar CPFs existentes no banco (exceto o proprio se ja existia)
        batch = db.fetchone("SELECT * FROM admission_batches WHERE id = ?;", (batch_id,))
        existing_cpfs_rows = db.fetchall("SELECT cpf FROM employees WHERE company_id = ?;", (batch["company_id"],))
        existing_cpfs = {clean_digits(r["cpf"]) for r in existing_cpfs_rows}

        # Outros CPFs no lote
        other_rows = db.fetchall("SELECT parsed_data_json FROM admission_rows WHERE batch_id = ? AND id != ?;", (batch_id, row_id))
        seen_batch_cpfs = {clean_digits(json.loads(o["parsed_data_json"]).get("cpf", "")) for o in other_rows}

        status, issues, normalized = AdmissionValidator.validate_row(
            row_data=current,
            row_number=row["row_number"],
            seen_cpfs_in_batch=seen_batch_cpfs,
            existing_cpfs_in_db=existing_cpfs
        )

        db.execute("DELETE FROM admission_validation_issues WHERE row_id = ?;", (row_id,))
        for issue in issues:
            db.execute("""
                INSERT INTO admission_validation_issues (
                    id, row_id, batch_id, severity, field_name,
                    error_code, message, suggested_action
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                f"iss-{uuid.uuid4()}", row_id, batch_id,
                issue.severity.value, issue.field_name,
                issue.error_code, issue.message, issue.suggested_action
            ))

        error_count = sum(1 for i in issues if i.severity == IssueSeverity.ERROR)
        warning_count = sum(1 for i in issues if i.severity == IssueSeverity.WARNING)

        db.execute("""
            UPDATE admission_rows
            SET parsed_data_json = ?, status = ?, error_count = ?, warning_count = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?;
        """, (json.dumps(normalized, ensure_ascii=False), status.value, error_count, warning_count, row_id))

        return {
            "row_id": row_id,
            "status": status.value,
            "error_count": error_count,
            "warning_count": warning_count,
            "issues": [i.to_dict() for i in issues]
        }

    @staticmethod
    def commit_batch_to_admissions(db, batch_id: str, actor_user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Gera registros na entidade 'admissions' a partir das linhas validas do lote.
        Linhas bloqueadas com erro permanecem no lote para correcao.
        """
        rows = db.fetchall("""
            SELECT * FROM admission_rows
            WHERE batch_id = ? AND status != 'bloqueado';
        """, (batch_id,))

        created_admissions = []
        for r in rows:
            data = json.loads(r["parsed_data_json"])
            adm_id = f"adm-{uuid.uuid4()}"
            cpf = data.get("cpf", "")
            name = data.get("full_name", "")
            email = data.get("email", "")
            
            # Checar se ja existe admission para essa linha
            existing = db.fetchone("SELECT id FROM admissions WHERE row_id = ?;", (r["id"],))
            if existing:
                created_admissions.append(existing)
                continue

            db.execute("""
                INSERT INTO admissions (
                    id, batch_id, row_id, candidate_name, candidate_cpf,
                    candidate_email, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (adm_id, batch_id, r["id"], name, cpf, email, r["status"]))

            created_admissions.append({"id": adm_id, "name": name, "cpf": cpf})

        AuditLogger.record(
            db=db,
            actor_user_id=actor_user_id,
            actor_email=None,
            actor_role=None,
            action="admission_batch.commit",
            entity_type="admission_batch",
            entity_id=batch_id,
            after={"committed_count": len(created_admissions)},
            reason="Compromisso de linhas válidas do lote para admissões ativas"
        )

        return created_admissions

    @staticmethod
    def generate_pre_admission_invite(
        db,
        admission_id: str,
        actor_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        adm = db.fetchone("SELECT * FROM admissions WHERE id = ?;", (admission_id,))
        if not adm:
            raise ValueError("Admissão não encontrada.")

        token = secrets.token_urlsafe(32)
        expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

        db.execute("""
            UPDATE admissions
            SET pre_admission_token = ?, pre_admission_token_expires_at = ?, status = 'aguardando documentos'
            WHERE id = ?;
        """, (token, expires_at, admission_id))

        if adm.get("row_id"):
            db.execute(
                "UPDATE admission_rows SET status = 'aguardando documentos' WHERE id = ?;",
                (adm["row_id"],)
            )

        invite_link = f"/portal/pre-admissao?token={token}"
        
        AuditLogger.record(
            db=db,
            actor_user_id=actor_user_id,
            actor_email=None,
            actor_role=None,
            action="pre_admission.invite_generated",
            entity_type="admission",
            entity_id=admission_id,
            after={"token_expires_at": expires_at},
            reason="Geração de link seguro de autoatendimento para o pré-admitido"
        )

        return {
            "admission_id": admission_id,
            "token": token,
            "expires_at": expires_at,
            "invite_link": invite_link,
            "candidate_name": adm["candidate_name"],
            "candidate_email": adm["candidate_email"]
        }

    @staticmethod
    def submit_pre_admission_self_service(
        db,
        token: str,
        self_service_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        now_str = datetime.now(timezone.utc).isoformat()
        adm = db.fetchone(
            "SELECT * FROM admissions WHERE pre_admission_token = ? AND pre_admission_token_expires_at > ?;",
            (token, now_str)
        )
        if not adm:
            raise ValueError("Token de pré-admissão inválido ou expirado.")

        # Atualizar dados da linha correspondente
        if adm.get("row_id"):
            row = db.fetchone("SELECT parsed_data_json FROM admission_rows WHERE id = ?;", (adm["row_id"],))
            if row:
                current_data = json.loads(row["parsed_data_json"])
                current_data.update(self_service_data)
                db.execute("""
                    UPDATE admission_rows
                    SET parsed_data_json = ?, status = 'pronto para eSocial', updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?;
                """, (json.dumps(current_data, ensure_ascii=False), adm["row_id"]))

        db.execute("""
            UPDATE admissions
            SET status = 'pronto para eSocial', pre_admission_completed_at = CURRENT_TIMESTAMP
            WHERE id = ?;
        """, (adm["id"],))

        return {
            "admission_id": adm["id"],
            "status": "pronto para eSocial",
            "message": "Dados complementares e documentos enviados com sucesso."
        }

    @staticmethod
    def activate_admission(
        db,
        admission_id: str,
        actor_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Efetiva a admissao apos validacao e aceitacao do eSocial:
        1. Cria ou atualiza Employee
        2. Cria EmploymentContract
        3. Cria endereco e conta bancaria
        4. Cria beneficios associados
        5. Cria conta de User com role COLABORADOR_SELF_SERVICE
        6. Gera tarefas de onboarding
        7. Atualiza status para 'admitido'
        """
        adm = db.fetchone("SELECT * FROM admissions WHERE id = ?;", (admission_id,))
        if not adm:
            raise ValueError("Admissão não encontrada.")

        batch = db.fetchone("SELECT * FROM admission_batches WHERE id = ?;", (adm["batch_id"],))
        company_id = batch["company_id"]
        tenant_id = db.fetchone("SELECT tenant_id FROM companies WHERE id = ?;", (company_id,))["tenant_id"]

        row = db.fetchone("SELECT parsed_data_json FROM admission_rows WHERE id = ?;", (adm["row_id"],)) if adm.get("row_id") else None
        data = json.loads(row["parsed_data_json"]) if row else {}

        cpf = data.get("cpf", adm["candidate_cpf"])
        clean_cpf = clean_digits(cpf)
        full_name = data.get("full_name", adm["candidate_name"])
        email = data.get("email", adm["candidate_email"])
        birth_date = data.get("birth_date", "1995-01-01")
        hire_date = data.get("hire_date", batch["target_start_date"])
        salary = float(data.get("base_salary", 5000.00))
        position_title = data.get("position_title", "Colaborador")
        cbo = data.get("cbo", "2124-05")

        # 1. Encontrar ou criar cargo
        pos = db.fetchone("SELECT id FROM positions WHERE company_id = ? AND title = ?;", (company_id, position_title))
        if not pos:
            pos_id = f"pos-{uuid.uuid4()}"
            db.execute("""
                INSERT INTO positions (id, company_id, code, title, cbo, standard_salary)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (pos_id, company_id, f"CARGO-{secrets.token_hex(2).upper()}", position_title, cbo, salary))
        else:
            pos_id = pos["id"]

        # 2. Encontrar filial padrao da empresa
        branch = db.fetchone("SELECT id FROM branches WHERE company_id = ? LIMIT 1;", (company_id,))
        branch_id = branch["id"] if branch else None

        # 3. Encontrar departamento
        dept_name = data.get("department_name", "Engenharia de Software")
        dept = db.fetchone("SELECT id FROM departments WHERE company_id = ? AND name = ?;", (company_id, dept_name))
        dept_id = dept["id"] if dept else db.fetchone("SELECT id FROM departments WHERE company_id = ? LIMIT 1;", (company_id,))["id"]

        # 4. Encontrar centro de custo
        cc = db.fetchone("SELECT id FROM cost_centers WHERE company_id = ? LIMIT 1;", (company_id,))
        cc_id = cc["id"] if cc else None

        # 5. Criar registro de Employee
        emp_id = f"emp-{uuid.uuid4()}"
        db.execute("""
            INSERT INTO employees (
                id, company_id, cpf, full_name, birth_date,
                personal_email, corporate_email, phone_mobile, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE');
        """, (
            emp_id, company_id, format_cpf(clean_cpf), full_name, birth_date,
            email, email, data.get("phone", "")
        ))

        # 6. Criar Endereco
        db.execute("""
            INSERT INTO employee_addresses (
                id, employee_id, zip_code, street, number, complement,
                neighborhood, city, state, is_primary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1);
        """, (
            f"addr-{uuid.uuid4()}", emp_id, data.get("zip_code", "01310-100"),
            data.get("street", "Avenida Paulista"), data.get("number", "1000"),
            data.get("complement", ""), data.get("neighborhood", "Bela Vista"),
            data.get("city", "São Paulo"), data.get("state", "SP")
        ))

        # 7. Criar Dados Bancarios
        db.execute("""
            INSERT INTO employee_bank_accounts (
                id, employee_id, bank_code, bank_name, agency, account_number, account_type, pix_key, is_primary
            ) VALUES (?, ?, ?, ?, ?, ?, 'CORRENTE', ?, 1);
        """, (
            f"bank-{uuid.uuid4()}", emp_id, "001", data.get("bank_name", "Banco do Brasil"),
            data.get("agency", "1234"), data.get("account_number", "56789-0"),
            data.get("pix_key", format_cpf(clean_cpf))
        ))

        # 8. Criar Contrato de Trabalho Ativo
        contract_id = f"cont-{uuid.uuid4()}"
        reg_number = f"MAT-{clean_cpf[-4:]}{secrets.token_hex(1).upper()}"
        db.execute("""
            INSERT INTO employment_contracts (
                id, employee_id, company_id, branch_id, department_id,
                cost_center_id, position_id, registration_number, hire_date,
                category, contract_type, base_salary, monthly_hours, is_active, valid_from
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '101', 'INDETERMINATE', ?, 220, 1, ?);
        """, (
            contract_id, emp_id, company_id, branch_id, dept_id,
            cc_id, pos_id, reg_number, hire_date, salary, hire_date
        ))

        # 9. Associar Beneficios
        va_split = int(data.get("va_split", 50))
        vr_split = 100 - va_split
        db.execute("""
            INSERT INTO employee_benefits (
                id, employee_id, benefit_type, va_percentage, vr_percentage, total_amount, effective_date
            ) VALUES (?, ?, 'VA_VR', ?, ?, 1400.00, ?);
        """, (f"ben-{uuid.uuid4()}", emp_id, va_split, vr_split, hire_date))

        # 10. Provisionar Usuario no Portal do Colaborador
        user_id = f"usr-{uuid.uuid4()}"
        from thpay.db.migrations import hash_password
        default_pwd = hash_password("ThPay@2026")
        db.execute("""
            INSERT INTO users (
                id, tenant_id, company_id, employee_id, email, password_hash, full_name, role
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'COLABORADOR_SELF_SERVICE');
        """, (user_id, tenant_id, company_id, emp_id, email, default_pwd, full_name))

        # 11. Gerar Tarefas de Onboarding
        onboarding_tasks = [
            ("Assinatura do Contrato de Trabalho", "Realizar o aceite formal dos termos admissionais no portal", "COMPLIANCE"),
            ("Apresentação e Boas-Vindas da Equipe", "Alinhamento inicial com gestor e entrega do playbook", "CULTURA"),
            ("Retirada e Configuração de Equipamentos", "Retirada de notebook, crachá e credenciais corporativas", "TI_OPERACAO"),
            ("Validação de Dependentes e Benefícios", "Conferência final da divisão VA/VR e plano odontológico", "BENEFICIOS")
        ]
        for task_title, task_desc, cat in onboarding_tasks:
            db.execute("""
                INSERT INTO admission_tasks (
                    id, admission_id, employee_id, title, description, category, status
                ) VALUES (?, ?, ?, ?, ?, ?, 'PENDING');
            """, (f"task-{uuid.uuid4()}", admission_id, emp_id, task_title, task_desc, cat))

        # 12. Atualizar status para admitido
        db.execute("UPDATE admissions SET status = 'admitido', employee_id = ? WHERE id = ?;", (emp_id, admission_id))
        if adm.get("row_id"):
            db.execute("UPDATE admission_rows SET status = 'admitido' WHERE id = ?;", (adm["row_id"],))

        AuditLogger.record(
            db=db,
            actor_user_id=actor_user_id,
            actor_email=None,
            actor_role=None,
            action="admission.activate",
            entity_type="employee",
            entity_id=emp_id,
            after={
                "admission_id": admission_id,
                "contract_id": contract_id,
                "registration_number": reg_number,
                "user_id": user_id
            },
            reason="Admissão homologada: vínculo ativo criado, usuário provisionado e onboarding disparado."
        )

        return {
            "admission_id": admission_id,
            "employee_id": emp_id,
            "contract_id": contract_id,
            "registration_number": reg_number,
            "user_id": user_id,
            "status": "admitido"
        }
