import unittest
from decimal import Decimal
from thpay.tax.irrf import calculate_irrf_employee

class TestIRRFCalculation(unittest.TestCase):
    def test_exempt_income(self):
        # Salario bruto R$ 2000.00 com INSS R$ 158.82
        # Base R$ 1841.18 -> Isento (ate 2259.20)
        gross = Decimal("2000.00")
        inss = Decimal("158.82")
        tax, base_used, method = calculate_irrf_employee(gross, inss, dependents_count=0)
        self.assertEqual(tax, Decimal("0.00"))

    def test_prefers_simplified_discount_when_beneficial(self):
        # Bruto R$ 3500.00, INSS R$ 318.82, 0 dependentes
        # Deducoes legais: 318.82
        # Desconto simplificado: 564.80 (Maior que 318.82!)
        # O motor deve escolher DESCONTO_SIMPLIFICADO
        gross = Decimal("3500.00")
        inss = Decimal("318.82")
        tax, base_used, method = calculate_irrf_employee(gross, inss, dependents_count=0)
        self.assertEqual(method, "DESCONTO_SIMPLIFICADO")
        self.assertEqual(base_used, gross - Decimal("564.80"))

    def test_prefers_traditional_when_legal_deductions_are_higher(self):
        # Bruto R$ 8000.00, INSS R$ 908.86, 3 dependentes (3 * 189.59 = 568.77)
        # Deducoes legais: 908.86 + 568.77 = 1477.63 (Muito maior que 564.80)
        # O motor deve escolher DEDUCOES_LEGAIS
        gross = Decimal("8000.00")
        inss = Decimal("908.86")
        tax, base_used, method = calculate_irrf_employee(gross, inss, dependents_count=3)
        self.assertEqual(method, "DEDUCOES_LEGAIS")
        expected_base = gross - (inss + Decimal("3") * Decimal("189.59"))
        self.assertEqual(base_used, expected_base)

if __name__ == "__main__":
    unittest.main()
