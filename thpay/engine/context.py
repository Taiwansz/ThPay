from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

@dataclass
class CalculationContext:
    competence: str              # Formato YYYY-MM
    worked_days: int = 30        # Padrao comercial CLT
    calendar_days: int = 30      # Dias do mes civil
    business_days: int = 25      # Dias uteis no mes (segunda a sabado para DSR)
    rest_and_holidays: int = 5   # Domingos e feriados legais no mes

    # Variaveis apuradas de ponto
    overtime_50_hours: Decimal = Decimal("0.00")
    overtime_100_hours: Decimal = Decimal("0.00")
    night_hours: Decimal = Decimal("0.00")
    absence_days: int = 0
    absence_hours: Decimal = Decimal("0.00")

    # Adicionais contratuais
    insalubrity_rate: Optional[Decimal] = None # 0.10, 0.20, 0.40 s/ Salario Minimo
    has_periculosity: bool = False             # 30% s/ Salario Base
    minimum_wage: Decimal = Decimal("1412.00")

    # Beneficios e descontos complementares
    transport_ticket_real_cost: Decimal = Decimal("0.00")
    meal_ticket_deduction_amount: Decimal = Decimal("0.00")
    health_insurance_deduction: Decimal = Decimal("0.00")
    advance_already_paid: Decimal = Decimal("0.00")
    consigned_loan_deduction: Decimal = Decimal("0.00")
