import unittest
from decimal import Decimal
from thpay.domain.entities import Company, Contract, Employee, TaxRegime, WorkerCategory, Dependent
from thpay.engine.context import CalculationContext
from thpay.pipelines.monthly import process_monthly_payroll

class TestMonthlyPipeline(unittest.TestCase):
    def setUp(self):
        self.company = Company(
            cnpj="12.345.678/0001-90",
            corporate_name="Tech Solutions Brasil Ltda",
            tax_regime=TaxRegime.LUCRO_REAL,
            cnae="6201-5/01",
            fpas="515",
            other_entities_code="0079",
            rat_basic=Decimal("0.02"),
            fap=Decimal("1.0000")
        )
        self.employee = Employee(
            cpf="123.456.789-00",
            full_name="Carlos Eduardo Silva",
            category=WorkerCategory.CLT_GERAL,
            dependents=[Dependent(name="Lucas Silva", relationship="Filho", is_irrf_dependent=True)]
        )
        self.contract = Contract(
            contract_id="CT-001",
            employee=self.employee,
            company=self.company,
            base_salary=Decimal("5000.00"),
            workload_monthly_hours=220
        )

    def test_full_monthly_calculation(self):
        ctx = CalculationContext(
            competence="2026-09",
            worked_days=30,
            business_days=25,
            rest_and_holidays=5,
            overtime_50_hours=Decimal("10.00"),
            transport_ticket_real_cost=Decimal("250.00"),
            meal_ticket_deduction_amount=Decimal("100.00")
        )

        payslip = process_monthly_payroll(self.contract, ctx)

        self.assertEqual(payslip.contract_id, "CT-001")
        self.assertEqual(payslip.competence, "2026-09")
        self.assertGreater(payslip.gross_total, Decimal("5000.00"))
        self.assertGreater(payslip.discounts_total, Decimal("0.00"))
        self.assertGreater(payslip.net_total, Decimal("0.00"))
        self.assertEqual(payslip.net_total, payslip.gross_total - payslip.discounts_total)
        self.assertIsNotNone(payslip.hash_lock)
        self.assertEqual(len(payslip.hash_lock), 64) # SHA-256

    def test_anti_negative_salary_protection(self):
        # Colaborador com salario R$ 1500 mas desconto abusivo que excede o provento
        low_contract = Contract(
            contract_id="CT-002",
            employee=self.employee,
            company=self.company,
            base_salary=Decimal("1500.00"),
            workload_monthly_hours=220
        )
        ctx = CalculationContext(
            competence="2026-09",
            worked_days=30,
            consigned_loan_deduction=Decimal("2000.00") # Excede o salario!
        )

        payslip = process_monthly_payroll(low_contract, ctx)

        # O liquido nao pode ser menor que zero
        self.assertEqual(payslip.net_total, Decimal("0.00"))
        # Deve conter a rubrica 1099 de insuficiencia de saldo
        has_anti_negative = any(item.rubric_code == "1099" for item in payslip.items)
        self.assertTrue(has_anti_negative)

if __name__ == "__main__":
    unittest.main()
