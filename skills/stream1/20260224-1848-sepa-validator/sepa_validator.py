"""
SEPA IBAN/BIC Validator + Generator
Validiert und generiert IBAN/BIC für SEPA-Zahlungen

Fokus: German E-Commerce, Banking, SEPA
"""

import re
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class IBANValidationResult:
    """Ergebnis der IBAN-Validierung"""
    gueltig: bool
    iban: str
    land: str
    bankleitzahl: Optional[str]
    kontonummer: Optional[str]
    bic: Optional[str]
    sepa_faehig: bool
    fehler: List[str]


class SEPAValidator:
    """
    Validator und Generator für SEPA-Zahlungsdaten
    
    Unterstützt:
    - IBAN-Validierung (alle EU-Länder)
    - BIC-Validierung
    - Deutsche Bankdaten (BLZ/Konto → IBAN)
    - Prüfziffer-Berechnung (Modulo 97-10)
    """
    
    # IBAN-Längen nach Land
    IBAN_LENGTHS = {
        'DE': 22, 'AT': 20, 'CH': 21, 'NL': 18, 'BE': 16,
        'FR': 27, 'IT': 27, 'ES': 24, 'PT': 25, 'PL': 28,
        'GB': 22, 'IE': 22, 'DK': 18, 'FI': 18, 'SE': 24,
        'NO': 15, 'LU': 20, 'CZ': 24, 'HU': 28, 'SK': 24,
        'SI': 19, 'HR': 21, 'BG': 22, 'RO': 24, 'EE': 20,
        'LV': 21, 'LT': 20, 'GR': 27, 'CY': 28, 'MT': 31,
        'IS': 26, 'LI': 21, 'MC': 27, 'SM': 27, 'VA': 22
    }
    
    # Ländernamen
    COUNTRY_NAMES = {
        'DE': 'Deutschland', 'AT': 'Österreich', 'CH': 'Schweiz',
        'NL': 'Niederlande', 'BE': 'Belgien', 'FR': 'Frankreich',
        'IT': 'Italien', 'ES': 'Spanien', 'PT': 'Portugal',
        'PL': 'Polen', 'GB': 'Großbritannien', 'IE': 'Irland',
        'DK': 'Dänemark', 'FI': 'Finnland', 'SE': 'Schweden',
        'NO': 'Norwegen', 'LU': 'Luxemburg', 'CZ': 'Tschechien',
        'HU': 'Ungarn', 'SK': 'Slowakei', 'SI': 'Slowenien',
        'HR': 'Kroatien', 'BG': 'Bulgarien', 'RO': 'Rumänien',
        'EE': 'Estland', 'LV': 'Lettland', 'LT': 'Litauen',
        'GR': 'Griechenland', 'CY': 'Zypern', 'MT': 'Malta',
        'IS': 'Island', 'LI': 'Liechtenstein', 'MC': 'Monaco',
        'SM': 'San Marino', 'VA': 'Vatikanstadt'
    }
    
    def __init__(self):
        self.fehler = []
    
    def format_iban(self, iban: str) -> str:
        """Formatiert IBAN zu standardisiertem Format"""
        return re.sub(r'[^A-Za-z0-9]', '', iban).upper()
    
    def format_bic(self, bic: str) -> str:
        """Formatiert BIC zu standardisiertem Format"""
        return re.sub(r'[^A-Za-z0-9]', '', bic).upper()
    
    def validate_iban(self, iban: str) -> IBANValidationResult:
        """
        Validiert eine IBAN mit Prüfziffer
        
        Algorithmus (Modulo 97-10):
        1. IBAN: DE00 1234 5678 9012 3456 78
        2. Verschiebe erstes 4 Zeichen ans Ende: 123456789012345678 DE00
        3. Ersetze Buchstaben durch Zahlen (A=10, B=11, ...): ... 131400
        4. Modulo 97: Wenn Rest = 1 → gültig
        """
        self.fehler = []
        formatted = self.format_iban(iban)
        
        # Länge prüfen
        if len(formatted) < 5:
            return IBANValidationResult(
                gueltig=False, iban=formatted, land='',
                bankleitzahl=None, kontonummer=None, bic=None,
                sepa_faehig=False, fehler=['IBAN zu kurz']
            )
        
        # Land extrahieren
        country = formatted[:2]
        
        if country not in self.IBAN_LENGTHS:
            return IBANValidationResult(
                gueltig=False, iban=formatted, land=country,
                bankleitzahl=None, kontonummer=None, bic=None,
                sepa_faehig=False, fehler=[f'Ungültiger Ländercode: {country}']
            )
        
        # Länderspezifische Länge prüfen
        expected_length = self.IBAN_LENGTHS[country]
        if len(formatted) != expected_length:
            return IBANValidationResult(
                gueltig=False, iban=formatted, land=country,
                bankleitzahl=None, kontonummer=None, bic=None,
                sepa_faehig=False,
                fehler=[f'Falsche Länge für {country}: {len(formatted)} (erwartet: {expected_length})']
            )
        
        # Prüfziffer validieren
        pruefziffer_ok = self._validate_iban_checksum(formatted)
        
        if not pruefziffer_ok:
            self.fehler.append('Prüfziffer ungültig')
        
        # Deutsche Bankdaten extrahieren
        blz, konto = None, None
        if country == 'DE':
            blz = formatted[4:12]
            konto = formatted[12:22]
        
        return IBANValidationResult(
            gueltig=pruefziffer_ok,
            iban=formatted,
            land=self.COUNTRY_NAMES.get(country, country),
            bankleitzahl=blz,
            kontonummer=konto,
            bic=None,  # Würde BIC-Lookup erfordern
            sepa_faehig=country in self.IBAN_LENGTHS,
            fehler=self.fehler
        )
    
    def _validate_iban_checksum(self, iban: str) -> bool:
        """Prüft die IBAN-Prüfziffer (Modulo 97-10)"""
        try:
            # Verschiebe erstes 4 Zeichen ans Ende
            rearranged = iban[4:] + iban[:4]
            
            # Konvertiere zu numerischer Darstellung
            numeric = ''
            for char in rearranged:
                if char.isalpha():
                    numeric += str(ord(char) - ord('A') + 10)
                else:
                    numeric += char
            
            # Modulo 97
            return int(numeric) % 97 == 1
            
        except (ValueError, OverflowError):
            return False
    
    def validate_bic(self, bic: str) -> Dict:
        """
        Validiert einen BIC (SWIFT-Code)
        
        Format: BKKLDEFFXXX oder BKKLDEFF
        - 4 Stellen: Bankcode
        - 2 Stellen: Ländercode
        - 2 Stellen: Ortscode
        - 3 Stellen: Filiale (optional, default: XXX)
        """
        formatted = self.format_bic(bic)
        fehler = []
        
        # Länge prüfen
        if len(formatted) not in [8, 11]:
            fehler.append(f'BIC muss 8 oder 11 Zeichen haben (aktuell: {len(formatted)})')
        
        # Bankcode (erste 4) - Buchstaben
        if len(formatted) >= 4 and not formatted[:4].isalpha():
            fehler.append('Bankcode muss aus Buchstaben bestehen')
        
        # Ländercode (Stelle 5-6)
        if len(formatted) >= 6:
            country = formatted[4:6]
            if country not in self.IBAN_LENGTHS:
                fehler.append(f'Ungültiger Ländercode im BIC: {country}')
        
        # Ortscode (Stelle 7-8) - alphanumerisch
        if len(formatted) >= 8 and not formatted[6:8].isalnum():
            fehler.append('Ortscode ungültig')
        
        return {
            'gueltig': len(fehler) == 0,
            'bic': formatted,
            'laendercode': formatted[4:6] if len(formatted) >= 6 else None,
            'bankcode': formatted[:4] if len(formatted) >= 4 else None,
            'filiale': formatted[8:11] if len(formatted) == 11 else 'XXX',
            'fehler': fehler
        }
    
    def german_to_iban(self, blz: str, konto: str) -> Dict:
        """
        Erstellt deutsche IBAN aus BLZ und Kontonummer
        
        Algorithmus:
        1. BBAN = BLZ (8) + Konto (10, mit führenden Nullen)
        2. Prüfziffer berechnen
        3. IBAN = DE + Prüfziffer + BBAN
        """
        fehler = []
        
        # BLZ validieren
        blz_clean = re.sub(r'\D', '', blz)
        if len(blz_clean) != 8:
            fehler.append(f'BLZ muss 8 Ziffern haben (aktuell: {len(blz_clean)})')
        
        # Konto validieren
        konto_clean = re.sub(r'\D', '', konto)
        if len(konto_clean) > 10:
            fehler.append(f'Kontonummer zu lang (max. 10 Ziffern)')
        
        if fehler:
            return {
                'gueltig': False,
                'fehler': fehler,
                'iban': None
            }
        
        # BBAN erstellen
        bban = blz_clean + konto_clean.zfill(10)
        
        # Prüfziffer berechnen
        pruefziffer = self._calculate_iban_checksum('DE', bban)
        
        # IBAN zusammensetzen
        iban = f'DE{pruefziffer:02d}{bban}'
        
        return {
            'gueltig': True,
            'iban': iban,
            'blz': blz_clean,
            'kontonummer': konto_clean,
            'pruefziffer': pruefziffer,
            'formatted': self.format_iban_readable(iban)
        }
    
    def _calculate_iban_checksum(self, country: str, bban: str) -> int:
        """Berechnet IBAN-Prüfziffer"""
        # Temporäre IBAN mit 00
        temp = bban + country + '00'
        
        # Konvertiere zu numerisch
        numeric = ''
        for char in temp:
            if char.isalpha():
                numeric += str(ord(char) - ord('A') + 10)
            else:
                numeric += char
        
        # Berechne Prüfziffer
        remainder = int(numeric) % 97
        pruefziffer = 98 - remainder
        
        return pruefziffer
    
    def format_iban_readable(self, iban: str) -> str:
        """Formatiert IBAN lesbar (DE00 1234 5678 ...)"""
        formatted = self.format_iban(iban)
        # 4er-Gruppen
        return ' '.join(formatted[i:i+4] for i in range(0, len(formatted), 4))
    
    def is_sepa_country(self, country_code: str) -> bool:
        """Prüft ob Land im SEPA-Raum"""
        return country_code.upper() in self.IBAN_LENGTHS


def validate_iban(iban: str) -> Dict:
    """
    Schnell-Validierung einer IBAN
    
    Usage:
        result = validate_iban('DE89370400440532013000')
        print(result['gueltig'])
        print(result['land'])
    """
    validator = SEPAValidator()
    result = validator.validate_iban(iban)
    
    return {
        'gueltig': result.gueltig,
        'iban': result.iban,
        'land': result.land,
        'bankleitzahl': result.bankleitzahl,
        'kontonummer': result.kontonummer,
        'sepa_faehig': result.sepa_faehig,
        'fehler': result.fehler
    }


def validate_bic(bic: str) -> Dict:
    """Schnell-Validierung eines BIC"""
    validator = SEPAValidator()
    return validator.validate_bic(bic)


def create_german_iban(blz: str, konto: str) -> Dict:
    """Erstellt deutsche IBAN aus BLZ/Konto"""
    validator = SEPAValidator()
    return validator.german_to_iban(blz, konto)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python sepa_validator.py <command> [args]")
        print("\nCommands:")
        print("  validate-iban <iban>       - IBAN validieren")
        print("  validate-bic <bic>         - BIC validieren")
        print("  create-iban <blz> <konto>  - Deutsche IBAN erstellen")
        print("  format <iban>              - IBAN formatieren")
        print("\nBeispiele:")
        print("  python sepa_validator.py validate-iban DE89370400440532013000")
        print("  python sepa_validator.py validate-bic COBADEFFXXX")
        print("  python sepa_validator.py create-iban 37040044 0532013000")
        sys.exit(1)
    
    command = sys.argv[1]
    validator = SEPAValidator()
    
    if command == "validate-iban":
        if len(sys.argv) < 3:
            print("❌ Fehler: IBAN angeben")
            sys.exit(1)
        
        iban = sys.argv[2]
        result = validator.validate_iban(iban)
        
        print(f"🔍 IBAN-Validierung")
        print("-" * 50)
        print(f"Eingabe: {iban}")
        print(f"Formatiert: {validator.format_iban_readable(result.iban)}")
        print(f"\nGültig: {'✅ Ja' if result.gueltig else '❌ Nein'}")
        print(f"Land: {result.land}")
        print(f"SEPA-fähig: {'✅ Ja' if result.sepa_faehig else '❌ Nein'}")
        
        if result.bankleitzahl:
            print(f"Bankleitzahl: {result.bankleitzahl}")
        if result.kontonummer:
            print(f"Kontonummer: {result.kontonummer}")
        
        if result.fehler:
            print(f"\n❌ Fehler:")
            for fehler in result.fehler:
                print(f"   - {fehler}")
    
    elif command == "validate-bic":
        if len(sys.argv) < 3:
            print("❌ Fehler: BIC angeben")
            sys.exit(1)
        
        bic = sys.argv[2]
        result = validator.validate_bic(bic)
        
        print(f"🔍 BIC-Validierung")
        print("-" * 50)
        print(f"BIC: {result['bic']}")
        print(f"Gültig: {'✅ Ja' if result['gueltig'] else '❌ Nein'}")
        print(f"Bankcode: {result['bankcode']}")
        print(f"Ländercode: {result['laendercode']}")
        print(f"Filiale: {result['filiale']}")
        
        if result['fehler']:
            print(f"\n❌ Fehler:")
            for fehler in result['fehler']:
                print(f"   - {fehler}")
    
    elif command == "create-iban":
        if len(sys.argv) < 4:
            print("❌ Fehler: BLZ und Kontonummer angeben")
            sys.exit(1)
        
        blz = sys.argv[2]
        konto = sys.argv[3]
        result = validator.german_to_iban(blz, konto)
        
        print(f"🔍 IBAN-Erstellung (Deutschland)")
        print("-" * 50)
        print(f"BLZ: {blz}")
        print(f"Kontonummer: {konto}")
        print("-" * 50)
        
        if result['gueltig']:
            print(f"✅ IBAN: {result['formatted']}")
            print(f"   Roh: {result['iban']}")
            print(f"   Prüfziffer: {result['pruefziffer']}")
        else:
            print("❌ Fehler:")
            for fehler in result['fehler']:
                print(f"   - {fehler}")
    
    elif command == "format":
        if len(sys.argv) < 3:
            print("❌ Fehler: IBAN angeben")
            sys.exit(1)
        
        iban = sys.argv[2]
        formatted = validator.format_iban_readable(iban)
        print(f"Formatierte IBAN: {formatted}")
    
    else:
        print(f"❌ Unbekannter Befehl: {command}")
