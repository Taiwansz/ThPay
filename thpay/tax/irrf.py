from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple

# Deducao mensal legal por dependente
DEPENDENT_DEDUCTION_AMOUNT = Decimal("189.59")

# Desconto simplificado mensal padrao (conforme Lei 14.663/2023 e vigentes)
DEFAULT_SIMPLIFIED_DISCOUNT = Decimal("564.80")

# Tabela progressiva mensal de IRRF: (limite_superior, aliquota, parcela_deduzir)
DEFAULT_IRRF_TABLE: List[Tuple[Decimal, Decimal, Decimal]] = [
    (Decimal("2259.20"), Decimal("0.000"), Decimal("0.00")),
    (Decimal("2826.65"), Decimal("0.075"), Decimal("169.44")),
    (Decimal("3751.05"), Decimal("0.150"), Decimal("381.44")),
    (Decimal("4664.68"), Decimal("0.225"), Decimal("662.77")),
    (Decimal("999999999.99"), Decimal("0.275"), Decimal("896.00")),
]

def calculate_irrf_employee(
    gross_taxable_amount: Decimal,
    inss_deduction: Decimal,
    dependents_count: int,
    alimony_deduction: Decimal = Decimal("0.00"),
    private_pension_deduction: Decimal = Decimal("0.00"),
    simplified_discount: Decimal = DEFAULT_SIMPLIFIED_DISCOUNT,
    table: List[Tuple[Decimal, Decimal, Decimal]] = DEFAULT_IRRF_TABLE
) -> Tuple[Decimal, Decimal, str]:
    """
    Calcula o IRRF mensal com comparativo automatico entre:
    1) Deducoes legais tradicionais (INSS, dependentes, pensao, previdencia)
    2) Desconto simplificado mensal parametrizado

    Aplica compulsoriamente a modalidade mais benefica (menor imposto).
    Retorna: (imposto_a_reter, base_de_calculo_utilizada, metodo_escolhido)
    """
    if gross_taxable_amount <= Decimal("0.00"):
        return Decimal("0.00"), Decimal("0.00"), "ISENTO"

    # 1. Total das deducoes legais tradicionais
    traditional_deductions = (
        inss_deduction +
        (Decimal(dependents_count) * DEPENDENT_DEDUCTION_AMOUNT) +
        alimony_deduction +
        private_pension_deduction
    )

    # 2. Escolha da deducao mais vantajosa (regra legal mais favoravel)
    if traditional_deductions >= simplified_discount:
        chosen_deduction = traditional_deductions
        method = "DEDUCOES_LEGAIS"
    else:
        chosen_deduction = simplified_discount
        method = "DESCONTO_SIMPLIFICADO"

    effective_base = max(Decimal("0.00"), gross_taxable_amount - chosen_deduction)

    # 3. Aplicacao da tabela progressiva sobre a base
    tax_calculated = Decimal("0.00")
    for limit, rate, deduction_parcel in table:
        if effective_base <= limit:
            tax_calculated = (effective_base * rate) - deduction_parcel
            break

    tax_calculated = max(Decimal("0.00"), tax_calculated).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # 4. Regra dos R$ 10,00 (Art. 724 RIR/2018 - dispensada a retencao inferior a dez reais)
    if tax_calculated < Decimal("10.00"):
        return Decimal("0.00"), effective_base, f"{method}_DISPENSADO_MENOR_10"

    return tax_calculated, effective_base, method
