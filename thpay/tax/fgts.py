from decimal import Decimal, ROUND_HALF_UP
from ..domain.entities import WorkerCategory

def calculate_fgts_monthly(base_amount: Decimal, category: WorkerCategory) -> Decimal:
    """
    Calcula o FGTS mensal devido pela empresa.
    - Menor Aprendiz (103): 2%
    - Demais categorias com vinculo FGTS: 8%
    """
    if base_amount <= Decimal("0.00"):
        return Decimal("0.00")

    if category == WorkerCategory.APRENDIZ:
        rate = Decimal("0.02")
    elif category in (
        WorkerCategory.CLT_GERAL,
        WorkerCategory.DOMESTICO,
        WorkerCategory.INTERMITENTE,
        WorkerCategory.TEMPORARIO,
        WorkerCategory.EXPERIENCIA,
        WorkerCategory.PRO_LABORE_COM_FGTS
    ):
        rate = Decimal("0.08")
    else:
        # Autonomos, estagiarios e diretores sem FGTS nao possuem encargo
        return Decimal("0.00")

    return (base_amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def calculate_fgts_fine(balance_amount: Decimal, is_mutual_agreement: bool = False) -> Decimal:
    """
    Calcula a multa rescisoria de FGTS.
    - Acordo Mutuo (Art. 484-A CLT): 20%
    - Demissao sem justa causa / Quebra de contrato pelo empregador: 40%
    """
    if balance_amount <= Decimal("0.00"):
        return Decimal("0.00")

    rate = Decimal("0.20") if is_mutual_agreement else Decimal("0.40")
    return (balance_amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
