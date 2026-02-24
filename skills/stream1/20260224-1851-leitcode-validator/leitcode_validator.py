"""
Deutsche Post Leitcode/Sendungsnummer Validator
Validiert Leitcodes für Massensendungen und Sendungsnummern

Fokus: German E-Commerce, Logistics, Deutsche Post
"""

import re
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class LeitcodeResult:
    """Ergebnis der Leitcode-Validierung"""
    gueltig: bool
    leitcode: str
    typ: str  # 'LEITCODE', 'SENDUNGSNUMMER', 'IDENTCODE'
    frachtpost: bool
    fehler: List[str]


class DeutschePostValidator:
    """
    Validator für Deutsche Post Codes
    
    Unterstützt:
    - Leitcode (14-stellig, Massensendungen)
    - Sendungsnummer (跟踪号, E-Commerce)
    - Identcode (Zustellnachweise)
    """
    
    # Leitcode: 14-stellig, 2x7 mit Prüfziffern
    LEITCODE_PATTERN = r'^[0-9]{14}$'
    
    # Sendungsnummern-Formate
    SENDUNGS_FORMATS = {
        'DHL_PACKET': r'^[0-9]{12}$',           # 003404341606
        'DHL_PACKET_INTERNATIONAL': r'^[A-Z]{2}[0-9]{9}DE$',  # RX123456789DE
        'DHL_EXPRESS': r'^[0-9]{10,11}$',        # 1234567890
        'DEUTSCHE_POST': r'^[A-Z]{2}[0-9]{9}DE$',  # Lx123456789DE
        'EINSCHREIBEN': r'^[A-Z]{1}[0-9]{9}DE$',   # R123456789DE
    }
    
    # Identcode (Zustellnachweis)
    IDENTCODE_PATTERN = r'^[0-9]{11}$'
    
    # Frachtpost-Kennung (erste beiden Stellen)
    FRACHTPOST_PREFIXES = ['40', '41', '42', '43', '44', '45']
    
    def __init__(self):
        self.fehler = []
    
    def format_code(self, code: str) -> str:
        """Formatiert Code (entfernt Leerzeichen)"""
        return re.sub(r'\s', '', code).upper()
    
    def validate_leitcode(self, leitcode: str) -> LeitcodeResult:
        """
        Validiert einen 14-stelligen Leitcode
        
        Format: NNNNNNNPNNNNNNP (2x7 Stellen mit jeweils Prüfziffer)
        
        Prüfziffer-Berechnung:
        - Modulo 10 mit Gewichtung 4-2-1
        """
        self.fehler = []
        formatted = self.format_code(leitcode)
        
        # Länge prüfen
        if len(formatted) != 14:
            return LeitcodeResult(
                gueltig=False,
                leitcode=formatted,
                typ='LEITCODE',
                frachtpost=False,
                fehler=[f'Leitcode muss 14 Ziffern haben (aktuell: {len(formatted)})']
            )
        
        # Nur Zahlen
        if not formatted.isdigit():
            return LeitcodeResult(
                gueltig=False,
                leitcode=formatted,
                typ='LEITCODE',
                frachtpost=False,
                fehler=['Leitcode darf nur Ziffern enthalten']
            )
        
        # Prüfziffern validieren (2x7)
        teil1_ok = self._validate_leitcode_part(formatted[:7])
        teil2_ok = self._validate_leitcode_part(formatted[7:14])
        
        if not teil1_ok:
            self.fehler.append('Prüfziffer der ersten 7 Stellen ungültig')
        if not teil2_ok:
            self.fehler.append('Prüfziffer der zweiten 7 Stellen ungültig')
        
        # Frachtpost prüfen
        is_frachtpost = formatted[:2] in self.FRACHTPOST_PREFIXES
        
        return LeitcodeResult(
            gueltig=teil1_ok and teil2_ok,
            leitcode=formatted,
            typ='LEITCODE',
            frachtpost=is_frachtpost,
            fehler=self.fehler
        )
    
    def _validate_leitcode_part(self, part: str) -> bool:
        """
        Prüft 7-stelligen Teil mit Prüfziffer
        
        Gewichtung: 4-2-1 wiederholend
        Stellen 1-6: Daten
        Stelle 7: Prüfziffer
        """
        if len(part) != 7 or not part.isdigit():
            return False
        
        try:
            ziffern = [int(d) for d in part]
            gewichte = [4, 2, 1, 4, 2, 1]  # Für Stellen 1-6
            
            # Berechne Summe
            summe = sum(z * w for z, w in zip(ziffern[:6], gewichte))
            
            # Prüfziffer = letzte Ziffer der Summe
            pruefziffer_berechnet = summe % 10
            
            return ziffern[6] == pruefziffer_berechnet
            
        except (ValueError, IndexError):
            return False
    
    def validate_sendungsnummer(self, sendungsnummer: str) -> LeitcodeResult:
        """
        Validiert Sendungsnummer (Tracking)
        
        Unterstützt:
        - DHL Packet (12-stellig numerisch)
        - DHL Packet International (XX123456789DE)
        - DHL Express (10-11 Stellen)
        - Deutsche Post Briefe (LX...DE)
        """
        self.fehler = []
        formatted = self.format_code(sendungsnummer)
        
        # Bestimme Typ
        typ = self._detect_sendung_type(formatted)
        
        if typ == 'UNKNOWN':
            return LeitcodeResult(
                gueltig=False,
                leitcode=formatted,
                typ='UNKNOWN',
                frachtpost=False,
                fehler=['Unbekanntes Sendungsnummern-Format']
            )
        
        # Prüfe gegen Pattern
        pattern = self.SENDUNGS_FORMATS.get(typ)
        if pattern and not re.match(pattern, formatted):
            return LeitcodeResult(
                gueltig=False,
                leitcode=formatted,
                typ=typ,
                frachtpost=False,
                fehler=[f'Format ungültig für {typ}']
            )
        
        return LeitcodeResult(
            gueltig=True,
            leitcode=formatted,
            typ=typ,
            frachtpost=False,
            fehler=[]
        )
    
    def _detect_sendung_type(self, sendungsnummer: str) -> str:
        """Erkennt den Sendungstyp anhand des Formats"""
        # DHL Packet International / Deutsche Post
        if re.match(r'^[A-Z]{2}[0-9]{9}DE$', sendungsnummer):
            if sendungsnummer.startswith(('RX', 'LX', 'CZ')):
                return 'DHL_PACKET_INTERNATIONAL'
            return 'DEUTSCHE_POST'
        
        # DHL Packet (12-stellig)
        if re.match(r'^[0-9]{12}$', sendungsnummer):
            return 'DHL_PACKET'
        
        # DHL Express (10-11 Stellen)
        if re.match(r'^[0-9]{10,11}$', sendungsnummer):
            return 'DHL_EXPRESS'
        
        # Einschreiben (1 Buchstabe + 9 Ziffern + DE)
        if re.match(r'^[A-Z][0-9]{9}DE$', sendungsnummer):
            return 'EINSCHREIBEN'
        
        return 'UNKNOWN'
    
    def validate_identcode(self, identcode: str) -> LeitcodeResult:
        """
        Validiert Identcode (Zustellnachweis)
        
        Format: 11-stellig numerisch
        """
        self.fehler = []
        formatted = self.format_code(identcode)
        
        if len(formatted) != 11:
            return LeitcodeResult(
                gueltig=False,
                leitcode=formatted,
                typ='IDENTCODE',
                frachtpost=False,
                fehler=[f'Identcode muss 11 Ziffern haben (aktuell: {len(formatted)})']
            )
        
        if not formatted.isdigit():
            return LeitcodeResult(
                gueltig=False,
                leitcode=formatted,
                typ='IDENTCODE',
                frachtpost=False,
                fehler=['Identcode darf nur Ziffern enthalten']
            )
        
        return LeitcodeResult(
            gueltig=True,
            leitcode=formatted,
            typ='IDENTCODE',
            frachtpost=False,
            fehler=[]
        )
    
    def get_tracking_url(self, sendungsnummer: str) -> Optional[str]:
        """Gibt Tracking-URL zurück"""
        formatted = self.format_code(sendungsnummer)
        typ = self._detect_sendung_type(formatted)
        
        if typ in ['DHL_PACKET', 'DHL_PACKET_INTERNATIONAL']:
            return f"https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html?piececode={formatted}"
        
        if typ == 'DHL_EXPRESS':
            return f"https://www.dhl.com/de-de/home/tracking/tracking-express.html?submit=1&tracking-id={formatted}"
        
        if typ in ['DEUTSCHE_POST', 'EINSCHREIBEN']:
            return f"https://www.deutschepost.de/sendung/simpleQuery.html?form.sendungsnummer={formatted}"
        
        return None


def validate_leitcode(leitcode: str) -> Dict:
    """Schnell-Validierung Leitcode"""
    validator = DeutschePostValidator()
    result = validator.validate_leitcode(leitcode)
    
    return {
        'gueltig': result.gueltig,
        'leitcode': result.leitcode,
        'frachtpost': result.frachtpost,
        'fehler': result.fehler
    }


def validate_sendungsnummer(sendungsnummer: str) -> Dict:
    """Schnell-Validierung Sendungsnummer"""
    validator = DeutschePostValidator()
    result = validator.validate_sendungsnummer(sendungsnummer)
    
    return {
        'gueltig': result.gueltig,
        'sendungsnummer': result.leitcode,
        'typ': result.typ,
        'tracking_url': validator.get_tracking_url(sendungsnummer),
        'fehler': result.fehler
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python leitcode_validator.py <command> [args]")
        print("\nCommands:")
        print("  validate-leitcode <code>      - Leitcode validieren")
        print("  validate-sendung <nummer>     - Sendungsnummer validieren")
        print("  validate-ident <code>         - Identcode validieren")
        print("  tracking-url <nummer>         - Tracking-URL anzeigen")
        print("\nBeispiele:")
        print("  python leitcode_validator.py validate-leitcode 12345671234567")
        print("  python leitcode_validator.py validate-sendung 003404341606")
        print("  python leitcode_validator.py validate-sendung RX123456789DE")
        sys.exit(1)
    
    command = sys.argv[1]
    validator = DeutschePostValidator()
    
    if command == "validate-leitcode":
        if len(sys.argv) < 3:
            print("❌ Fehler: Leitcode angeben")
            sys.exit(1)
        
        code = sys.argv[2]
        result = validator.validate_leitcode(code)
        
        print(f"🔍 Leitcode-Validierung")
        print("-" * 50)
        print(f"Eingabe: {code}")
        print(f"Formatiert: {result.leitcode}")
        print(f"\nGültig: {'✅ Ja' if result.gueltig else '❌ Nein'}")
        print(f"Frachtpost: {'✅ Ja' if result.frachtpost else '❌ Nein'}")
        
        if result.fehler:
            print(f"\n❌ Fehler:")
            for fehler in result.fehler:
                print(f"   - {fehler}")
    
    elif command == "validate-sendung":
        if len(sys.argv) < 3:
            print("❌ Fehler: Sendungsnummer angeben")
            sys.exit(1)
        
        nummer = sys.argv[2]
        result = validator.validate_sendungsnummer(nummer)
        
        print(f"🔍 Sendungsnummer-Validierung")
        print("-" * 50)
        print(f"Eingabe: {nummer}")
        print(f"Formatiert: {result.leitcode}")
        print(f"\nGültig: {'✅ Ja' if result.gueltig else '❌ Nein'}")
        print(f"Typ: {result.typ}")
        
        url = validator.get_tracking_url(nummer)
        if url:
            print(f"Tracking-URL: {url}")
        
        if result.fehler:
            print(f"\n❌ Fehler:")
            for fehler in result.fehler:
                print(f"   - {fehler}")
    
    elif command == "validate-ident":
        if len(sys.argv) < 3:
            print("❌ Fehler: Identcode angeben")
            sys.exit(1)
        
        code = sys.argv[2]
        result = validator.validate_identcode(code)
        
        print(f"🔍 Identcode-Validierung")
        print("-" * 50)
        print(f"Gültig: {'✅ Ja' if result.gueltig else '❌ Nein'}")
        print(f"Code: {result.leitcode}")
        
        if result.fehler:
            print(f"\n❌ Fehler:")
            for fehler in result.fehler:
                print(f"   - {fehler}")
    
    elif command == "tracking-url":
        if len(sys.argv) < 3:
            print("❌ Fehler: Sendungsnummer angeben")
            sys.exit(1)
        
        nummer = sys.argv[2]
        url = validator.get_tracking_url(nummer)
        
        if url:
            print(f"🔗 Tracking-URL:\n{url}")
        else:
            print("❌ Keine Tracking-URL verfügbar")
    
    else:
        print(f"❌ Unbekannter Befehl: {command}")
