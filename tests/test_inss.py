import unittest
from decimal import Decimal
from thpay.tax.inss import calculate_inss_employee

class TestINSSCalculation(unittest.TestCase):
    def test_minimum_wage_bracket(self):
        # Base R$ 1412.00 na 1a faixa a 7.5% = R$ 105.90
        base = Decimal("1412.00")
        inss = calculate_inss_employee(base)
        self.assertEqual(inss, Decimal("105.90"))

    def test_intermediate_bracket(self):
        # Base R$ 3000.00:
        # Faixa 1: 1412.00 * 0.075 = 105.90
        # Faixa 2: (2666.68 - 1412.00) * 0.09 = 1254.68 * 0.09 = 112.9212
        # Faixa 3: (3000.00 - 2666.68) * 0.12 = 333.32 * 0.12 = 39.9984
        # Total = 105.90 + 112.9212 + 39.9984 = 258.8196 -> 258.82
        base = Decimal("3000.00")
        inss = calculate_inss_employee(base)
        self.assertEqual(inss, Decimal("258.82"))

    def test_above_ceiling(self):
        # Base R$ 10000.00 (Teto 7786.02):
        # Faixa 1: 1412.00 * 0.075 = 105.90
        # Faixa 2: 1254.68 * 0.09 = 112.9212
        # Faixa 3: 1333.35 * 0.12 = 160.0020
        # Faixa 4: (7786.02 - 4000.03) * 0.14 = 3785.99 * 0.14 = 530.0386
        # Total = 105.90 + 112.9212 + 160.002 + 530.0386 = 908.8618 -> 908.86
        base = Decimal("10000.00")
        inss = calculate_inss_employee(base)
        self.assertEqual(inss, Decimal("908.86"))

    def test_multiple_employers_deduction(self):
        base = Decimal("5000.00")
        full_inss = calculate_inss_employee(base)
        already_paid = Decimal("200.00")
        net_inss = calculate_inss_employee(base, already_contributed_other_source=already_paid)
        self.assertEqual(net_inss, full_inss - already_paid)

if __name__ == "__main__":
    unittest.main()
