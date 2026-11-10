import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ria_transfer_trends as rt  # noqa: E402


class NormalizeCountryTests(unittest.TestCase):
    def test_turkey_spellings(self):
        for value in ("Türkiye", "TÜRKİYE", "Turkiye", "turkey", "TUR", "تركيا", "‏تركيا"):
            self.assertEqual(rt.normalize_country(value), "TR", value)

    def test_jordan_hamza_variants(self):
        self.assertEqual(rt.normalize_country("الأردن"), "JO")
        self.assertEqual(rt.normalize_country("الاردن"), "JO")

    def test_unknown_kept_uppercase(self):
        self.assertEqual(rt.normalize_country("germany"), "GERMANY")


class RouteTests(unittest.TestCase):
    def test_arrows_and_separators(self):
        for route in ("TR → EG", "TR->EG", "TR-->EG", "TR => EG", "TR > EG", "TR / EG", "Türkiye - مصر"):
            self.assertEqual(rt.split_route(route), ["TR", "EG"], route)

    def test_explicit_columns_win(self):
        row = {"From": "Türkiye", "To": "Egypt", "Route": "EG → TR"}
        self.assertEqual(rt.route_from_row(row)[:2], ("TR", "EG"))


class CodeTests(unittest.TestCase):
    def test_alnum_and_embedded(self):
        self.assertEqual(rt.code_from_row({"PIN": "it-9314773257"}), "IT9314773257")
        self.assertEqual(rt.code_from_row({"Note": "Order: IT9314773257"}), "IT9314773257")

    def test_code_column_preferred_over_phone(self):
        row = {"Phone": "905551234567", "Order Number": "bad"}
        self.assertEqual(rt.code_from_row(row), "")


class AnalyzeTests(unittest.TestCase):
    def _write(self, text, encoding):
        tmp = tempfile.NamedTemporaryFile("wb", suffix=".csv", delete=False)
        tmp.write(text.encode(encoding))
        tmp.close()
        self.addCleanup(Path(tmp.name).unlink)
        return Path(tmp.name)

    CSV = (
        "رقم الحوالة;المسار;الحالة\n"
        "IT9314773257;تركيا → مصر;مدفوعة\n"
        "1234567890;Türkiye -> Syria;معلقة\n"
        "1234567890;العراق ⇒ TR;مدفوعة\n"
        "x;EG → MA;ملغاة\n"
    )

    def _check(self, report):
        self.assertEqual(report["total_rows"], 4)
        self.assertEqual(report["valid_code_count"], 3)
        self.assertEqual(report["duplicate_codes"], {"1234567890": 2})
        self.assertEqual(report["from_turkey_count"], 2)
        self.assertEqual(report["to_country_counts"], {"EG": 1, "SY": 1})
        self.assertEqual(report["to_turkey_count"], 1)
        self.assertEqual(report["to_turkey_status_counts"], {"مدفوعة": 1})

    def test_encodings(self):
        for encoding in ("utf-8", "utf-8-sig", "utf-16", "cp1256"):
            text = self.CSV.replace("Türkiye", "Turkiye") if encoding == "cp1256" else self.CSV
            text = text.replace("⇒", "=>").replace("→", "->") if encoding == "cp1256" else text
            with self.subTest(encoding=encoding):
                self._check(rt.analyze(self._write(text, encoding)))


if __name__ == "__main__":
    unittest.main()
