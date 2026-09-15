from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple

# Faixas vigentes RGPS (Progressivas por fatias marginais)
DEFAULT_INSS_BRACKETS: List[Tuple[Decimal, Decimal]] = [
    (Decimal("1412.00"), Decimal("0.075")),
    (Decimal("2666.68"), Decimal("0.090")),
    (Decimal("4000.03"), Decimal("0.120")),
    (Decimal("7786.02"), Decimal("0.140")),
]

def calculate_inss_employee(
    base_amount: Decimal,
    brackets: List[Tuple[Decimal, Decimal]] = DEFAULT_INSS_BRACKETS,
    already_contributed_other_source: Decimal = Decimal("0.00")
) -> Decimal:
    """
    Calcula a contribuicao previdenciaria do empregado conforme a EC 103/2019
    atraves de fatiamento por faixas marginais progressivas.
    Suporta deducao de recolhimento previo em multiplos vinculos.
    """
    if base_amount <= Decimal("0.00"):
        return Decimal("0.00")

    ceiling = brackets[-1][0]
    taxable_base = min(base_amount, ceiling)

    total_inss = Decimal("0.00")
    prev_limit = Decimal("0.00")

    for limit, rate in brackets:
        if taxable_base > prev_limit:
            slice_amount = min(taxable_base, limit) - prev_limit
            total_inss += slice_amount * rate
            prev_limit = limit
        else:
            break

    # Arredondamento centavo a centavo conforme RFB
    calculated = total_inss.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Deduz recolhimento de outro vinculo, se houver
    if already_contributed_other_source > Decimal("0.00"):
        payable = max(Decimal("0.00"), calculated - already_contributed_other_source)
        return payable.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return calculated
