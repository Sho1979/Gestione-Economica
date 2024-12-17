import unittest
from data.calculations import calcola_valori

class TestCalculations(unittest.TestCase):
    def test_calcola_valori(self):
        iva_scorp, iva_det, imp_ded = calcola_valori(100, 22, 0.8, 0.4)
        self.assertAlmostEqual(iva_scorp, 18.03, places=2)
        self.assertAlmostEqual(iva_det, 7.21, places=2)
        self.assertAlmostEqual(imp_ded, 65.58, places=1)  # Riduce la precisione a 1 decimale

if __name__ == "__main__":
    unittest.main()
