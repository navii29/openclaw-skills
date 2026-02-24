"""
Deutsche USt-IdNr Validierung
Validiert USt-IdNr gegen das BZSt (Bundeszentralamt für Steuern)

Fokus: German E-Commerce Automation
"""

import requests
import xml.etree.ElementTree as ET
from typing import Optional, Tuple
import re


class UStIdValidator:
    """Validator für deutsche und europäische USt-IdNummern"""
    
    BZST_URL = "https://evatr.bff-online.de/evatrRPC"
    
    # Ländercodes EU
    EU_COUNTRIES = {
        'AT': 'Österreich', 'BE': 'Belgien', 'BG': 'Bulgarien', 'HR': 'Kroatien',
        'CY': 'Zypern', 'CZ': 'Tschechien', 'DK': 'Dänemark', 'EE': 'Estland',
        'FI': 'Finnland', 'FR': 'Frankreich', 'DE': 'Deutschland', 'GR': 'Griechenland',
        'HU': 'Ungarn', 'IE': 'Irland', 'IT': 'Italien', 'LV': 'Lettland',
        'LT': 'Litauen', 'LU': 'Luxemburg', 'MT': 'Malta', 'NL': 'Niederlande',
        'PL': 'Polen', 'PT': 'Portugal', 'RO': 'Rumänien', 'SK': 'Slowakei',
        'SI': 'Slowenien', 'ES': 'Spanien', 'SE': 'Schweden'
    }
    
    def __init__(self):
        self.session = requests.Session()
    
    def format_ustid(self, ustid: str) -> str:
        """Formatiert USt-IdNr zu standardisiertem Format (DEXXXXXXXXX)"""
        # Entferne Leerzeichen und Sonderzeichen
        cleaned = re.sub(r'[^A-Za-z0-9]', '', ustid).upper()
        
        # Füge DE hinzu wenn nur Zahlen
        if cleaned.isdigit() and len(cleaned) == 9:
            cleaned = 'DE' + cleaned
        
        return cleaned
    
    def validate_format(self, ustid: str) -> Tuple[bool, str]:
        """Prüft nur das Format der USt-IdNr"""
        formatted = self.format_ustid(ustid)
        
        # Deutsche USt-IdNr: DE + 9 Ziffern
        if formatted.startswith('DE'):
            if re.match(r'^DE\d{9}$', formatted):
                return True, formatted
            return False, f"Ungültiges Format: Deutsche USt-IdNr benötigt DE + 9 Ziffern"
        
        # EU-USt-IdNr: 2 Buchstaben + Variabel
        if re.match(r'^[A-Z]{2}[A-Z0-9]{2,12}$', formatted):
            return True, formatted
        
        return False, f"Ungültiges Format: {formatted}"
    
    def validate_online(self, ustid: str, 
                        eigen_ustid: Optional[str] = None,
                        firma: Optional[str] = None,
                        ort: Optional[str] = None,
                        plz: Optional[str] = None,
                        strasse: Optional[str] = None) -> dict:
        """
        Validierung gegen BZSt-Webservice
        
        Args:
            ustid: Zu prüfende USt-IdNr
            eigen_ustid: Eigene deutsche USt-IdNr (für qualifizierte Prüfung)
            firma, ort, plz, strasse: Optional für qualifizierte Prüfung
        
        Returns:
            dict mit Ergebnis der Validierung
        """
        valid, formatted = self.validate_format(ustid)
        if not valid:
            return {
                'valid': False,
                'error': formatted,
                'status': 'FORMAT_ERROR',
                'druck': None,
                'ergebnis': None
            }
        
        # Nur deutsche USt-IdNr können beim BZSt geprüft werden
        if not formatted.startswith('DE'):
            return {
                'valid': True,  # Format ist OK
                'format_check': True,
                'online_check': False,
                'status': 'EU_FORMAT_VALID',
                'note': 'Online-Prüfung nur für deutsche USt-IdNr verfügbar',
                'land': self.EU_COUNTRIES.get(formatted[:2], 'Unbekannt')
            }
        
        # BZSt Request vorbereiten
        params = {
            'UstId_1': eigen_ustid or 'DE123456789',  # Demo-Wert
            'UstId_2': formatted,
            'Firmenname': firma or '',
            'Ort': ort or '',
            'PLZ': plz or '',
            'Strasse': strasse or '',
            'Druck': 'nein'
        }
        
        try:
            response = self.session.get(self.BZST_URL, params=params, timeout=30)
            response.raise_for_status()
            
            # XML Response parsen
            return self._parse_response(response.text, formatted)
            
        except requests.Timeout:
            return {
                'valid': None,
                'error': 'Timeout beim BZSt-Server',
                'status': 'TIMEOUT',
                'ustid': formatted
            }
        except Exception as e:
            return {
                'valid': None,
                'error': str(e),
                'status': 'ERROR',
                'ustid': formatted
            }
    
    def _parse_response(self, xml_text: str, ustid: str) -> dict:
        """Parsed die XML-Antwort des BZSt"""
        try:
            # BZSt liefert XML-RPC Format
            # Extrahiere Parameter
            result = {
                'valid': False,
                'ustid': ustid,
                'status': 'UNKNOWN',
                'error_code': None,
                'error_message': None,
                'datum': None,
                'uhrzeit': None
            }
            
            # Suche nach Ergebnis-Code
            if 'ErrorCode' in xml_text:
                # Extrahiere Error Code
                match = re.search(r'<string>(\d{3})</string>', xml_text)
                if match:
                    error_code = match.group(1)
                    result['error_code'] = error_code
                    result['error_message'] = self._get_error_message(error_code)
            
            # Prüfe auf erfolgreiche Validierung (200 = gültig)
            if '200' in xml_text or '216' in xml_text:
                result['valid'] = True
                result['status'] = 'VALID'
            elif '201' in xml_text:
                result['valid'] = False
                result['status'] = 'INVALID'
            elif '202' in xml_text:
                result['valid'] = None
                result['status'] = 'NOT_REGISTERED'
            elif '203' in xml_text or '204' in xml_text:
                result['valid'] = None
                result['status'] = 'VALIDATION_NOT_POSSIBLE'
            
            # Extrahiere Datum/Uhrzeit
            date_match = re.search(r'<dateTime\.iso8601>(\d{8})T(\d{6})', xml_text)
            if date_match:
                result['datum'] = date_match.group(1)
                result['uhrzeit'] = date_match.group(2)
            
            return result
            
        except Exception as e:
            return {
                'valid': None,
                'error': f'Parse-Fehler: {str(e)}',
                'status': 'PARSE_ERROR',
                'ustid': ustid
            }
    
    def _get_error_message(self, code: str) -> str:
        """BZSt Fehlercodes"""
        codes = {
            '200': 'USt-IdNr ist gültig',
            '201': 'USt-IdNr ist ungültig',
            '202': 'Die angefragte USt-IdNr ist nicht registriert',
            '203': 'Prüfung nicht möglich (Timeout)',
            '204': 'Prüfung nicht möglich (Fehler)',
            '205': 'Ihre eigene USt-IdNr ist ungültig',
            '206': 'Ihre eigene USt-IdNr fehlt',
            '207': 'Ihre eigene USt-IdNr ist ungültig',
            '208': 'Ihre eigene USt-IdNr hat falsches Format',
            '209': 'Anfrage-USt-IdNr fehlt',
            '210': 'Anfrage-USt-IdNr hat falsches Format',
            '211': 'Anfrage-USt-IdNr beginnt nicht mit EU-Ländercode',
            '212': 'Ungültiges Länderkürzel',
            '213': 'Falsche Parameter',
            '214': 'Ihre deutsche USt-IdNr ist ungültig',
            '215': 'Ihre deutsche USt-IdNr fehlt',
            '216': 'Gültig (mit Unterschieden im Adressfeld)',
            '217': 'Gültig (ohne Adressabgleich)',
            '218': 'Test-Verfahren aktiv',
            '219': 'Anfragelimit überschritten',
            '220': 'Test-Verfahren inaktiv',
            '221': 'IP-Adresse gesperrt',
            '222': 'Ungültige Auftragsnummer'
        }
        return codes.get(code, f'Unbekannter Fehler (Code {code})')


def validate_ustid(ustid: str, **kwargs) -> dict:
    """
    Schnell-Validierung einer USt-IdNr
    
    Usage:
        result = validate_ustid("DE123456789")
        result = validate_ustid("DE123456789", eigen_ustid="DE987654321")
    """
    validator = UStIdValidator()
    return validator.validate_online(ustid, **kwargs)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ustid_validator.py <USt-IdNr> [eigene_UStIdNr]")
        print("\nBeispiele:")
        print("  python ustid_validator.py DE123456789")
        print("  python ustid_validator.py DE123456789 DE987654321")
        sys.exit(1)
    
    ustid = sys.argv[1]
    eigen_ustid = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"🔍 Prüfe USt-IdNr: {ustid}")
    print("-" * 50)
    
    result = validate_ustid(ustid, eigen_ustid=eigen_ustid)
    
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
