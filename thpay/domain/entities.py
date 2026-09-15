from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import List, Optional

class TaxRegime(str, Enum):
    SIMPLES_NACIONAL_ANEXO_I_II_III_V = "SIMPLES_NACIONAL_ANEXO_I_II_III_V"
    SIMPLES_NACIONAL_ANEXO_IV = "SIMPLES_NACIONAL_ANEXO_IV"
    LUCRO_PRESUMIDO = "LUCRO_PRESUMIDO"
    LUCRO_REAL = "LUCRO_REAL"
    DESONERACAO_CPRB = "DESONERACAO_CPRB"
    ENTIDADE_BENEFICENTE = "ENTIDADE_BENEFICENTE"

class WorkerCategory(str, Enum):
    CLT_GERAL = "101"
    APRENDIZ = "103"
    DOMESTICO = "104"
    INTERMITENTE = "105"
    TEMPORARIO = "106"
    EXPERIENCIA = "111"
    PRO_LABORE_COM_FGTS = "721"
    PRO_LABORE_SEM_FGTS = "722"
    AUTONOMO = "731"
    ESTAGIARIO = "901"

class RubricType(str, Enum):
    PROVENTO = "1"
    DESCONTO = "2"
    INFORMATIVA = "3"
    INFORMATIVA_DEDUTORA = "4"

@dataclass
class Dependent:
    name: str
    relationship: str
    is_irrf_dependent: bool = True
    is_family_salary_dependent: bool = False
    birth_date: Optional[str] = None

@dataclass
class AlimonyOrder:
    beneficiary_name: str
    percentage_net: Optional[Decimal] = None
    percentage_gross: Optional[Decimal] = None
    fixed_amount: Optional[Decimal] = None
    applies_to_13th: bool = True
    applies_to_vacation: bool = True

@dataclass
class Company:
    cnpj: str
    corporate_name: str
    tax_regime: TaxRegime
    cnae: str
    fpas: str
    other_entities_code: str
    rat_basic: Decimal
    fap: Decimal

    @property
    def rat_adjusted(self) -> Decimal:
        return (self.rat_basic * self.fap).quantize(Decimal("0.0001"))

@dataclass
class Employee:
    cpf: str
    full_name: str
    category: WorkerCategory
    dependents: List[Dependent] = field(default_factory=list)
    alimony_orders: List[AlimonyOrder] = field(default_factory=list)

    @property
    def irrf_dependents_count(self) -> int:
        return sum(1 for d in self.dependents if d.is_irrf_dependent)

    @property
    def family_salary_dependents_count(self) -> int:
        return sum(1 for d in self.dependents if d.is_family_salary_dependent)

@dataclass
class Contract:
    contract_id: str
    employee: Employee
    company: Company
    base_salary: Decimal
    workload_monthly_hours: int = 220
    is_active: bool = True

    @property
    def hourly_rate(self) -> Decimal:
        return (self.base_salary / Decimal(self.workload_monthly_hours)).quantize(Decimal("0.0001"))

@dataclass
class PayslipItem:
    rubric_code: str
    rubric_name: str
    rubric_type: RubricType
    reference: Optional[Decimal]
    amount: Decimal

@dataclass
class Payslip:
    contract_id: str
    competence: str
    items: List[PayslipItem] = field(default_factory=list)
    gross_total: Decimal = Decimal("0.00")
    discounts_total: Decimal = Decimal("0.00")
    net_total: Decimal = Decimal("0.00")
    inss_base: Decimal = Decimal("0.00")
    irrf_base: Decimal = Decimal("0.00")
    fgts_base: Decimal = Decimal("0.00")
    fgts_amount: Decimal = Decimal("0.00")
    hash_lock: Optional[str] = None
