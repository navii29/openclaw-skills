"""
EORI-Nummer Validierung
Validiert EORI-Nummern (Economic Operators Registration and Identification)
Wichtig für: E-Commerce Import/Export, Zoll, Brexit-Geschäfte

Fokus: German E-Commerce Automation
"""

import requests
from typing import Optional, Tuple
import re


class EORIValidator:
    """Validator für EORI-Nummern"""
    
    # Zoll-Webservice URLs
    EU_EORI_URL = "https://ec.europa.eu/taxation_customs/dds2/eos/validation"
    
    # Ländercodes EU + EWR
    EORI_COUNTRIES = {
        'AT': 'Österreich', 'BE': 'Belgien', 'BG': 'Bulgarien', 'HR': 'Kroatien',
        'CY': 'Zypern', 'CZ': 'Tschechien', 'DK': 'Dänemark', 'EE': 'Estland',
        'FI': 'Finnland', 'FR': 'Frankreich', 'DE': 'Deutschland', 'GR': 'Griechenland',
        'HU': 'Ungarn', 'IE': 'Irland', 'IT': 'Italien', 'LV': 'Lettland',
        'LT': 'Litauen', 'LU': 'Luxemburg', 'MT': 'Malta', 'NL': 'Niederlande',
        'PL': 'Polen', 'PT': 'Portugal', 'RO': 'Rumänien', 'SK': 'Slowakei',
        'SI': 'Slowenien', 'ES': 'Spanien', 'SE': 'Schweden',
        # EWR + Sonderfälle
        'IS': 'Island', 'LI': 'Liechtenstein', 'NO': 'Norwegen', 'CH': 'Schweiz',
        'GB': 'Großbritannien'
    }
    
    # Länderspezifische Formate
    FORMATS = {
        'DE': r'^DE\d{9}$',           # DE + 9 Ziffern
        'AT': r'^ATU\d{8}$',          # ATU + 8 Ziffern
        'BE': r'^BE0\d{9}$',          # BE0 + 9 Ziffern
        'FR': r'^FR[A-Z0-9]{11}$',    # FR + 11 alphanumerisch
        'IT': r'^IT\d{11}$',          # IT + 11 Ziffern
        'NL': r'^NL[A-Z0-9]{12}$',    # NL + 12 alphanumerisch
        'ES': r'^ES[A-Z]\d{8}$',      # ES + Buchstabe + 8 Ziffern
        'PL': r'^PL\d{10}$',          # PL + 10 Ziffern
        'GB': r'^GB[A-Z0-9]{12,15}$', # GB + 12-15 alphanumerisch
    }
    
    def __init__(self):
        self.session = requests.Session()
    
    def format_eori(self, eori: str) -> str:
        """Formatiert EORI zu standardisiertem Format"""
        # Entferne Leerzeichen und Sonderzeichen
        cleaned = re.sub(r'[^A-Za-z0-9]', '', eori).upper()
        return cleaned
    
    def extract_country(self, eori: str) -> Optional[str]:
        """Extrahiert Ländercode aus EORI"""
        formatted = self.format_eori(eori)
        if len(formatted) >= 2:
            return formatted[:2]
        return None
    
    def validate_format(self, eori: str) -> Tuple[bool, str, Optional[str]]:
        """
        Prüft das Format der EORI-Nummer
        
        Returns:
            (is_valid, formatted_eori, error_message)
        """
        formatted = self.format_eori(eori)
        
        if len(formatted) < 3:
            return False, formatted, "EORI zu kurz (min. 3 Zeichen)"
        
        country = formatted[:2]
        
        if country not in self.EORI_COUNTRIES:
            return False, formatted, f"Ungültiger Ländercode: {country}"
        
        # Länderspezifische Prüfung wenn verfügbar
        if country in self.FORMATS:
            if not re.match(self.FORMATS[country], formatted):
                return False, formatted, f"Ungültiges Format für {self.EORI_COUNTRIES[country]}"
        else:
            # Generische Prüfung: 2 Buchstaben + 3-15 alphanumerisch
            if not re.match(r'^[A-Z]{2}[A-Z0-9]{3,15}$', formatted):
                return False, formatted, "Ungültiges EORI-Format"
        
        return True, formatted, None
    
    def validate_online(self, eori: str) -> dict:
        """
        Online-Validierung über EU-Webservice
        
        Returns:
            dict mit Validierungsergebnis
        """
        valid, formatted, error = self.validate_format(eori)
        
        if not valid:
            return {
                'valid': False,
                'eori': formatted,
                'status': 'FORMAT_ERROR',
                'error': error
            }
        
        country = formatted[:2]
        
        try:
            # EU EORI Validation Service
            # Hinweis: Der echte Webservice benötigt spezifische SOAP Requests
            # Dies ist eine vereinfachte Implementierung
            
            url = f"{self.EU_EORI_URL}/?eori={formatted}"
            
            # Für deutsche EORI: Bundeszollverwaltung
            if country == 'DE':
                return self._validate_german_eori(formatted)
            
            return {
                'valid': None,
                'eori': formatted,
                'status': 'ONLINE_NOT_IMPLEMENTED',
                'land': self.EORI_COUNTRIES.get(country),
                'note': f'Online-Validierung für {country} erfordert spezifischen Zoll-Service'
            }
            
        except Exception as e:
            return {
                'valid': None,
                'eori': formatted,
                'status': 'ERROR',
                'error': str(e)
            }
    
    def _validate_german_eori(self, eori: str) -> dict:
        """
        Spezifische Validierung für deutsche EORI
        Deutsche EORI: DE + Zollnummer (9 Stellen)
        """
        # Prüfziffer-Validierung für deutsche EORI
        zollnummer = eori[2:]
        
        if len(zollnummer) != 9 or not zollnummer.isdigit():
            return {
                'valid': False,
                'eori': eori,
                'status': 'FORMAT_ERROR',
                'error': 'Deutsche EORI benötigt 9 Ziffern'
            }
        
        # Prüfziffer-Validierung (Modulo 11)
        pruefziffer_valid = self._check_zoll_pruefziffer(zollnummer)
        
        return {
            'valid': pruefziffer_valid,
            'eori': eori,
            'status': 'VALID' if pruefziffer_valid else 'INVALID_CHECKDIGIT',
            'land': 'Deutschland',
            'zollnummer': zollnummer,
            'pruefziffer_ok': pruefziffer_valid
        }
    
    def _check_zoll_pruefziffer(self, zollnummer: str) -> bool:
        """
        Berechnet die Prüfziffer für deutsche Zollnummern
        Gewichtung: 3-1-2-1-2-1-2-1-2
        """
        if len(zollnummer) != 9:
            return False
        
        try:
            ziffern = [int(d) for d in zollnummer]
            gewichte = [3, 1, 2, 1, 2, 1, 2, 1, 2]
            
            summe = sum(z * w for z, w in zip(ziffern, gewichte))
            pruefziffer_berechnet = summe % 11
            
            # Wenn Rest 10: ungültig
            if pruefziffer_berechnet == 10:
                return False
            
            # Letzte Ziffer ist Prüfziffer
            return ziffern[-1] == pruefziffer_berechnet
            
        except (ValueError, IndexError):
            return False
    
    def get_info(self, eori: str) -> dict:
        """Gibt Informationen zur EORI ohne Validierung"""
        formatted = self.format_eori(eori)
        country = self.extract_country(formatted)
        
        return {
            'eori': formatted,
            'laendercode': country,
            'land': self.EORI_COUNTRIES.get(country, 'Unbekannt'),
            'laenge': len(formatted),
            'format_gueltig': self.validate_format(eori)[0]
        }


def validate_eori(eori: str, online: bool = False) -> dict:
    """
    Schnell-Validierung einer EORI-Nummer
    
    Args:
        eori: Die zu prüfende EORI-Nummer
        online: Ob Online-Validierung durchgeführt werden soll
    
    Usage:
        result = validate_eori("DE123456789")
        result = validate_eori("DE123456789", online=True)
    """
    validator = EORIValidator()
    
    if online:
        return validator.validate_online(eori)
    
    valid, formatted, error = validator.validate_format(eori)
    return {
        'valid': valid,
        'eori': formatted,
        'status': 'VALID' if valid else 'INVALID',
        'error': error,
        'land': validator.EORI_COUNTRIES.get(formatted[:2]) if len(formatted) >= 2 else None
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python eori_validator.py <EORI> [--online]")
        print("\nBeispiele:")
        print("  python eori_validator.py DE123456789")
        print("  python eori_validator.py DE123456789 --online")
        print("\nWichtige EORI-Formate:")
        print("  DE: DE + 9 Ziffern (DE123456789)")
        print("  AT: ATU + 8 Ziffern (ATU12345678)")
        print("  NL: NL + 12 Zeichen (NL123456789B01)")
        sys.exit(1)
    
    eori = sys.argv[1]
    online = '--online' in sys.argv
    
    print(f"🔍 Prüfe EORI: {eori}")
    print("-" * 50)
    
    result = validate_eori(eori, online=online)
    
    if result.get('valid') is True:
        print("✅ Status: GÜLTIG")
    elif result.get('valid') is False:
        print("❌ Status: UNGÜLTIG")
    else:
        print("⚠️  Status: PRÜFUNG NICHT MÖGLICH")
    
    print(f"\nDetails:")
    for key, value in result.items():
        if value is not None:
            print(f"  {key}: {value}")
