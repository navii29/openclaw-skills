#!/usr/bin/env python3
"""Test PDF Rechnung zu DATEV CSV"""

import sys
sys.path.insert(0, '/Users/fridolin/.openclaw/workspace/skills/pdf-rechnung-datev')

from pdf_to_datev import PDFInvoiceParser, DATEVExporter

def run_tests():
    """Test invoice parsing without real PDFs."""
    print("🧪 Testing PDF Rechnung zu DATEV CSV...\n")
    
    # Test 1: Parse Amazon invoice
    print("Test 1: Amazon Rechnung")
    amazon_text = """
    Amazon.de
    Amazon EU S.a r.l.
    
    Rechnungsnummer: DE123456789
    Rechnungsdatum: 15.03.2024
    
    Gesamtbetrag: 89,99 €
    Enthaltene MwSt. 19%: 14,36 €
    
    Artikel:
    1x Kindle Paperwhite
    """
    
    parser1 = PDFInvoiceParser(amazon_text)
    data1 = parser1.parse()
    
    print(f"   Rechnungsnr: {data1.get('rechnungsnummer')} (Expected: DE123456789)")
    print(f"   Datum: {data1.get('datum')} (Expected: 2024-03-15)")
    print(f"   Betrag: {data1.get('betrag_brutto')} (Expected: 89.99)")
    print(f"   Konto: {data1.get('konto')} (Expected: 3400)")
    print()
    
    test1_pass = (
        data1.get('rechnungsnummer') == 'DE123456789' and
        data1.get('datum') == '2024-03-15' and
        data1.get('betrag_brutto') == 89.99 and
        data1.get('konto') == '3400'
    )
    
    # Test 2: Parse Telekom invoice
    print("Test 2: Telekom Rechnung")
    telekom_text = """
    Telekom Deutschland GmbH
    
    Rechnung Nr.: T-987654321
    Datum: 01.02.2024
    
    Rechnungsbetrag: 49,95 €
    zzgl. MwSt. 19%
    """
    
    parser2 = PDFInvoiceParser(telekom_text)
    data2 = parser2.parse()
    
    print(f"   Rechnungsnr: {data2.get('rechnungsnummer')}")
    print(f"   Datum: {data2.get('datum')}")
    print(f"   Betrag: {data2.get('betrag_brutto')}")
    print(f"   Konto: {data2.get('konto')} (Expected: 6300 für Telekom)")
    print()
    
    test2_pass = data2.get('konto') == '6300'  # Telekom -> Telefonkosten
    
    # Test 3: Parse REWE receipt
    print("Test 3: REWE Kassenbon")
    rewe_text = """
    REWE Markt GmbH
    
    Beleg-Nr: 12345
    20.02.2024
    
    Summe: 45,67
    MwSt 7%: 2,99
    
    Danke für Ihren Einkauf!
    """
    
    parser3 = PDFInvoiceParser(rewe_text)
    data3 = parser3.parse()
    
    print(f"   Betrag: {data3.get('betrag_brutto')}")
    print(f"   MwSt: {data3.get('mwst_satz')} (Expected: 7)")
    print(f"   Konto: {data3.get('konto')} (Expected: 6400 für Lebensmittel)")
    print()
    
    test3_pass = (
        data3.get('mwst_satz') == '7' and
        data3.get('konto') == '6400'
    )
    
    # Test 4: DATEV Export
    print("Test 4: DATEV CSV Export")
    test_invoices = [
        {
            'rechnungsnummer': 'TEST-001',
            'datum': '2024-03-15',
            'betrag_brutto': 119.00,
            'mwst_satz': '19',
            'lieferant': 'Test GmbH',
            'konto': '6300',
            'gegenkonto': '1200'
        }
    ]
    
    exporter = DATEVExporter(test_invoices)
    netto, mwst = exporter.calculate_net_amount(119.0, '19')
    
    print(f"   Brutto: 119.00 €")
    print(f"   Netto: {netto} € (Expected: ~100.00)")
    print(f"   MwSt: {mwst} € (Expected: ~19.00)")
    print()
    
    test4_pass = abs(netto - 100.0) < 0.1 and abs(mwst - 19.0) < 0.1
    
    # Test 5: Date format conversion
    print("Test 5: Datum Formatierung")
    test_dates = [
        ('15.03.2024', '2024-03-15'),
        ('1.1.24', '2024-01-01'),
    ]
    
    date_tests_pass = True
    for input_date, expected in test_dates:
        parser = PDFInvoiceParser(f"Datum: {input_date}")
        result = parser.extract_date()
        status = "✅" if result == expected else "❌"
        print(f"   {status} {input_date} → {result} (Expected: {expected})")
        if result != expected:
            date_tests_pass = False
    
    print()
    
    # Summary
    results = [test1_pass, test2_pass, test3_pass, test4_pass, date_tests_pass]
    passed = sum(results)
    total = len(results)
    
    print(f"📊 Test Summary: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Skill is ready for production.")
        return True
    else:
        print(f"⚠️ {total - passed} tests failed.")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
