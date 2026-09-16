from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

class BatchStatus(str, Enum):
    DRAFT = "DRAFT"
    IMPORTING = "IMPORTING"
    VALIDATING = "VALIDATING"
    HAS_ERRORS = "HAS_ERRORS"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    PRE_ADMISSION = "PRE_ADMISSION"
    READY_FOR_ESOCIAL = "READY_FOR_ESOCIAL"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class AdmissionRowStatus(str, Enum):
    IMPORTED = "importado"
    VALIDATING = "em validação"
    HAS_WARNING = "com alerta"
    BLOCKED = "bloqueado"
    AWAITING_DOCUMENTS = "aguardando documentos"
    AWAITING_EXAM = "aguardando exame"
    READY_PRE_ADMISSION = "pronto para pré-admissão"
    READY_ESOCIAL = "pronto para eSocial"
    SUBMITTED = "enviado"
    REJECTED = "rejeitado"
    ADMITTED = "admitido"
    CANCELLED = "cancelado"

class IssueSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"

@dataclass
class ValidationIssue:
    field_name: str
    error_code: str
    message: str
    suggested_action: Optional[str] = None
    severity: IssueSeverity = IssueSeverity.ERROR

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_name": self.field_name,
            "error_code": self.error_code,
            "message": self.message,
            "suggested_action": self.suggested_action,
            "severity": self.severity.value
        }
