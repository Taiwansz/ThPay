import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any

from ..domain.entities import Contract, Payslip, PayslipItem, RubricType, WorkerCategory
from ..domain.rubrics import CANONICAL_RUBRICS
from ..engine.context import CalculationContext
from ..engine.dag import PayrollDAG
from ..tax.inss import calculate_inss_employee
from ..tax.irrf import calculate_irrf_employee
from ..tax.fgts import calculate_fgts_monthly

def build_monthly_payroll_dag(contract: Contract, ctx: CalculationContext) -> PayrollDAG:
    dag = PayrollDAG()

    # 1. Provento: Salario Base Proporcional
    def eval_base_salary(state: Dict[str, Any]) -> Decimal:
        if ctx.worked_days == 30:
            return contract.base_salary
        daily_rate = (contract.base_salary / Decimal("30")).quantize(Decimal("0.0001"))
        return (daily_rate * Decimal(ctx.worked_days)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    dag.add_node("rubric_1000", eval_base_salary)

    # 2. Adicional de Insalubridade
    def eval_insalubrity(state: Dict[str, Any]) -> Decimal:
        if ctx.insalubrity_rate:
            return (ctx.minimum_wage * ctx.insalubrity_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return Decimal("0.00")
    dag.add_node("rubric_1040", eval_insalubrity)

    # 3. Adicional de Periculosidade
    def eval_periculosity(state: Dict[str, Any]) -> Decimal:
        if ctx.has_periculosity:
            return (contract.base_salary * Decimal("0.30")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return Decimal("0.00")
    dag.add_node("rubric_1050", eval_periculosity)

    # 4. Horas Extras 50%
    def eval_he_50(state: Dict[str, Any]) -> Decimal:
        if ctx.overtime_50_hours <= Decimal("0.00"):
            return Decimal("0.00")
        remuneracao_base = contract.base_salary + state["rubric_1040"] + state["rubric_1050"]
        base_hourly = remuneracao_base / Decimal(contract.workload_monthly_hours)
        he_rate = base_hourly * Decimal("1.50")
        return (he_rate * ctx.overtime_50_hours).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    dag.add_node("rubric_1010", eval_he_50, depends_on=["rubric_1040", "rubric_1050"])

    # 5. Horas Extras 100%
    def eval_he_100(state: Dict[str, Any]) -> Decimal:
        if ctx.overtime_100_hours <= Decimal("0.00"):
            return Decimal("0.00")
        remuneracao_base = contract.base_salary + state["rubric_1040"] + state["rubric_1050"]
        base_hourly = remuneracao_base / Decimal(contract.workload_monthly_hours)
        he_rate = base_hourly * Decimal("2.00")
        return (he_rate * ctx.overtime_100_hours).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    dag.add_node("rubric_1015", eval_he_100, depends_on=["rubric_1040", "rubric_1050"])

    # 6. DSR sobre Horas Extras
    def eval_dsr_he(state: Dict[str, Any]) -> Decimal:
        total_he = state["rubric_1010"] + state["rubric_1015"]
        if total_he <= Decimal("0.00") or ctx.business_days == 0:
            return Decimal("0.00")
        dsr = (total_he / Decimal(ctx.business_days)) * Decimal(ctx.rest_and_holidays)
        return dsr.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    dag.add_node("rubric_1020", eval_dsr_he, depends_on=["rubric_1010", "rubric_1015"])

    # 7. Adicional Noturno 20% com Reducao Ficta (8/7)
    def eval_night_additional(state: Dict[str, Any]) -> Decimal:
        if ctx.night_hours <= Decimal("0.00"):
            return Decimal("0.00")
        fictional_hours = ctx.night_hours * (Decimal("60.0") / Decimal("52.5"))
        hourly_rate = contract.hourly_rate
        return (fictional_hours * hourly_rate * Decimal("0.20")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    dag.add_node("rubric_1030", eval_night_additional)

    # 8. DSR sobre Adicional Noturno
    def eval_dsr_night(state: Dict[str, Any]) -> Decimal:
        val = state["rubric_1030"]
        if val <= Decimal("0.00") or ctx.business_days == 0:
            return Decimal("0.00")
        dsr = (val / Decimal(ctx.business_days)) * Decimal(ctx.rest_and_holidays)
        return dsr.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    dag.add_node("rubric_1035", eval_dsr_night, depends_on=["rubric_1030"])

    # 9. Desconto de Faltas Injustificadas
    def eval_absence_deduction(state: Dict[str, Any]) -> Decimal:
        if ctx.absence_days == 0 and ctx.absence_hours <= Decimal("0.00"):
            return Decimal("0.00")
        daily_rate = (contract.base_salary / Decimal("30")).quantize(Decimal("0.0001"))
        days_cost = daily_rate * Decimal(ctx.absence_days)
        hours_cost = contract.hourly_rate * ctx.absence_hours
        return (days_cost + hours_cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    dag.add_node("rubric_5020", eval_absence_deduction)

    # 10. Desconto DSR da semana por Faltas
    def eval_absence_dsr_deduction(state: Dict[str, Any]) -> Decimal:
        if ctx.absence_days > 0:
            weeks_with_absence = min(ctx.absence_days, ctx.rest_and_holidays)
            daily_rate = (contract.base_salary / Decimal("30")).quantize(Decimal("0.0001"))
            return (daily_rate * Decimal(weeks_with_absence)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return Decimal("0.00")
    dag.add_node("rubric_5025", eval_absence_dsr_deduction)

    # 11. Base INSS Mensal (Rubricas com codIncCP = 11)
    def eval_inss_base(state: Dict[str, Any]) -> Decimal:
        proventos_inss = (
            state["rubric_1000"] +
            state["rubric_1010"] +
            state["rubric_1015"] +
            state["rubric_1020"] +
            state["rubric_1030"] +
            state["rubric_1035"] +
            state["rubric_1040"] +
            state["rubric_1050"]
        )
        descontos_inss = state["rubric_5020"] + state["rubric_5025"]
        base = max(Decimal("0.00"), proventos_inss - descontos_inss)
        return base.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    dag.add_node(
        "rubric_9000",
        eval_inss_base,
        depends_on=[
            "rubric_1000", "rubric_1010", "rubric_1015", "rubric_1020",
            "rubric_1030", "rubric_1035", "rubric_1040", "rubric_1050",
            "rubric_5020", "rubric_5025"
        ]
    )

    # 12. Desconto INSS Empregado (Progressivo)
    def eval_inss_discount(state: Dict[str, Any]) -> Decimal:
        return calculate_inss_employee(state["rubric_9000"])
    dag.add_node("rubric_5000", eval_inss_discount, depends_on=["rubric_9000"])

    # 13. Base FGTS Mensal
    def eval_fgts_base(state: Dict[str, Any]) -> Decimal:
        return state["rubric_9000"]
    dag.add_node("rubric_9010", eval_fgts_base, depends_on=["rubric_9000"])

    # 14. FGTS Empresa Mensal
    def eval_fgts_amount(state: Dict[str, Any]) -> Decimal:
        return calculate_fgts_monthly(state["rubric_9010"], contract.employee.category)
    dag.add_node("rubric_9030", eval_fgts_amount, depends_on=["rubric_9010"])

    # 15. Pensao Alimenticia Judicial
    def eval_alimony(state: Dict[str, Any]) -> Decimal:
        total_alimony = Decimal("0.00")
        for order in contract.employee.alimony_orders:
            if order.fixed_amount:
                total_alimony += order.fixed_amount
            elif order.percentage_net:
                net_base = max(Decimal("0.00"), state["rubric_9000"] - state["rubric_5000"])
                total_alimony += (net_base * (order.percentage_net / Decimal("100.0")))
            elif order.percentage_gross:
                total_alimony += (state["rubric_9000"] * (order.percentage_gross / Decimal("100.0")))
        return total_alimony.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    dag.add_node("rubric_5070", eval_alimony, depends_on=["rubric_9000", "rubric_5000"])

    # 16. Calculo IRRF Empregado (com comparacao automatica do Desconto Simplificado)
    def eval_irrf(state: Dict[str, Any]) -> Decimal:
        gross_taxable = state["rubric_9000"]
        inss_retido = state["rubric_5000"]
        alimony = state["rubric_5070"]
        dependents = contract.employee.irrf_dependents_count

        tax, base_used, _ = calculate_irrf_employee(
            gross_taxable_amount=gross_taxable,
            inss_deduction=inss_retido,
            dependents_count=dependents,
            alimony_deduction=alimony
        )
        state["_irrf_base_used"] = base_used
        return tax
    dag.add_node("rubric_5010", eval_irrf, depends_on=["rubric_9000", "rubric_5000", "rubric_5070"])

    def eval_irrf_base_informative(state: Dict[str, Any]) -> Decimal:
        return state.get("_irrf_base_used", Decimal("0.00"))
    dag.add_node("rubric_9020", eval_irrf_base_informative, depends_on=["rubric_5010"])

    # 17. Desconto Vale-Transporte (Limite 6% sobre salario base ou custo real)
    def eval_vt_discount(state: Dict[str, Any]) -> Decimal:
        if ctx.transport_ticket_real_cost <= Decimal("0.00"):
            return Decimal("0.00")
        six_percent = (contract.base_salary * Decimal("0.06")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return min(six_percent, ctx.transport_ticket_real_cost)
    dag.add_node("rubric_5030", eval_vt_discount)

    # 18. Descontos Diversos (Refeicao, Saude, Adiantamento, Consignado)
    dag.add_node("rubric_5040", lambda s: ctx.meal_ticket_deduction_amount)
    dag.add_node("rubric_5050", lambda s: ctx.health_insurance_deduction)
    dag.add_node("rubric_5060", lambda s: ctx.advance_already_paid)
    dag.add_node("rubric_5080", lambda s: ctx.consigned_loan_deduction)

    return dag

def process_monthly_payroll(contract: Contract, ctx: CalculationContext) -> Payslip:
    """
    Executa a folha mensal completa via DAG, aplica a salvaguarda de saldo
    anti-negativo e gera o demonstrativo com assinatura SHA-256.
    """
    dag = build_monthly_payroll_dag(contract, ctx)
    results = dag.execute()

    items = []
    total_earnings = Decimal("0.00")
    total_deductions = Decimal("0.00")

    # Mapeia resultados para itens de holerite (somente Proventos e Descontos entram na lista de lancamentos)
    for rubric_code, definition in CANONICAL_RUBRICS.items():
        if definition.rubric_type not in (RubricType.PROVENTO, RubricType.DESCONTO):
            continue

        key = f"rubric_{rubric_code}"
        if key in results:
            val = results[key]
            if val > Decimal("0.00"):
                ref = None
                if rubric_code == "1000":
                    ref = Decimal(ctx.worked_days)
                elif rubric_code == "1010":
                    ref = ctx.overtime_50_hours
                elif rubric_code == "1015":
                    ref = ctx.overtime_100_hours
                elif rubric_code == "1030":
                    ref = ctx.night_hours
                elif rubric_code == "5020":
                    ref = Decimal(ctx.absence_days)

                item = PayslipItem(
                    rubric_code=rubric_code,
                    rubric_name=definition.name,
                    rubric_type=definition.rubric_type,
                    reference=ref,
                    amount=val
                )
                items.append(item)

                if definition.rubric_type == RubricType.PROVENTO:
                    total_earnings += val
                elif definition.rubric_type == RubricType.DESCONTO:
                    total_deductions += val

    # Regra de Protecao Anti-Liquido Negativo (Insuficiencia de Saldo)
    if total_deductions > total_earnings:
        insufficiency_amount = total_deductions - total_earnings
        item_compensatorio = PayslipItem(
            rubric_code="1099",
            rubric_name=CANONICAL_RUBRICS["1099"].name,
            rubric_type=RubricType.PROVENTO,
            reference=None,
            amount=insufficiency_amount
        )
        items.append(item_compensatorio)
        total_earnings += insufficiency_amount

    net_total = total_earnings - total_deductions

    payslip = Payslip(
        contract_id=contract.contract_id,
        competence=ctx.competence,
        items=items,
        gross_total=total_earnings,
        discounts_total=total_deductions,
        net_total=net_total,
        inss_base=results.get("rubric_9000", Decimal("0.00")),
        irrf_base=results.get("rubric_9020", Decimal("0.00")),
        fgts_base=results.get("rubric_9010", Decimal("0.00")),
        fgts_amount=results.get("rubric_9030", Decimal("0.00"))
    )

    # Geracao do Hash Criptografico SHA-256 de fechamento
    hash_payload = {
        "contract_id": payslip.contract_id,
        "competence": payslip.competence,
        "gross": str(payslip.gross_total),
        "discounts": str(payslip.discounts_total),
        "net": str(payslip.net_total),
        "inss_base": str(payslip.inss_base),
        "irrf_base": str(payslip.irrf_base),
        "fgts_base": str(payslip.fgts_base),
        "items": [
            {"code": it.rubric_code, "amount": str(it.amount), "type": it.rubric_type.value}
            for it in payslip.items
        ]
    }
    digest = hashlib.sha256(json.dumps(hash_payload, sort_keys=True).encode("utf-8")).hexdigest()
    payslip.hash_lock = digest

    return payslip
