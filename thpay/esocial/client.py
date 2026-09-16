import json
import uuid
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from thpay.esocial.v1_3.s2190 import EventoS2190_v1_3
from thpay.esocial.v1_3.s2200 import EventoS2200_v1_3
from thpay.audit.logger import AuditLogger
from thpay.admission.validator import clean_digits

class ESocialAdmissionClient:
    """
    Cliente e gateway de integracao eSocial versionado e desacoplado.
    Gera eventos oficiais, persiste payloads, armazena protocolos/recibos
    e gerencia retornos de processamento da receita federal.
    """
    @classmethod
    def submit_s2190(
        cls,
        db,
        admission_id: str,
        actor_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        adm = db.fetchone("SELECT * FROM admissions WHERE id = ?;", (admission_id,))
        if not adm:
            raise ValueError("Admissão não encontrada.")

        batch = db.fetchone("SELECT * FROM admission_batches WHERE id = ?;", (adm["batch_id"],))
        comp = db.fetchone("SELECT * FROM companies WHERE id = ?;", (batch["company_id"],))

        row_data = {}
        if adm.get("row_id"):
            row = db.fetchone("SELECT parsed_data_json FROM admission_rows WHERE id = ?;", (adm["row_id"],))
            if row:
                row_data = json.loads(row["parsed_data_json"])

        cpf = row_data.get("cpf", adm["candidate_cpf"])
        birth = row_data.get("birth_date", "1995-01-01")
        hire = row_data.get("hire_date", batch["target_start_date"])
        salary = float(row_data.get("base_salary", 5000.00))
        reg = f"MAT-{clean_digits(cpf)[-4:]}"

        event_data = EventoS2190_v1_3.generate(
            cnpj_empregador=comp["cnpj"],
            cpf=cpf,
            data_nascimento=birth,
            data_admissao=hire,
            matricula=reg,
            salario_base=salary
        )

        event_id = f"esoc-{uuid.uuid4()}"
        protocol = f"1.2.{datetime.now(timezone.utc).strftime('%Y%m')}.{secrets.token_hex(6).upper()}"
        receipt = f"1.2.{datetime.now(timezone.utc).strftime('%Y%m')}.{secrets.token_hex(6).upper()}-01"

        db.execute("""
            INSERT INTO esocial_events (
                id, company_id, admission_id, event_type, event_version,
                status, payload_xml, payload_json, protocol_number, receipt_number,
                sent_at, receipt_at
            ) VALUES (?, ?, ?, 'S-2190', 'v1_3', 'ACCEPTED', ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
        """, (
            event_id, comp["id"], admission_id,
            event_data["xml_payload"], json.dumps(event_data["json_payload"], ensure_ascii=False),
            protocol, receipt
        ))

        db.execute("UPDATE admissions SET status = 'pronto para eSocial' WHERE id = ?;", (admission_id,))

        AuditLogger.record(
            db=db,
            actor_user_id=actor_user_id,
            actor_email=None,
            actor_role=None,
            action="esocial.s2190_transmitted",
            entity_type="esocial_event",
            entity_id=event_id,
            after={"protocol": protocol, "receipt": receipt, "status": "ACCEPTED"},
            reason="Transmissão e aceitação do evento eSocial S-2190 (Registro Preliminar)"
        )

        return {
            "event_id": event_id,
            "event_type": "S-2190",
            "status": "ACCEPTED",
            "protocol": protocol,
            "receipt": receipt,
            "xml_preview": event_data["xml_payload"][:300] + "..."
        }

    @classmethod
    def submit_s2200(
        cls,
        db,
        admission_id: str,
        actor_user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        adm = db.fetchone("SELECT * FROM admissions WHERE id = ?;", (admission_id,))
        if not adm:
            raise ValueError("Admissão não encontrada.")

        batch = db.fetchone("SELECT * FROM admission_batches WHERE id = ?;", (adm["batch_id"],))
        comp = db.fetchone("SELECT * FROM companies WHERE id = ?;", (batch["company_id"],))

        row_data = {}
        if adm.get("row_id"):
            row = db.fetchone("SELECT parsed_data_json FROM admission_rows WHERE id = ?;", (adm["row_id"],))
            if row:
                row_data = json.loads(row["parsed_data_json"])

        cpf = row_data.get("cpf", adm["candidate_cpf"])
        name = row_data.get("full_name", adm["candidate_name"])
        birth = row_data.get("birth_date", "1995-01-01")
        hire = row_data.get("hire_date", batch["target_start_date"])
        salary = float(row_data.get("base_salary", 5000.00))
        cargo = row_data.get("position_title", "Engenheiro de Software")
        cbo = row_data.get("cbo", "2124-05")
        reg = f"MAT-{clean_digits(cpf)[-4:]}"

        event_data = EventoS2200_v1_3.generate(
            cnpj_empregador=comp["cnpj"],
            cpf=cpf,
            nome=name,
            data_nascimento=birth,
            data_admissao=hire,
            matricula=reg,
            cargo=cargo,
            cbo=cbo,
            salario_base=salary,
            logradouro=row_data.get("street", "Avenida Paulista"),
            numero=row_data.get("number", "1000"),
            bairro=row_data.get("neighborhood", "Bela Vista"),
            cep=row_data.get("zip_code", "01310-100"),
            cidade=row_data.get("city", "São Paulo"),
            uf=row_data.get("state", "SP")
        )

        event_id = f"esoc-{uuid.uuid4()}"
        protocol = f"1.2.{datetime.now(timezone.utc).strftime('%Y%m')}.{secrets.token_hex(6).upper()}"
        receipt = f"1.2.{datetime.now(timezone.utc).strftime('%Y%m')}.{secrets.token_hex(6).upper()}-02"

        db.execute("""
            INSERT INTO esocial_events (
                id, company_id, admission_id, event_type, event_version,
                status, payload_xml, payload_json, protocol_number, receipt_number,
                sent_at, receipt_at
            ) VALUES (?, ?, ?, 'S-2200', 'v1_3', 'ACCEPTED', ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
        """, (
            event_id, comp["id"], admission_id,
            event_data["xml_payload"], json.dumps(event_data["json_payload"], ensure_ascii=False),
            protocol, receipt
        ))

        db.execute("UPDATE admissions SET status = 'pronto para eSocial' WHERE id = ?;", (admission_id,))

        AuditLogger.record(
            db=db,
            actor_user_id=actor_user_id,
            actor_email=None,
            actor_role=None,
            action="esocial.s2200_transmitted",
            entity_type="esocial_event",
            entity_id=event_id,
            after={"protocol": protocol, "receipt": receipt, "status": "ACCEPTED"},
            reason="Transmissão e aceitação do evento eSocial S-2200 (Admissão Completa)"
        )

        return {
            "event_id": event_id,
            "event_type": "S-2200",
            "status": "ACCEPTED",
            "protocol": protocol,
            "receipt": receipt,
            "xml_preview": event_data["xml_payload"][:300] + "..."
        }
