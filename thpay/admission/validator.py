import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Set, Tuple

from thpay.admission.models import AdmissionRowStatus, IssueSeverity, ValidationIssue

def clean_digits(val: Any) -> str:
    if val is None:
        return ""
    return re.sub(r"\D", "", str(val))

def validate_cpf(cpf_raw: str) -> bool:
    cpf = clean_digits(cpf_raw)
    if len(cpf) != 11:
        return False
    # CPFs com todos os digitos iguais sao invalidos
    if cpf == cpf[0] * 11:
        return False
        
    # Primeiro digito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = 11 - (soma % 11)
    d1 = 0 if d1 >= 10 else d1
    if int(cpf[9]) != d1:
        return False
        
    # Segundo digito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = 11 - (soma % 11)
    d2 = 0 if d2 >= 10 else d2
    return int(cpf[10]) == d2

def format_cpf(cpf_raw: str) -> str:
    digits = clean_digits(cpf_raw)
    if len(digits) == 11:
        return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
    return str(cpf_raw).strip()

def parse_brazilian_date(val: Any) -> Optional[str]:
    """
    Normaliza datas em formato ISO YYYY-MM-DD.
    Suporta YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY e inteiros seriais do Excel.
    """
    if val is None or str(val).strip() == "":
        return None
    val_str = str(val).strip()
    
    # Se for serial do Excel (ex. 34567)
    if val_str.isdigit() and int(val_str) > 10000:
        try:
            # Excel base: 1899-12-30
            dt = datetime.fromordinal(datetime(1899, 12, 30).toordinal() + int(val_str))
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

    formats = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%Y/%m/%d"]
    for fmt in formats:
        try:
            dt = datetime.strptime(val_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None

def parse_decimal_currency(val: Any) -> Optional[Decimal]:
    if val is None or str(val).strip() == "":
        return None
    s = str(val).strip()
    # Limpar R$, espacos, etc.
    s = re.sub(r"[R$\s]", "", s)
    
    # Se formato brasileiro 1.500,50
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    
    try:
        d = Decimal(s)
        return d.quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None

class AdmissionValidator:
    @staticmethod
    def validate_row(
        row_data: Dict[str, Any],
        row_number: int,
        seen_cpfs_in_batch: Set[str],
        existing_cpfs_in_db: Set[str]
    ) -> Tuple[AdmissionRowStatus, List[ValidationIssue], Dict[str, Any]]:
        issues: List[ValidationIssue] = []
        normalized: Dict[str, Any] = dict(row_data)

        # 1. Nome Completo
        full_name = str(row_data.get("full_name", "")).strip()
        if not full_name:
            issues.append(ValidationIssue(
                field_name="full_name",
                error_code="REQUIRED_FIELD_MISSING",
                message="Nome completo do colaborador é obrigatório.",
                suggested_action="Preencha o nome completo.",
                severity=IssueSeverity.ERROR
            ))
        elif len(full_name.split()) < 2:
            issues.append(ValidationIssue(
                field_name="full_name",
                error_code="INCOMPLETE_NAME",
                message="Informe pelo menos nome e sobrenome.",
                suggested_action="Inclua o sobrenome do colaborador.",
                severity=IssueSeverity.WARNING
            ))
        normalized["full_name"] = full_name

        # 2. CPF
        cpf_raw = str(row_data.get("cpf", "")).strip()
        cpf_clean = clean_digits(cpf_raw)
        if not cpf_raw:
            issues.append(ValidationIssue(
                field_name="cpf",
                error_code="REQUIRED_FIELD_MISSING",
                message="CPF do colaborador é obrigatório para admissão.",
                suggested_action="Informe o CPF válido.",
                severity=IssueSeverity.ERROR
            ))
        elif not validate_cpf(cpf_clean):
            issues.append(ValidationIssue(
                field_name="cpf",
                error_code="INVALID_CPF",
                message=f"CPF '{cpf_raw}' possui dígitos verificadores inválidos.",
                suggested_action="Corrija os dígitos do CPF.",
                severity=IssueSeverity.ERROR
            ))
        else:
            # Validar duplicidade no mesmo lote
            if cpf_clean in seen_cpfs_in_batch:
                issues.append(ValidationIssue(
                    field_name="cpf",
                    error_code="DUPLICATE_CPF_IN_BATCH",
                    message=f"CPF {format_cpf(cpf_clean)} duplicado na mesma planilha/lote.",
                    suggested_action="Remova ou corrija a linha duplicada.",
                    severity=IssueSeverity.ERROR
                ))
            seen_cpfs_in_batch.add(cpf_clean)

            # Validar duplicidade no banco de colaboradores existentes
            if cpf_clean in existing_cpfs_in_db:
                issues.append(ValidationIssue(
                    field_name="cpf",
                    error_code="CPF_ALREADY_EXISTS_IN_DB",
                    message=f"Colaborador com CPF {format_cpf(cpf_clean)} já possui contrato ativo no sistema.",
                    suggested_action="Verifique se trata-se de readmissão ou recontratação.",
                    severity=IssueSeverity.ERROR
                ))
        normalized["cpf"] = format_cpf(cpf_clean) if cpf_clean else ""

        # 3. Data de Nascimento
        birth_raw = row_data.get("birth_date")
        birth_iso = parse_brazilian_date(birth_raw)
        if not birth_iso:
            issues.append(ValidationIssue(
                field_name="birth_date",
                error_code="INVALID_DATE",
                message="Data de nascimento inválida ou ausente.",
                suggested_action="Informe no formato DD/MM/AAAA ou AAAA-MM-DD.",
                severity=IssueSeverity.ERROR
            ))
        else:
            # Checar idade mínima de trabalho
            birth_dt = datetime.strptime(birth_iso, "%Y-%m-%d").date()
            today = date.today()
            age = today.year - birth_dt.year - ((today.month, today.day) < (birth_dt.month, birth_dt.day))
            if age < 14:
                issues.append(ValidationIssue(
                    field_name="birth_date",
                    error_code="AGE_BELOW_LEGAL_MINIMUM",
                    message=f"Idade calculada ({age} anos) abaixo do mínimo legal de 14 anos.",
                    suggested_action="Verifique a data de nascimento.",
                    severity=IssueSeverity.ERROR
                ))
            elif age < 16:
                issues.append(ValidationIssue(
                    field_name="birth_date",
                    error_code="APPRENTICE_AGE",
                    message=f"Menor de 16 anos ({age} anos): somente permitida admissão na condição de Aprendiz.",
                    suggested_action="Confirme o enquadramento de Menor Aprendiz.",
                    severity=IssueSeverity.WARNING
                ))
        normalized["birth_date"] = birth_iso

        # 4. Salário Base
        salary_raw = row_data.get("base_salary")
        salary_dec = parse_decimal_currency(salary_raw)
        if salary_dec is None:
            issues.append(ValidationIssue(
                field_name="base_salary",
                error_code="REQUIRED_FIELD_MISSING",
                message="Salário base inválido ou não informado.",
                suggested_action="Informe um valor numérico positivo para o salário base.",
                severity=IssueSeverity.ERROR
            ))
        elif salary_dec <= Decimal("0.00"):
            issues.append(ValidationIssue(
                field_name="base_salary",
                error_code="INVALID_SALARY_AMOUNT",
                message="Salário base deve ser estritamente maior que zero.",
                suggested_action="Corrija o valor do salário.",
                severity=IssueSeverity.ERROR
            ))
        elif salary_dec < Decimal("1412.00"): # Salário mínimo legal 2024+
            issues.append(ValidationIssue(
                field_name="base_salary",
                error_code="SALARY_BELOW_MINIMUM_WAGE",
                message=f"Salário (R$ {salary_dec}) inferior ao salário mínimo nacional (R$ 1.412,00).",
                suggested_action="Verifique se a jornada é proporcional ou corrija o valor.",
                severity=IssueSeverity.WARNING
            ))
        normalized["base_salary"] = float(salary_dec) if salary_dec else 0.0

        # 5. Cargo / CBO
        position = str(row_data.get("position_title", "")).strip()
        if not position:
            issues.append(ValidationIssue(
                field_name="position_title",
                error_code="REQUIRED_FIELD_MISSING",
                message="Cargo contratual é obrigatório.",
                suggested_action="Informe o cargo a ser ocupado.",
                severity=IssueSeverity.ERROR
            ))
        normalized["position_title"] = position

        # 6. Data de Admissão
        hire_raw = row_data.get("hire_date")
        hire_iso = parse_brazilian_date(hire_raw)
        if not hire_iso:
            issues.append(ValidationIssue(
                field_name="hire_date",
                error_code="INVALID_DATE",
                message="Data de admissão inválida ou não informada.",
                suggested_action="Informe a data prevista de início das atividades.",
                severity=IssueSeverity.ERROR
            ))
        normalized["hire_date"] = hire_iso

        # 7. E-mail e Contato
        email = str(row_data.get("email", "")).strip()
        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            issues.append(ValidationIssue(
                field_name="email",
                error_code="INVALID_EMAIL",
                message=f"Endereço de e-mail '{email}' em formato incorreto.",
                suggested_action="Corrija o formato do e-mail.",
                severity=IssueSeverity.WARNING
            ))
        normalized["email"] = email

        # 8. Campos Condicionais / Dados Pendentes para Pré-Admissão
        has_address = bool(row_data.get("street") and row_data.get("zip_code") and row_data.get("city"))
        has_bank = bool(row_data.get("bank_name") and row_data.get("account_number") and row_data.get("agency"))
        
        # Determinar status da linha
        has_blocking_errors = any(i.severity == IssueSeverity.ERROR for i in issues)
        has_warnings = any(i.severity == IssueSeverity.WARNING for i in issues)

        if has_blocking_errors:
            status = AdmissionRowStatus.BLOCKED
        elif not has_address or not has_bank or not email:
            # Dados mínimos obrigatórios atendidos, mas faltam dados pessoais/bancários para admissão completa
            status = AdmissionRowStatus.READY_PRE_ADMISSION
        elif has_warnings:
            status = AdmissionRowStatus.HAS_WARNING
        else:
            status = AdmissionRowStatus.READY_ESOCIAL

        return status, issues, normalized
