import json
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime

class AuditLogger:
    """
    Trilha de auditoria append-only para conformidade, compliance e rastreabilidade total.
    Registra autor, acao, entidade, estados antes/depois, IP, horario UTC e justificativa.
    """
    @staticmethod
    def record(
        db,
        actor_user_id: Optional[str],
        actor_email: Optional[str],
        actor_role: Optional[str],
        action: str,
        entity_type: str,
        entity_id: str,
        before: Optional[Dict[str, Any]] = None,
        after: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        tenant_id: Optional[str] = None,
        company_id: Optional[str] = None,
        correlation_id: Optional[str] = None
    ) -> str:
        audit_id = f"aud-{uuid.uuid4()}"
        before_json = json.dumps(before, default=str, ensure_ascii=False) if before else None
        after_json = json.dumps(after, default=str, ensure_ascii=False) if after else None
        
        db.execute("""
            INSERT INTO audit_trail (
                id, actor_user_id, actor_email, actor_role, ip_address,
                tenant_id, company_id, action, entity_type, entity_id,
                before_json, after_json, reason, correlation_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            audit_id, actor_user_id, actor_email, actor_role, ip_address,
            tenant_id, company_id, action, entity_type, entity_id,
            before_json, after_json, reason, correlation_id
        ))
        
        return audit_id

    @staticmethod
    def query(
        db,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        action: Optional[str] = None,
        company_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        conditions = []
        params = []
        
        if entity_type:
            conditions.append("entity_type = ?")
            params.append(entity_type)
        if entity_id:
            conditions.append("entity_id = ?")
            params.append(entity_id)
        if action:
            conditions.append("action = ?")
            params.append(action)
        if company_id:
            conditions.append("company_id = ?")
            params.append(company_id)
            
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        sql = f"""
            SELECT id, occurred_at, actor_user_id, actor_email, actor_role,
                   ip_address, tenant_id, company_id, action, entity_type,
                   entity_id, before_json, after_json, reason, correlation_id
            FROM audit_trail
            {where_clause}
            ORDER BY occurred_at DESC
            LIMIT ? OFFSET ?;
        """
        params.extend([limit, offset])
        
        rows = db.fetchall(sql, tuple(params))
        for row in rows:
            if row["before_json"]:
                row["before"] = json.loads(row["before_json"])
            if row["after_json"]:
                row["after"] = json.loads(row["after_json"])
        return rows
