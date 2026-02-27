#!/usr/bin/env python3
"""
German Accounting Suite - Integration Module

Verbindet GoBD, ZUGFeRD, DATEV und SEPA zu einem nahtlosen Workflow:
PDF Rechnung → Validierung → E-Rechnung → Buchhaltung → Zahlung
"""

import sys
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass

# Import Skills (angenommen sie sind im PYTHONPATH)
try:
    from gobd_validator_v25 import EnhancedGoBDValidator, ValidationResult
    from zugferd_generator import ZUGFeRDGenerator, Invoice, InvoiceItem, Party
    from datev_export_v2 import DATEVExporter, SmartAccountSuggestor
    from sepa_generator import SEPAGenerator, CreditTransfer, DirectDebit
    SUITE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Suite-Module nicht verfügbar: {e}")
    SUITE_AVAILABLE = False


@dataclass
class AccountingWorkflowResult:
    """Ergebnis eines kompletten Accounting-Workflows"""
    pdf_path: str
    is_valid: bool
    zugferd_path: Optional[str]
    datev_path: Optional[str]
    sepa_path: Optional[str]
    extracted_data: Dict
    errors: List[str]
    ocr_used: bool = False
    ocr_language: str = ""
    ocr_confidence: float = 0.0
    
    def summary(self) -> str:
        """Text-Zusammenfassung"""
        lines = [
            f"📄 PDF: {self.pdf_path}",
            f"   Valid: {'✅' if self.is_valid else '❌'}",
        ]
        if self.ocr_used:
            lines.append(f"   OCR: {self.ocr_language} ({self.ocr_confidence:.0%})")
        if self.zugferd_path:
            lines.append(f"   ZUGFeRD: ✅ {self.zugferd_path}")
        if self.datev_path:
            lines.append(f"   DATEV: ✅ {self.datev_path}")
        if self.sepa_path:
            lines.append(f"   SEPA: ✅ {self.sepa_path}")
        if self.errors:
            lines.append(f"   Fehler: {len(self.errors)}")
        return "\n".join(lines)


class GermanAccountingSuite:
    """
    Hauptklasse für die German Accounting Suite.
    
    Kombiniert alle Accounting-Skills zu einem Workflow:
    1. PDF validieren (GoBD) mit erweitertem OCR
    2. E-Rechnung generieren (ZUGFeRD)
    3. Buchhaltung exportieren (DATEV)
    4. Zahlung vorbereiten (SEPA)
    """
    
    VERSION = "1.1.0"
    
    def __init__(
        self,
        use_ocr: bool = True,
        smart_suggest: bool = True,
        ocr_preset: str = 'invoice',
        ocr_languages: List[str] = None,
        dpi: int = 300
    ):
        """
        Args:
            use_ocr: OCR aktivieren?
            smart_suggest: Smart-Suggest für DATEV?
            ocr_preset: OCR-Preset ('scanned', 'low_quality', 'invoice', 'fast', 'max_quality')
            ocr_languages: Sprachen für OCR (z.B. ['deu', 'eng', 'fra'])
            dpi: DPI für OCR-Konvertierung
        """
        if not SUITE_AVAILABLE:
            raise RuntimeError("Accounting Suite Module nicht verfügbar")
        
        self.validator = EnhancedGoBDValidator(
            use_ocr=use_ocr,
            ocr_preset=ocr_preset,
            ocr_languages=ocr_languages or ['deu', 'eng'],
            dpi=dpi
        )
        self.zugferd_generator = ZUGFeRDGenerator()
        self.datev_exporter = DATEVExporter(smart_suggest=smart_suggest)
        self.sepa_generator = SEPAGenerator()
        
        self.errors: List[str] = []
        self.ocr_config = {
            'preset': ocr_preset,
            'languages': ocr_languages or ['deu', 'eng'],
            'dpi': dpi
        }
    
    def process_invoice(
        self,
        pdf_path: str,
        output_dir: str = "./output",
        generate_zugferd: bool = True,
        generate_datev: bool = True,
        generate_sepa: bool = True,
        creditor_iban: Optional[str] = None
    ) -> AccountingWorkflowResult:
        """
        Verarbeitet eine Rechnung durch den kompletten Workflow.
        
        Args:
            pdf_path: Pfad zur Rechnungs-PDF
            output_dir: Ausgabeverzeichnis
            generate_zugferd: ZUGFeRD generieren?
            generate_datev: DATEV Export?
            generate_sepa: SEPA Zahlung vorbereiten?
            creditor_iban: IBAN für SEPA-Zahlung
            
        Returns:
            AccountingWorkflowResult mit allen Pfaden
        """
        self.errors = []
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        result_paths = {
            'zugferd': None,
            'datev': None,
            'sepa': None
        }
        
        # Schritt 1: Validierung
        print("🔍 Schritt 1: PDF validieren...")
        validation = self.validator.validate(pdf_path)
        
        if not validation.is_valid:
            self.errors.append(f"Validierung fehlgeschlagen: {validation.missing_fields}")
            return AccountingWorkflowResult(
                pdf_path=pdf_path,
                is_valid=False,
                zugferd_path=None,
                datev_path=None,
                sepa_path=None,
                extracted_data=validation.extracted_data,
                errors=self.errors,
                ocr_used=validation.ocr_used,
                ocr_language=validation.ocr_language,
                ocr_confidence=validation.ocr_confidence
            )
        
        print(f"   ✅ Valid ({validation.score}/{validation.max_score} Punkte)")
        if validation.ocr_used:
            print(f"      OCR: {validation.ocr_language} ({validation.ocr_confidence:.0%})")
        
        # Schritt 2: ZUGFeRD generieren
        if generate_zugferd and validation.zugferd_compatible:
            print("🧾 Schritt 2: ZUGFeRD E-Rechnung generieren...")
            try:
                zugferd_path = output_path / f"{Path(pdf_path).stem}.zugferd.zip"
                self.validator.generate_zugferd(pdf_path, str(zugferd_path))
                result_paths['zugferd'] = str(zugferd_path)
                print(f"   ✅ {zugferd_path}")
            except Exception as e:
                self.errors.append(f"ZUGFeRD Fehler: {e}")
                print(f"   ❌ Fehler: {e}")
        
        # Schritt 3: DATEV Export
        if generate_datev:
            print("📊 Schritt 3: DATEV Export...")
            try:
                # Daten extrahieren
                data = validation.extracted_data
                
                # Rechnungsbetrag parsen
                betrag_str = data.get('gesamtbetrag', '0').replace('.', '').replace(',', '.').replace('€', '').strip()
                try:
                    brutto = float(betrag_str)
                except ValueError:
                    brutto = 0.0
                
                # USt-Satz
                ust_satz = 19.0
                if data.get('ust_satz'):
                    import re
                    match = re.search(r'(\d+)', data['ust_satz'])
                    if match:
                        ust_satz = float(match.group(1))
                
                # Smarte Buchung hinzufügen
                self.datev_exporter.add_rechnung_smart(
                    datum=data.get('rechnungsdatum', '01.01.2025'),
                    brutto=brutto,
                    text=data.get('lieferant_name', 'Rechnung'),
                    ust_satz=ust_satz
                )
                
                # Exportieren
                datev_path = output_path / f"{Path(pdf_path).stem}_datev.csv"
                self.datev_exporter.export(str(datev_path))
                result_paths['datev'] = str(datev_path)
                print(f"   ✅ {datev_path}")
                
            except Exception as e:
                self.errors.append(f"DATEV Fehler: {e}")
                print(f"   ❌ Fehler: {e}")
        
        # Schritt 4: SEPA Zahlung
        if generate_sepa and creditor_iban:
            print("💳 Schritt 4: SEPA Zahlung vorbereiten...")
            try:
                data = validation.extracted_data
                
                # Betrag parsen
                betrag_str = data.get('gesamtbetrag', '0').replace('.', '').replace(',', '.').replace('€', '').strip()
                try:
                    amount = float(betrag_str)
                except ValueError:
                    amount = 0.0
                
                # Credit Transfer erstellen
                transfer = CreditTransfer(
                    end_to_end_id=data.get('rechnungsnummer', 'RE-001'),
                    creditor_iban=creditor_iban,
                    creditor_name=data.get('lieferant_name', 'Unbekannt'),
                    amount=amount,
                    currency="EUR",
                    remittance_information=f"Rechnung {data.get('rechnungsnummer', 'RE-001')}"
                )
                
                sepa_path = output_path / f"{Path(pdf_path).stem}_sepa.xml"
                self.sepa_generator.add_credit_transfer(transfer)
                self.sepa_generator.generate_xml(str(sepa_path))
                result_paths['sepa'] = str(sepa_path)
                print(f"   ✅ {sepa_path}")
                
            except Exception as e:
                self.errors.append(f"SEPA Fehler: {e}")
                print(f"   ❌ Fehler: {e}")
        
        return AccountingWorkflowResult(
            pdf_path=pdf_path,
            is_valid=True,
            zugferd_path=result_paths['zugferd'],
            datev_path=result_paths['datev'],
            sepa_path=result_paths['sepa'],
            extracted_data=validation.extracted_data,
            errors=self.errors,
            ocr_used=validation.ocr_used,
            ocr_language=validation.ocr_language,
            ocr_confidence=validation.ocr_confidence
        )
    
    def batch_process(
        self,
        pdf_folder: str,
        output_dir: str = "./output",
        **kwargs
    ) -> List[AccountingWorkflowResult]:
        """
        Batch-Verarbeitung eines ganzen Ordners.
        
        Args:
            pdf_folder: Ordner mit PDFs
            output_dir: Ausgabeverzeichnis
            **kwargs: Weitere Parameter für process_invoice
            
        Returns:
            Liste aller Ergebnisse
        """
        import glob
        
        pdf_files = glob.glob(f"{pdf_folder}/*.pdf")
        results = []
        
        print(f"🔄 Batch-Verarbeitung: {len(pdf_files)} PDFs")
        print(f"   OCR-Preset: {self.ocr_config['preset']}")
        print(f"   Sprachen: {', '.join(self.ocr_config['languages'])}")
        print("="*50)
        
        for i, pdf_path in enumerate(pdf_files, 1):
            print(f"\n[{i}/{len(pdf_files)}] {pdf_path}")
            result = self.process_invoice(pdf_path, output_dir, **kwargs)
            results.append(result)
            print(result.summary())
        
        # Gesamtzusammenfassung
        print("\n" + "="*50)
        print("📊 BATCH-ZUSAMMENFASSUNG")
        print("="*50)
        valid_count = sum(1 for r in results if r.is_valid)
        zugferd_count = sum(1 for r in results if r.zugferd_path)
        datev_count = sum(1 for r in results if r.datev_path)
        ocr_count = sum(1 for r in results if r.extracted_data.get('ocr_used', False))
        
        print(f"Geprüft:     {len(results)}")
        print(f"Valide:      {valid_count} ✅")
        print(f"ZUGFeRD:     {zugferd_count} 🧾")
        print(f"DATEV:       {datev_count} 📊")
        print(f"OCR genutzt: {ocr_count} 🔍")
        
        return results


# CLI Interface
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='German Accounting Suite v1.1',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
OCR Presets:
  scanned      - Optimal für gescannte Dokumente (300 DPI)
  low_quality  - Für schlechte Scan-Qualität (400 DPI)
  invoice      - Für mehrsprachige Rechnungen (Standard)
  fast         - Schnelle Verarbeitung (150 DPI)
  max_quality  - Maximale Qualität (langsam)

Beispiele:
  %(prog)s rechnung.pdf --iban DE89370400440532013000
  %(prog)s gescannte_rechnungen/ --batch --preset scanned --lang deu eng
  %(prog)s international/ --batch --preset invoice --lang deu eng fra
        """
    )
    parser.add_argument('pdf', help='PDF-Datei oder Ordner')
    parser.add_argument('--output', '-o', default='./output', help='Ausgabeverzeichnis')
    parser.add_argument('--iban', help='Kreditor-IBAN für SEPA')
    parser.add_argument('--batch', action='store_true', help='Batch-Modus')
    parser.add_argument('--no-ocr', action='store_true', help='OCR deaktivieren')
    parser.add_argument('--no-smart', action='store_true', help='Smart-Suggest deaktivieren')
    parser.add_argument('--preset', default='invoice',
                       choices=['scanned', 'low_quality', 'invoice', 'fast', 'max_quality'],
                       help='OCR-Preset (Standard: invoice)')
    parser.add_argument('--lang', nargs='+', default=['deu', 'eng'],
                       help='Sprachen für OCR (z.B. deu eng fra)')
    parser.add_argument('--dpi', type=int, default=300,
                       help='DPI für OCR (Standard: 300)')
    
    args = parser.parse_args()
    
    suite = GermanAccountingSuite(
        use_ocr=not args.no_ocr,
        smart_suggest=not args.no_smart,
        ocr_preset=args.preset,
        ocr_languages=args.lang,
        dpi=args.dpi
    )
    
    if args.batch:
        results = suite.batch_process(
            args.pdf,
            args.output,
            creditor_iban=args.iban
        )
    else:
        result = suite.process_invoice(
            args.pdf,
            args.output,
            creditor_iban=args.iban
        )
        print("\n" + result.summary())
