"""
DATEV-Format Validator
Validiert DATEV-kompatible CSV/TXT Dateien für Buchhaltungsexporte

Fokus: German Accounting, DATEV, Tax Compliance
"""

import csv
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from io import StringIO


@dataclass
class DATEVValidationResult:
    """Ergebnis der DATEV-Validierung"""
    gueltig: bool
    format: str  # 'BUCHUNGSSTAPEL', 'DEBITOREN', 'KREDITOREN'
    zeilen_gesamt: int
    zeilen_fehlerhaft: int
    fehler: List[Dict]
    warnungen: List[str]


class DATEVValidator:
    """
    Validator für DATEV-Buchhaltungsformate
    
    Unterstützt:
    - Buchungsstapel (Standardbuchungen)
    - Debitoren-Stammdaten
    - Kreditoren-Stammdaten
    """
    
    # DATEV Standard-Felddefinitionen
    BUCHUNGSSTAPEL_HEADER = [
        'Umsatz (ohne Soll/Haben-Kz)',
        'Soll/Haben-Kennzeichen',
        'WKZ Umsatz',
        'Kurs',
        'Basisumsatz',
        'WKZ Basisumsatz',
        'Konto',
        'Gegenkonto (ohne BU-Schlüssel)',
        'BU-Schlüssel',
        'Belegdatum',
        'Belegfeld 1',
        'Belegfeld 2',
        'Skonto',
        'Buchungstext',
        'Postensperre',
        'Diverse Adressnummer',
        'Geschäftspartnerbank',
        'Sachverhalt',
        'Zinssperre',
        'Beleglink'
    ]
    
    # Gültige Soll/Haben-Kennzeichen
    SOLL_HABEN_KZ = ['S', 'H']
    
    # Gültige Währungscodes
    WKZ = ['EUR', 'USD', 'CHF', 'GBP']
    
    # DATEV Datumsformat: TTMMJJJJ
    DATUM_PATTERN = r'^\d{8}$'
    
    # Konto-Muster (max. 9 Stellen)
    KONTO_PATTERN = r'^\d{1,9}$'
    
    def __init__(self):
        self.fehler = []
        self.warnungen = []
    
    def validate_csv(self, csv_content: str, delimiter: str = ';') -> DATEVValidationResult:
        """
        Validiert DATEV-CSV-Datei
        
        Args:
            csv_content: CSV-String
            delimiter: Trennzeichen (meist ';')
        """
        self.fehler = []
        self.warnungen = []
        
        try:
            reader = csv.DictReader(StringIO(csv_content), delimiter=delimiter)
            
            if not reader.fieldnames:
                return DATEVValidationResult(
                    gueltig=False,
                    format='UNKNOWN',
                    zeilen_gesamt=0,
                    zeilen_fehlerhaft=0,
                    fehler=[{'zeile': 0, 'fehler': ['Keine Header gefunden']}],
                    warnungen=[]
                )
            
            # Erkenne Format anhand der Header
            datev_format = self._detect_format(reader.fieldnames)
            
            # Validiere Zeilen
            zeilen_nummer = 1
            fehlerhafte_zeilen = 0
            
            for row in reader:
                zeilen_fehler = self._validate_buchungszeile(row, zeilen_nummer)
                if zeilen_fehler:
                    self.fehler.extend(zeilen_fehler)
                    fehlerhafte_zeilen += 1
                zeilen_nummer += 1
            
            return DATEVValidationResult(
                gueltig=len(self.fehler) == 0,
                format=datev_format,
                zeilen_gesamt=zeilen_nummer - 1,
                zeilen_fehlerhaft=fehlerhafte_zeilen,
                fehler=self.fehler,
                warnungen=self.warnungen
            )
            
        except csv.Error as e:
            return DATEVValidationResult(
                gueltig=False,
                format='ERROR',
                zeilen_gesamt=0,
                zeilen_fehlerhaft=0,
                fehler=[{'zeile': 0, 'fehler': [f'CSV Parse-Fehler: {e}']}],
                warnungen=[]
            )
    
    def _detect_format(self, headers: List[str]) -> str:
        """Erkennt DATEV-Format anhand der Header"""
        header_set = set(headers)
        buchungsstapel_set = set(self.BUCHUNGSSTAPEL_HEADER)
        
        # Prüfe Übereinstimmung mit Buchungsstapel (mindestens 5 gemeinsame Header)
        gemeinsam = len(header_set & buchungsstapel_set)
        if gemeinsam >= 5:
            return 'BUCHUNGSSTAPEL'
        
        # Prüfe auf charakteristische Felder
        if 'Umsatz (ohne Soll/Haben-Kz)' in header_set or 'Soll/Haben-Kennzeichen' in header_set:
            return 'BUCHUNGSSTAPEL'
        
        # Weitere Formate erkennen
        if any('Debitoren' in h for h in headers):
            return 'DEBITOREN'
        if any('Kreditoren' in h for h in headers):
            return 'KREDITOREN'
        
        self.warnungen.append(f"Unbekanntes Format, erkannte Header: {list(headers)[:5]}...")
        return 'UNKNOWN'
    
    def _validate_buchungszeile(self, row: Dict, zeilen_nummer: int) -> List[Dict]:
        """Validiert eine einzelne Buchungszeile"""
        fehler = []
        
        # Pflichtfelder prüfen
        pflichtfelder = [
            ('Umsatz (ohne Soll/Haben-Kz)', 'Umsatz'),
            ('Soll/Haben-Kennzeichen', 'Soll/Haben-Kz'),
            ('Konto', 'Konto'),
            ('Gegenkonto (ohne BU-Schlüssel)', 'Gegenkonto'),
            ('Belegdatum', 'Belegdatum')
        ]
        
        for header_feld, fehler_name in pflichtfelder:
            wert = row.get(header_feld, '').strip()
            if not wert:
                fehler.append({
                    'zeile': zeilen_nummer,
                    'feld': fehler_name,
                    'fehler': f'Pflichtfeld fehlt: {fehler_name}'
                })
        
        # Soll/Haben-Kennzeichen
        sh_kz = row.get('Soll/Haben-Kennzeichen', '').strip().upper()
        if sh_kz and sh_kz not in self.SOLL_HABEN_KZ:
            fehler.append({
                'zeile': zeilen_nummer,
                'feld': 'Soll/Haben-Kz',
                'fehler': f'Ungültiges Soll/Haben-Kennzeichen: {sh_kz} (erlaubt: S, H)'
            })
        
        # Umsatz format prüfen
        umsatz = row.get('Umsatz (ohne Soll/Haben-Kz)', '').strip()
        if umsatz:
            umsatz_clean = umsatz.replace(',', '.').replace('.', '')
            try:
                float(umsatz_clean)
            except ValueError:
                fehler.append({
                    'zeile': zeilen_nummer,
                    'feld': 'Umsatz',
                    'fehler': f'Ungültiges Umsatz-Format: {umsatz}'
                })
        
        # Belegdatum prüfen (TTMMJJJJ)
        datum = row.get('Belegdatum', '').strip()
        if datum and not re.match(self.DATUM_PATTERN, datum):
            fehler.append({
                'zeile': zeilen_nummer,
                'feld': 'Belegdatum',
                'fehler': f'Ungültiges Datumsformat: {datum} (erwartet: TTMMJJJJ)'
            })
        
        # Konto prüfen
        konto = row.get('Konto', '').strip()
        if konto and not re.match(self.KONTO_PATTERN, konto):
            fehler.append({
                'zeile': zeilen_nummer,
                'feld': 'Konto',
                'fehler': f'Ungültiges Konto: {konto} (max. 9 Stellen)'
            })
        
        # Gegenkonto prüfen
        gegenkonto = row.get('Gegenkonto (ohne BU-Schlüssel)', '').strip()
        if gegenkonto and not re.match(self.KONTO_PATTERN, gegenkonto):
            fehler.append({
                'zeile': zeilen_nummer,
                'feld': 'Gegenkonto',
                'fehler': f'Ungültiges Gegenkonto: {gegenkonto}'
            })
        
        return fehler
    
    def validate_konto(self, kontonummer: str) -> Dict:
        """Validiert eine einzelne Kontonummer"""
        if not kontonummer:
            return {'gueltig': False, 'fehler': 'Kontonummer leer'}
        
        if not re.match(self.KONTO_PATTERN, kontonummer):
            return {'gueltig': False, 'fehler': 'Kontonummer ungültig (max. 9 Stellen)'}
        
        # DATEV Standardkontenrahmen (SKR03/SKR04) Hinweise
        konto_nr = int(kontonummer)
        
        hinweis = None
        if 1000 <= konto_nr <= 6999:
            hinweis = 'Bestandskonto (Aktiv/Passiv)'
        elif 8000 <= konto_nr <= 8999:
            hinweis = 'Erfolgskonto (Aufwand/Ertrag)'
        elif 9000 <= konto_nr <= 9999:
            hinweis = 'Abschlusskonto'
        
        return {
            'gueltig': True,
            'kontonummer': kontonummer,
            'hinweis': hinweis
        }
    
    def generate_sample_csv(self) -> str:
        """Generiert Beispiel-DATEV-CSV"""
        output = StringIO()
        writer = csv.DictWriter(
            output, 
            fieldnames=self.BUCHUNGSSTAPEL_HEADER,
            delimiter=';',
            lineterminator='\n'
        )
        writer.writeheader()
        
        # Beispiel-Buchung
        writer.writerow({
            'Umsatz (ohne Soll/Haben-Kz)': '1000,00',
            'Soll/Haben-Kennzeichen': 'S',
            'WKZ Umsatz': 'EUR',
            'Kurs': '',
            'Basisumsatz': '',
            'WKZ Basisumsatz': '',
            'Konto': '8400',
            'Gegenkonto (ohne BU-Schlüssel)': '1200',
            'BU-Schlüssel': '',
            'Belegdatum': '24022025',
            'Belegfeld 1': 'RE-2025-001',
            'Belegfeld 2': '',
            'Skonto': '',
            'Buchungstext': 'Erlöse aus Lieferungen',
            'Postensperre': '',
            'Diverse Adressnummer': '',
            'Geschäftspartnerbank': '',
            'Sachverhalt': '',
            'Zinssperre': '',
            'Beleglink': ''
        })
        
        return output.getvalue()


def validate_datev(csv_content: str, delimiter: str = ';') -> Dict:
    """
    Schnell-Validierung einer DATEV-CSV
    
    Usage:
        with open('export.csv', 'r') as f:
            result = validate_datev(f.read())
        
        print(result['gueltig'])
        print(result['fehler'])
    """
    validator = DATEVValidator()
    result = validator.validate_csv(csv_content, delimiter)
    
    return {
        'gueltig': result.gueltig,
        'format': result.format,
        'zeilen_gesamt': result.zeilen_gesamt,
        'zeilen_fehlerhaft': result.zeilen_fehlerhaft,
        'fehler': result.fehler,
        'warnungen': result.warnungen
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python datev_validator.py <command> [args]")
        print("\nCommands:")
        print("  validate <file.csv>    - CSV-Datei validieren")
        print("  validate-konto <nr>   - Einzelnes Konto validieren")
        print("  sample                 - Beispiel-CSV generieren")
        print("\nBeispiele:")
        print("  python datev_validator.py validate buchungen.csv")
        print("  python datev_validator.py validate-konto 8400")
        sys.exit(1)
    
    command = sys.argv[1]
    validator = DATEVValidator()
    
    if command == "validate":
        if len(sys.argv) < 3:
            print("❌ Fehler: CSV-Datei angeben")
            sys.exit(1)
        
        filepath = sys.argv[2]
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            
            result = validator.validate_csv(csv_content)
            
            print(f"🔍 DATEV-Validierung: {filepath}")
            print("-" * 60)
            print(f"Format: {result.format}")
            print(f"Zeilen gesamt: {result.zeilen_gesamt}")
            print(f"Zeilen fehlerhaft: {result.zeilen_fehlerhaft}")
            print(f"\nGültig: {'✅ Ja' if result.gueltig else '❌ Nein'}")
            
            if result.warnungen:
                print(f"\n⚠️  Warnungen:")
                for warn in result.warnungen:
                    print(f"   - {warn}")
            
            if result.fehler:
                print(f"\n❌ Fehler ({len(result.fehler)}):")
                for fehler in result.fehler[:10]:  # Max 10 anzeigen
                    print(f"   Zeile {fehler['zeile']}: {fehler['fehler']}")
                if len(result.fehler) > 10:
                    print(f"   ... und {len(result.fehler) - 10} weitere")
                    
        except FileNotFoundError:
            print(f"❌ Datei nicht gefunden: {filepath}")
    
    elif command == "validate-konto":
        if len(sys.argv) < 3:
            print("❌ Fehler: Kontonummer angeben")
            sys.exit(1)
        
        konto = sys.argv[2]
        result = validator.validate_konto(konto)
        
        print(f"🔍 Konto-Validierung: {konto}")
        print("-" * 50)
        print(f"Gültig: {'✅ Ja' if result['gueltig'] else '❌ Nein'}")
        
        if result.get('hinweis'):
            print(f"Hinweis: {result['hinweis']}")
        
        if result.get('fehler'):
            print(f"Fehler: {result['fehler']}")
    
    elif command == "sample":
        sample = validator.generate_sample_csv()
        print("Beispiel DATEV-CSV (Buchungsstapel):")
        print("-" * 60)
        print(sample)
    
    else:
        print(f"❌ Unbekannter Befehl: {command}")
