from decimal import Decimal
from thpay.domain.entities import Company, Contract, Employee, TaxRegime, WorkerCategory, Dependent
from thpay.engine.context import CalculationContext
from thpay.pipelines.monthly import process_monthly_payroll

def run_demo():
    print("================================================================================")
    print("ThPay // Demonstracao de Processamento de Folha de Pagamento Determinística")
    print("================================================================================")

    company = Company(
        cnpj="12.345.678/0001-90",
        corporate_name="Tech Solutions Brasil Ltda",
        tax_regime=TaxRegime.LUCRO_REAL,
        cnae="6201-5/01",
        fpas="515",
        other_entities_code="0079",
        rat_basic=Decimal("0.02"),
        fap=Decimal("1.2500")
    )

    employee = Employee(
        cpf="123.456.789-00",
        full_name="Carlos Eduardo da Silva",
        category=WorkerCategory.CLT_GERAL,
        dependents=[
            Dependent(name="Lucas Silva", relationship="Filho", is_irrf_dependent=True)
        ]
    )

    contract = Contract(
        contract_id="MAT-2026-0042",
        employee=employee,
        company=company,
        base_salary=Decimal("6200.00"),
        workload_monthly_hours=220
    )

    ctx = CalculationContext(
        competence="2026-09",
        worked_days=30,
        business_days=25,
        rest_and_holidays=5,
        overtime_50_hours=Decimal("12.00"),
        night_hours=Decimal("14.00"),
        transport_ticket_real_cost=Decimal("380.00"),
        meal_ticket_deduction_amount=Decimal("120.00"),
        health_insurance_deduction=Decimal("85.50")
    )

    payslip = process_monthly_payroll(contract, ctx)

    print(f"\nEmpresa: {company.corporate_name} (CNPJ: {company.cnpj})")
    print(f"Colaborador: {employee.full_name} (CPF: {employee.cpf})")
    print(f"Competencia: {payslip.competence} | Matricula: {payslip.contract_id}")
    print(f"Salario Contratual: R$ {contract.base_salary}")
    print(f"RAT Efetivo Ajustado (RAT x FAP): {company.rat_adjusted * Decimal('100')}%")
    print("-" * 80)
    print(f"{'Cod':<6} {'Rubrica':<35} {'Tipo':<12} {'Ref':<10} {'Valor (R$)':>12}")
    print("-" * 80)

    for item in payslip.items:
        tipo_str = "Provento" if item.rubric_type.value == "1" else "Desconto"
        ref_str = f"{item.reference:.2f}" if item.reference is not None else "-"
        print(f"{item.rubric_code:<6} {item.rubric_name:<35} {tipo_str:<12} {ref_str:<10} {item.amount:>12.2f}")

    print("=" * 80)
    print(f"{'Total de Proventos:':<64} R$ {payslip.gross_total:>10.2f}")
    print(f"{'Total de Descontos:':<64} R$ {payslip.discounts_total:>10.2f}")
    print(f"{'Salario Liquido a Receber:':<64} R$ {payslip.net_total:>10.2f}")
    print("-" * 80)
    print("Bases de Encargos Fiscais e Previdenciarios:")
    print(f"- Base INSS:  R$ {payslip.inss_base:>10.2f}")
    print(f"- Base IRRF:  R$ {payslip.irrf_base:>10.2f}")
    print(f"- Base FGTS:  R$ {payslip.fgts_base:>10.2f} (Valor Depositado pela Empresa 8%: R$ {payslip.fgts_amount:.2f})")
    print("-" * 80)
    print(f"Hash Criptografico SHA-256 (Version Lock): {payslip.hash_lock}")
    print("=" * 80)

if __name__ == "__main__":
    run_demo()
