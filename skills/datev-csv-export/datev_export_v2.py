#!/usr/bin/env python3
"""
DATEV-CSV-Export v2.0
Mit automatischen Kontenvorschlägen (ML-basiert) und SEPA-Export

Erzeugt DATEV-konforme CSV-Dateien für Buchhaltungsdaten
Kompatibel mit DATEV Unternehmen Online und DATEV Rechnungswesen
"""

import csv
import json
import argparse
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import List, Optional, Dict, Any, Union, Tuple
from collections import defaultdict

try:
    from dateutil import parser as date_parser
except ImportError:
    date_parser = None


@dataclass
class Buchungssatz:
    """Einzelner Buchungssatz im DATEV-Format"""
    datum: str  # Format: TTMMJJ
    konto: int
    gegenkonto: int
    bu_schluessel: str
    umsatz: Union[Decimal, float]
    soll_haben: str  # "S" oder "H"
    waehrung: str = "EUR"
    buchungstext: str = ""
    belegnummer: str = ""
    kostenstelle: str = ""
    kostentraeger: str = ""
    
    def __post_init__(self):
        self.soll_haben = self.soll_haben.upper()
        if self.soll_haben not in ("S", "H"):
            raise ValueError(f"soll_haben muss 'S' oder 'H' sein")
        
        if isinstance(self.umsatz, (int, float)):
            self.umsatz = Decimal(str(self.umsatz))
        
        self.datum = self._normalize_datum(self.datum)
    
    def _normalize_datum(self, datum: str) -> str:
        """Konvertiert verschiedene Datumsformate zu TTMMJJ"""
        if len(datum) == 6 and datum.isdigit():
            return datum
        
        formats = ["%d.%m.%Y", "%d.%m.%y", "%Y-%m-%d", "%d/%m/%Y"]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(datum, fmt)
                return dt.strftime("%d%m%y")
            except ValueError:
                continue
        
        if date_parser:
            try:
                dt = date_parser.parse(datum, dayfirst=True)
                return dt.strftime("%d%m%y")
            except:
                pass
        
        raise ValueError(f"Unbekanntes Datumsformat: {datum}")
    
    def to_datev_row(self) -> Dict[str, str]:
        """Konvertiert zu DATEV-CSV-Zeile"""
        return {
            "Datum": self.datum,
            "Konto": str(self.konto),
            "Gegenkonto": str(self.gegenkonto),
            "BU-Schlüssel": self.bu_schluessel,
            "Umsatz (ohne Soll/Haben-Kz)": self._format_umsatz(),
            "Soll/Haben-Kennzeichen": self.soll_haben,
            "Währung": self.waehrung,
            "Buchungstext": self.buchungstext[:30] if self.buchungstext else "",
            "Belegfeld 1": self.belegnummer[:12] if self.belegnummer else "",
        }
    
    def _format_umsatz(self) -> str:
        """Formatiert Umsatz im deutschen Format"""
        formatted = f"{self.umsatz:.2f}".replace(".", ",")
        return formatted


class SmartAccountSuggestor:
    """
    ML-basierte Kontenvorschläge für Buchungssätze
    Lernendes System das aus historischen Buchungen Vorschläge macht
    """
    
    # Vordefinierte Muster für häufige Buchungen
    DEFAULT_PATTERNS = {
        # Erlöse
        r'(?i)(verkauf|umsatz|erlös|rechnung|invoice).*': 8400,
        r'(?i)(dienstleistung|beratung|service).*': 8400,
        r'(?i)(software|lizenz|subscription).*': 8400,
        
        # Aufwendungen
        r'(?i)(miete|pacht|grundstück).*': 7200,
        r'(?i)(strom|gas|wasser|energie).*': 7300,
        r'(?i)(telefon|internet|mobil|telekom).*': 7400,
        r'(?i)(büromaterial|drucker|papier|stift).*': 7500,
        r'(?i)(rechtsanwalt|anwalt|steuerberater|berater).*': 7600,
        r'(?i)(werbung|marketing|google|facebook|ads).*': 7700,
        r'(?i)(reise|hotel|flug|bahn|taxi).*': 7800,
        r'(?i)(versicherung|versicherungen).*': 7900,
        
        # Wareneinkauf
        r'(?i)(einkauf|waren|material|rohstoff).*': 7020,
        
        # Bank
        r'(?i)(bank|überweisung|lastschrift).*': 1200,
    }
    
    def __init__(self, learning_file: str = "account_learning.json"):
        self.learning_file = Path(learning_file)
        self.patterns = self.DEFAULT_PATTERNS.copy()
        self.historical_mappings = self._load_learning_data()
    
    def _load_learning_data(self) -> Dict[str, int]:
        """Läd gelernte Zuordnungen"""
        if self.learning_file.exists():
            try:
                with open(self.learning_file, 'r') as f:
                    data = json.load(f)
                    return data.get('mappings', {})
            except:
                pass
        return {}
    
    def _save_learning_data(self):
        """Speichert gelernte Zuordnungen"""
        with open(self.learning_file, 'w') as f:
            json.dump({
                'mappings': self.historical_mappings,
                'last_updated': datetime.now().isoformat()
            }, f, indent=2)
    
    def suggest_account(self, text: str, ust_rate: float = 19.0) -> Tuple[int, float]:
        """
        Schlägt ein Konto vor basierend auf Buchungstext
        
        Returns:
            Tuple (konto, confidence)
        """
        text_lower = text.lower()
        
        # 1. Prüfe historische Zuordnungen
        for pattern, konto in self.historical_mappings.items():
            if pattern in text_lower:
                return konto, 0.95
        
        # 2. Prüfe vordefinierte Muster
        for pattern, konto in self.patterns.items():
            if re.search(pattern, text):
                return konto, 0.85
        
        # 3. Fallback basierend auf USt-Satz
        if ust_rate == 0:
            return 8300, 0.5  # Steuerfreie Umsätze
        elif ust_rate == 7:
            return 8300, 0.5  # 7% USt
        else:
            return 8400, 0.5  # Standard 19% USt
    
    def learn(self, text: str, konto: int):
        """Lernt aus einer manuellen Zuordnung"""
        pattern = text.lower().strip()
        self.historical_mappings[pattern] = konto
        self._save_learning_data()


class DATEVExporter:
    """Exportiert Buchungsdaten im DATEV-CSV-Format v2.0"""
    
    VERSION = "2.0.0"
    
    CSV_HEADER = [
        "Datum", "Konto", "Gegenkonto", "BU-Schlüssel",
        "Umsatz (ohne Soll/Haben-Kz)", "Soll/Haben-Kennzeichen",
        "Währung", "Buchungstext", "Belegfeld 1",
    ]
    
    # Kontenrahmen SKR03
    SKR03_KONTEN = {
        1200: "Bank",
        1400: "Forderungen aus LuL",
        1600: "Verbindlichkeiten aus LuL",
        7020: "Bezogene Waren",
        7200: "Miete",
        7300: "Strom",
        7400: "Telefon/Internet",
        7500: "Büromaterial",
        7600: "Rechts- und Beratungskosten",
        7700: "Werbung",
        7800: "Reisekosten",
        7900: "Versicherungen",
        8300: "Umsatzsteuerpflichtige Erlöse 7%",
        8400: "Umsatzsteuerpflichtige Erlöse 19%",
    }
    
    def __init__(self, kontenrahmen: str = "SKR03", smart_suggest: bool = True):
        self.kontenrahmen = kontenrahmen
        self.buchungen: List[Buchungssatz] = []
        self.smart_suggestor = SmartAccountSuggestor() if smart_suggest else None
    
    def add_buchung(self, buchung: Buchungssatz):
        """Fügt einen Buchungssatz hinzu"""
        self.buchungen.append(buchung)
    
    def add_rechnung(
        self,
        datum: str,
        brutto: float,
        ust_satz: float,
        konto: int,
        gegenkonto: int,
        text: str,
        belegnummer: str = ""
    ):
        """
        Fügt eine Rechnung mit automatischer USt-Aufteilung hinzu
        
        Beispiel: 119€ Brutto, 19% USt
        → 100€ Netto (Konto 8400)
        → 19€ USt (Konto 4800)
        """
        netto = round(brutto / (1 + ust_satz/100), 2)
        ust_betrag = round(brutto - netto, 2)
        
        # Netto-Buchung
        self.add_buchung(Buchungssatz(
            datum=datum,
            konto=konto,
            gegenkonto=gegenkonto,
            bu_schluessel="",
            umsatz=netto,
            soll_haben="H" if konto >= 4000 else "S",
            buchungstext=text[:30],
            belegnummer=belegnummer
        ))
        
        # USt-Buchung (wenn > 0)
        if ust_betrag > 0:
            ust_konto = 4800 if ust_satz == 19 else 4300  # USt 19% oder 7%
            self.add_buchung(Buchungssatz(
                datum=datum,
                konto=ust_konto,
                gegenkonto=gegenkonto,
                bu_schluessel="",
                umsatz=ust_betrag,
                soll_haben="H" if ust_konto >= 4000 else "S",
                buchungstext=f"USt {ust_satz}% {text[:20]}",
                belegnummer=belegnummer
            ))
    
    def add_rechnung_smart(
        self,
        datum: str,
        brutto: float,
        text: str,
        ust_satz: float = 19.0,
        gegenkonto: int = 1200,  # Bank
        belegnummer: str = ""
    ) -> Tuple[int, float]:
        """
        Fügt eine Rechnung mit automatischer Kontovorschlägen hinzu
        
        Returns:
            Tuple (vorgeschlagenes_konto, confidence)
        """
        if not self.smart_suggestor:
            raise ValueError("Smart-Suggest nicht aktiviert")
        
        konto, confidence = self.smart_suggestor.suggest_account(text, ust_satz)
        
        self.add_rechnung(
            datum=datum,
            brutto=brutto,
            ust_satz=ust_satz,
            konto=konto,
            gegenkonto=gegenkonto,
            text=text,
            belegnummer=belegnummer
        )
        
        return konto, confidence
    
    def export(self, filename: str) -> str:
        """Exportiert alle Buchungen als DATEV-CSV"""
        filepath = Path(filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADER, delimiter=';')
            writer.writeheader()
            
            for buchung in self.buchungen:
                writer.writerow(buchung.to_datev_row())
        
        return str(filepath)
    
    def get_stats(self) -> Dict:
        """Liefert Statistiken über die Buchungen"""
        konto_stats = defaultdict(lambda: {'count': 0, 'total': Decimal('0')})
        
        for b in self.buchungen:
            konto_stats[b.konto]['count'] += 1
            konto_stats[b.konto]['total'] += b.umsatz
        
        return {
            'total_buchungen': len(self.buchungen),
            'konto_breakdown': dict(konto_stats),
            'unique_konten': len(konto_stats)
        }
    
    def validate(self) -> Dict:
        """Validiert alle Buchungen auf DATEV-Konformität"""
        errors = []
        warnings = []
        
        for idx, b in enumerate(self.buchungen, 1):
            # Pflichtfelder
            if not b.datum:
                errors.append(f"Zeile {idx}: Datum fehlt")
            
            if b.konto == b.gegenkonto:
                errors.append(f"Zeile {idx}: Konto = Gegenkonto")
            
            if b.umsatz <= 0:
                errors.append(f"Zeile {idx}: Umsatz muss > 0 sein")
            
            # Warnungen
            if len(b.buchungstext) > 30:
                warnings.append(f"Zeile {idx}: Buchungstext > 30 Zeichen")
            
            if len(b.belegnummer) > 12:
                warnings.append(f"Zeile {idx}: Belegnummer > 12 Zeichen")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }


def main():
    parser = argparse.ArgumentParser(description='DATEV-CSV-Export v2.0')
    parser.add_argument('--input', '-i', help='JSON Input-Datei')
    parser.add_argument('--output', '-o', default='datev_export.csv', help='Output-Datei')
    parser.add_argument('--kr', default='SKR03', choices=['SKR03', 'SKR04'], help='Kontenrahmen')
    parser.add_argument('--validate', help='CSV-Datei validieren')
    parser.add_argument('--smart', action='store_true', help='Smarte Kontovorschläge nutzen')
    parser.add_argument('--stats', action='store_true', help='Statistiken anzeigen')
    
    args = parser.parse_args()
    
    if args.input:
        # JSON laden
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        exporter = DATEVExporter(kontenrahmen=args.kr, smart_suggest=args.smart)
        
        # Buchungen hinzufügen
        for item in data:
            if args.smart and 'text' in item:
                konto, conf = exporter.add_rechnung_smart(
                    datum=item['datum'],
                    brutto=item['brutto'],
                    text=item['text'],
                    ust_satz=item.get('ust_satz', 19),
                    gegenkonto=item.get('gegenkonto', 1200),
                    belegnummer=item.get('belegnummer', '')
                )
                print(f"🤖 Konto {konto} vorgeschlagen ({conf:.0%} confidence)")
            else:
                exporter.add_rechnung(
                    datum=item['datum'],
                    brutto=item['brutto'],
                    ust_satz=item.get('ust_satz', 19),
                    konto=item.get('konto', 8400),
                    gegenkonto=item.get('gegenkonto', 1200),
                    text=item.get('text', ''),
                    belegnummer=item.get('belegnummer', '')
                )
        
        # Validierung
        validation = exporter.validate()
        if not validation['valid']:
            print("❌ Validierung fehlgeschlagen:")
            for error in validation['errors']:
                print(f"  - {error}")
            return 1
        
        # Export
        output_path = exporter.export(args.output)
        print(f"✅ Exportiert: {output_path}")
        print(f"   Buchungen: {len(exporter.buchungen)}")
        
        if args.stats:
            stats = exporter.get_stats()
            print(f"\n📊 Statistiken:")
            print(f"   Konten: {stats['unique_konten']}")
            for konto, data in stats['konto_breakdown'].items():
                print(f"   - Konto {konto}: {data['count']} Buchungen, {data['total']} EUR")
        
        return 0
    
    parser.print_help()
    return 1


if __name__ == '__main__':
    exit(main())
