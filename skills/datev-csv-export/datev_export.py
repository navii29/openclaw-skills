#!/usr/bin/env python3
"""
DATEV-CSV-Export
Erzeugt DATEV-konforme CSV-Dateien für Buchhaltungsdaten

Kompatibel mit:
- DATEV Unternehmen Online
- DATEV Rechnungswesen
- DATEV Mittelstand Faktura

Kontenrahmen: SKR03, SKR04
"""

import csv
import json
import argparse
from dataclasses import dataclass, asdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

try:
    from dateutil import parser as date_parser
except ImportError:
    date_parser = None


@dataclass
class Buchungssatz:
    """Einzelner Buchungssatz im DATEV-Format"""
    datum: str  # Format: TTMMJJ oder TT.MM.JJJJ
    konto: int
    gegenkonto: int
    bu_schluessel: str  # Buchungsstichwort/BU-Schlüssel
    umsatz: Union[Decimal, float]
    soll_haben: str  # "S" oder "H"
    waehrung: str = "EUR"
    buchungstext: str = ""
    belegnummer: str = ""
    kostenstelle: str = ""
    kostentraeger: str = ""
    
    def __post_init__(self):
        # Normalisiere Soll/Haben
        self.soll_haben = self.soll_haben.upper()
        if self.soll_haben not in ("S", "H"):
            raise ValueError(f"soll_haben muss 'S' oder 'H' sein, nicht '{self.soll_haben}'")
        
        # Konvertiere Umsatz zu Decimal
        if isinstance(self.umsatz, (int, float)):
            self.umsatz = Decimal(str(self.umsatz))
        
        # Normalisiere Datum
        self.datum = self._normalize_datum(self.datum)
    
    def _normalize_datum(self, datum: str) -> str:
        """Konvertiert verschiedene Datumsformate zu TTMMJJ"""
        # Bereits im richtigen Format?
        if len(datum) == 6 and datum.isdigit():
            return datum
        
        # Versuche verschiedene Formate
        formats = [
            "%d.%m.%Y",  # 15.02.2024
            "%d.%m.%y",  # 15.02.24
            "%Y-%m-%d",  # 2024-02-15
            "%d/%m/%Y",  # 15/02/2024
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(datum, fmt)
                return dt.strftime("%d%m%y")  # TTMMJJ
            except ValueError:
                continue
        
        # Fallback zu dateutil
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
            "Buchungstext": self.buchungstext[:30] if self.buchungstext else "",  # Max 30 Zeichen
            "Belegfeld 1": self.belegnummer[:12] if self.belegnummer else "",  # Max 12 Zeichen
        }
    
    def _format_umsatz(self) -> str:
        """Formatiert Umsatz im deutschen Format (Komma als Dezimalzeichen)"""
        # DATEV verwendet Komma als Dezimalzeichen
        formatted = f"{self.umsatz:.2f}".replace(".", ",")
        return formatted


class DATEVExporter:
    """Exportiert Buchungsdaten im DATEV-CSV-Format"""
    
    # DATEV CSV-Header (Standard)
    CSV_HEADER = [
        "Datum",
        "Konto",
        "Gegenkonto",
        "BU-Schlüssel",
        "Umsatz (ohne Soll/Haben-Kz)",
        "Soll/Haben-Kennzeichen",
        "Währung",
        "Buchungstext",
        "Belegfeld 1",
    ]
    
    # Kontenrahmen SKR03 (Auszug - wichtigste Konten)
    SKR03_KONTEN = {
        # Banken
        1200: "Bank",
        1210: "Bank 2",
        1800: "Kasse",
        # Forderungen (Kunden)
        1400: "Forderungen aus Lieferungen und Leistungen",
        1401: "Forderungen aus Lieferungen und Leistungen (verbundene Unternehmen)",
        # Verbindlichkeiten (Kreditoren)
        1600: "Verbindlichkeiten aus Lieferungen und Leistungen",
        1601: "Verbindlichkeiten aus Lieferungen und Leistungen (verbundene Unternehmen)",
        # Erlöse
        8300: "Steuerfreie Umsätze §4 Nr. 1-7 UStG",
        8400: "Umsatzsteuerpflichtige Erlöse 19%",
        8300: "Umsatzsteuerpflichtige Erlöse 7%",
        # Aufwendungen
        7000: "Aufwendungen für Roh-, Hilfs- und Betriebsstoffe",
        7020: "Bezogene Waren",
        7200: "Miete",
        7300: "Strom",
        7400: "Telefon, Internet",
        7500: "Büromaterial",
        7600: "Rechts- und Beratungskosten",
        7700: "Werbung",
        7800: "Reisekosten",
        # Steuern
        1571: "Umsatzsteuer 19%",
        1572: "Umsatzsteuer 7%",
        1576: "Vorsteuer 19%",
        1577: "Vorsteuer 7%",
        1600: "Finanzamt",
        # Sonstiges
        9000: "Privatentnahmen",
        9010: "Privatenlagen",
        9900: "Gewinn-/Verlustvortrag",
    }
    
    # Kontenrahmen SKR04 (Auszug)
    SKR04_KONTEN = {
        # Banken
        1800: "Bank",
        1880: "Kasse",
        # Forderungen
        1200: "Forderungen aus Lieferungen und Leistungen",
        # Verbindlichkeiten
        1600: "Verbindlichkeiten aus Lieferungen und Leistungen",
        # Erlöse
        4400: "Umsatzsteuerpflichtige Erlöse 19%",
        4310: "Umsatzsteuerpflichtige Erlöse 7%",
        4120: "Steuerfreie Umsätze §4 UStG",
        # Aufwendungen
        6000: "Aufwendungen für Waren",
        6300: "Miete",
        6400: "Strom",
        6500: "Telefon, Internet",
        6600: "Büromaterial",
        6700: "Rechts- und Beratungskosten",
        6800: "Werbung",
        6900: "Reisekosten",
        # Steuern
        3801: "Umsatzsteuer 19%",
        3802: "Umsatzsteuer 7%",
        1401: "Vorsteuer 19%",
        1402: "Vorsteuer 7%",
    }
    
    # Gültige BU-Schlüssel
    BU_SCHLUESSEL = {
        "": "Kein BU-Schlüssel",
        "1": "Innergemeinschaftliche Lieferung/Leistung",
        "2": "Innergemeinschaftlicher Erwerb",
        "3": "Einfuhr (Einfuhrabgaben)",
        "4": "Erlös für steuerpflichtige Lieferungen/Leistungen",
        "5": "Erlös für steuerfreie Lieferungen/Leistungen",
        "9": "Steuerfreie Inland-Leistungen §4 UStG",
        "10": "Steuerpflichtige Inland-Leistungen 19%",
        "11": "Steuerpflichtige Inland-Leistungen 7%",
        "20": "Innergemeinschaftliche Lieferungen §4 Abs. 1b UStG",
        "25": "Innergemeinschaftliche Lieferungen §4 Abs. 1b i.V.m. §6 UStG",
    }
    
    def __init__(self, kontenrahmen: str = "SKR03"):
        """
        Args:
            kontenrahmen: "SKR03" oder "SKR04"
        """
        if kontenrahmen not in ("SKR03", "SKR04"):
            raise ValueError(f"Ungültiger Kontenrahmen: {kontenrahmen}")
        
        self.kontenrahmen = kontenrahmen
        self.konten = self.SKR03_KONTEN if kontenrahmen == "SKR03" else self.SKR04_KONTEN
        self.buchungen: List[Buchungssatz] = []
    
    def validate_konto(self, konto: int) -> bool:
        """Prüft ob Konto im gültigen Bereich liegt"""
        return 1000 <= konto <= 99999
    
    def add_buchung(self, buchung: Buchungssatz) -> None:
        """Fügt einen Buchungssatz hinzu"""
        # Validierung
        if not self.validate_konto(buchung.konto):
            raise ValueError(f"Ungültiges Konto: {buchung.konto}")
        if not self.validate_konto(buchung.gegenkonto):
            raise ValueError(f"Ungültiges Gegenkonto: {buchung.gegenkonto}")
        if buchung.konto == buchung.gegenkonto:
            raise ValueError(f"Konto und Gegenkonto dürfen nicht identisch sein: {buchung.konto}")
        
        self.buchungen.append(buchung)
    
    def add_rechnung(
        self,
        datum: str,
        brutto: Union[Decimal, float],
        ust_satz: int,
        konto: int,
        gegenkonto: int,
        text: str = "",
        belegnummer: str = "",
        ist_eingangsrechnung: bool = True
    ) -> None:
        """
        Erzeugt automatisch Buchungen für eine Rechnung mit USt
        
        Bei Eingangsrechnung (ist_eingangsrechnung=True):
        - Konto: Aufwand (z.B. 7000)
        - Gegenkonto: Verbindlichkeit (z.B. 1600)
        
        Bei Ausgangsrechnung (ist_eingangsrechnung=False):
        - Konto: Erlös (z.B. 8400)
        - Gegenkonto: Forderung (z.B. 1400)
        """
        brutto_dec = Decimal(str(brutto))
        ust_faktor = Decimal(str(ust_satz)) / Decimal("100")
        netto = (brutto_dec / (Decimal("1") + ust_faktor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        ust_betrag = (brutto_dec - netto).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        # Vorsteuer/Erwerbssteuer-Konto basierend auf Kontenrahmen
        if self.kontenrahmen == "SKR03":
            ust_konto = 1576 if ust_satz == 19 else 1577
        else:  # SKR04
            ust_konto = 1401 if ust_satz == 19 else 1402
        
        if ist_eingangsrechnung:
            # Eingangsrechnung: Aufwand + Vorsteuer an Kreditor
            # 1. Aufwand (Soll) an Kreditor (Haben)
            self.add_buchung(Buchungssatz(
                datum=datum,
                konto=konto,
                gegenkonto=gegenkonto,
                bu_schluessel="",
                umsatz=netto,
                soll_haben="S",
                buchungstext=text[:25],
                belegnummer=belegnummer
            ))
            # 2. Vorsteuer (Soll) an Kreditor (Haben)
            self.add_buchung(Buchungssatz(
                datum=datum,
                konto=ust_konto,
                gegenkonto=gegenkonto,
                bu_schluessel="",
                umsatz=ust_betrag,
                soll_haben="S",
                buchungstext=f"VSt {belegnummer}"[:25],
                belegnummer=belegnummer
            ))
        else:
            # Ausgangsrechnung: Forderung an Erlös + USt
            # 1. Forderung (Soll) an Erlös (Haben)
            self.add_buchung(Buchungssatz(
                datum=datum,
                konto=gegenkonto,
                gegenkonto=konto,
                bu_schluessel="",
                umsatz=netto,
                soll_haben="S",
                buchungstext=text[:25],
                belegnummer=belegnummer
            ))
            # 2. Forderung (Soll) an USt (Haben)
            self.add_buchung(Buchungssatz(
                datum=datum,
                konto=gegenkonto,
                gegenkonto=ust_konto,
                bu_schluessel="",
                umsatz=ust_betrag,
                soll_haben="S",
                buchungstext=f"USt {belegnummer}"[:25],
                belegnummer=belegnummer
            ))
    
    def export(self, output_path: str, encoding: str = "utf-8-sig") -> None:
        """
        Exportiert Buchungen als DATEV-CSV
        
        Args:
            output_path: Pfad zur Ausgabe-CSV
            encoding: UTF-8 mit BOM für Excel-Kompatibilität
        """
        path = Path(output_path)
        
        with open(path, 'w', newline='', encoding=encoding) as f:
            writer = csv.DictWriter(f, fieldnames=self.CSV_HEADER, delimiter=';', quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            
            for buchung in self.buchungen:
                writer.writerow(buchung.to_datev_row())
        
        print(f"✅ {len(self.buchungen)} Buchungen exportiert nach: {path}")
    
    def to_json(self) -> str:
        """Exportiert Buchungen als JSON"""
        data = [asdict(b) for b in self.buchungen]
        # Konvertiere Decimal zu float für JSON
        for item in data:
            if isinstance(item['umsatz'], Decimal):
                item['umsatz'] = float(item['umsatz'])
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def load_json(self, json_path: str) -> None:
        """Lädt Buchungen aus JSON-Datei"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for item in data:
            buchung = Buchungssatz(**item)
            self.add_buchung(buchung)
    
    def get_stats(self) -> Dict[str, Any]:
        """Gibt Statistiken zu den Buchungen zurück"""
        if not self.buchungen:
            return {"anzahl": 0, "summe_soll": 0, "summe_haben": 0}
        
        summe_soll = sum(b.umsatz for b in self.buchungen if b.soll_haben == "S")
        summe_haben = sum(b.umsatz for b in self.buchungen if b.soll_haben == "H")
        
        return {
            "anzahl": len(self.buchungen),
            "summe_soll": float(summe_soll),
            "summe_haben": float(summe_haben),
            "differenz": float(summe_soll - summe_haben),
            "kontenrahmen": self.kontenrahmen,
        }


def validate_datev_csv(csv_path: str) -> List[str]:
    """Validiert eine DATEV-CSV-Datei"""
    errors = []
    
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        
        for i, row in enumerate(reader, start=2):
            # Datum prüfen
            datum = row.get('Datum', '')
            if len(datum) != 6 or not datum.isdigit():
                errors.append(f"Zeile {i}: Ungültiges Datum '{datum}' (erwartet: TTMMJJ)")
            
            # Konto prüfen
            try:
                konto = int(row.get('Konto', 0))
                if not (1000 <= konto <= 99999):
                    errors.append(f"Zeile {i}: Konto {konto} außerhalb gültigen Bereichs")
            except ValueError:
                errors.append(f"Zeile {i}: Ungültiges Konto '{row.get('Konto')}'")
            
            # Gegenkonto prüfen
            try:
                gegenkonto = int(row.get('Gegenkonto', 0))
                if konto == gegenkonto:
                    errors.append(f"Zeile {i}: Konto und Gegenkonto sind identisch")
            except ValueError:
                errors.append(f"Zeile {i}: Ungültiges Gegenkonto '{row.get('Gegenkonto')}'")
            
            # Soll/Haben prüfen
            sh = row.get('Soll/Haben-Kennzeichen', '').upper()
            if sh not in ('S', 'H'):
                errors.append(f"Zeile {i}: Ungültiges Soll/Haben-Kennzeichen '{sh}'")
    
    return errors


def generate_example():
    """Generiert ein Beispiel-DATEV-CSV"""
    exporter = DATEVExporter(kontenrahmen="SKR03")
    
    # Beispiel-Buchungen
    exporter.add_buchung(Buchungssatz(
        datum="150224",
        konto=8400,
        gegenkonto=1400,
        bu_schluessel="",
        umsatz=Decimal("1000.00"),
        soll_haben="H",
        buchungstext="Verkauf Produkt A",
        belegnummer="RE-001"
    ))
    
    exporter.add_rechnung(
        datum="200224",
        brutto=119.00,
        ust_satz=19,
        konto=7020,
        gegenkonto=1600,
        text="Einkauf Büromaterial",
        belegnummer="ER-042",
        ist_eingangsrechnung=True
    )
    
    exporter.add_buchung(Buchungssatz(
        datum="280224",
        konto=1600,
        gegenkonto=1200,
        bu_schluessel="",
        umsatz=Decimal("119.00"),
        soll_haben="S",
        buchungstext="Zahlung Lieferant",
        belegnummer="UE-001"
    ))
    
    return exporter


def main():
    parser = argparse.ArgumentParser(description='DATEV-CSV-Export')
    parser.add_argument('--input', '-i', help='JSON-Input-Datei')
    parser.add_argument('--output', '-o', help='CSV-Output-Datei')
    parser.add_argument('--kr', choices=['SKR03', 'SKR04'], default='SKR03', help='Kontenrahmen')
    parser.add_argument('--validate', help='CSV-Datei validieren')
    parser.add_argument('--example', action='store_true', help='Beispiel-CSV generieren')
    parser.add_argument('--stats', action='store_true', help='Statistiken anzeigen')
    
    args = parser.parse_args()
    
    if args.validate:
        errors = validate_datev_csv(args.validate)
        if errors:
            print(f"❌ {len(errors)} Fehler gefunden:")
            for err in errors[:10]:  # Max 10 anzeigen
                print(f"   - {err}")
            if len(errors) > 10:
                print(f"   ... und {len(errors) - 10} weitere")
        else:
            print("✅ CSV ist DATEV-konform")
    
    elif args.example:
        exporter = generate_example()
        if args.output:
            exporter.export(args.output)
            if args.stats:
                print("\n📊 Statistiken:")
                for key, val in exporter.get_stats().items():
                    print(f"   {key}: {val}")
        else:
            # CSV auf stdout ausgeben
            import io
            output = io.StringIO()
            with open('/dev/stdout', 'w', newline='') if hasattr(__import__('os'), 'devnull') else output as f:
                pass  # Placeholder
            # Export zu stdout nicht direkt unterstützt, daher temp
            print(exporter.to_json())
    
    elif args.input and args.output:
        exporter = DATEVExporter(kontenrahmen=args.kr)
        exporter.load_json(args.input)
        exporter.export(args.output)
        
        if args.stats:
            print("\n📊 Statistiken:")
            for key, val in exporter.get_stats().items():
                print(f"   {key}: {val}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
