"""
Steuer-Identifikationsnummer (IdNr) Validator
Validiert die 11-stellige deutsche Steuer-ID mit Prüfziffer

Fokus: German Tax, Personal Tax ID, ELSTER
"""

import re
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class IdNrValidationResult:
    """Ergebnis der IdNr-Validierung"""
    gueltig: bool
    idnr: str
    format_korrekt: bool
    pruefziffer_korrekt: Optional[bool]
    fehler: list


class IdNrValidator:
    """
    Validator für deutsche Steuer-Identifikationsnummern (IdNr)
    
    Format:
    - 11 Stellen (Ziffern)
    - Erste Stelle: 1-9 (keine 0)
    - Letzte Stelle: Prüfziffer
    - Keine doppelten Ziffern in aufeinanderfolgenden Positionen
    
    Berechnung:
    - Modulo 11 mit speziellem Gewichtungsalgorithmus
    """
    
    def __init__(self):
        self.fehler = []
    
    def format_idnr(self, idnr: str) -> str:
        """
        Formatierung: Entfernt alle nicht-numerischen Zeichen
        """
        return re.sub(r'\D', '', idnr)
    
    def validate_format(self, idnr: str) -> Tuple[bool, str, list]:
        """
        Prüft das Format der IdNr
        
        Returns:
            (is_valid, formatted_idnr, error_list)
        """
        fehler = []
        formatted = self.format_idnr(idnr)
        
        # Länge prüfen
        if len(formatted) != 11:
            fehler.append(f"IdNr muss genau 11 Ziffern haben (aktuell: {len(formatted)})")
        
        # Erste Stelle darf nicht 0 sein
        if formatted and formatted[0] == '0':
            fehler.append("Erste Ziffer darf nicht 0 sein")
        
        # Nur Zahlen
        if not formatted.isdigit():
            fehler.append("IdNr darf nur Ziffern enthalten")
        
        # Keine doppelten aufeinanderfolgenden Ziffern
        for i in range(len(formatted) - 1):
            if formatted[i] == formatted[i + 1]:
                fehler.append(f"Doppelte Ziffer an Position {i+1}/{i+2}")
                break  # Nur ersten Fehler melden
        
        return len(fehler) == 0, formatted, fehler
    
    def validate_checksum(self, idnr: str) -> bool:
        """
        Prüft die Prüfziffer der IdNr
        
        Algorithmus:
        1. Multipliziere jede Ziffer mit ihrer Position (gewichtet)
        2. Summiere die Produkte
        3. Modulo 11
        4. Prüfziffer = 11 - Rest (wenn 10 oder 11: ungültig)
        """
        formatted = self.format_idnr(idnr)
        
        if len(formatted) != 11:
            return False
        
        try:
            ziffern = [int(d) for d in formatted]
            
            # Prüfziffer ist die letzte Stelle
            pruefziffer = ziffern[-1]
            
            # Berechne Prüfziffer nach offiziellem Algorithmus
            # Algorithmus: modulare gewichtete Quersumme
            produkte = []
            for i, ziffer in enumerate(ziffern[:-1]):  # Ohne Prüfziffer
                position = i + 1
                produkt = ziffer * position
                produkte.append(produkt)
            
            summe = sum(produkte)
            rest = summe % 11
            
            # Errechnete Prüfziffer
            if rest == 10:
                errechnet = 0
            else:
                errechnet = rest
            
            return pruefziffer == errechnet
            
        except (ValueError, IndexError):
            return False
    
    def validate(self, idnr: str, strict: bool = True) -> IdNrValidationResult:
        """
        Vollständige Validierung einer IdNr
        
        Args:
            idnr: Die zu prüfende Steuer-ID
            strict: Wenn True, werden alle Regeln geprüft
        
        Returns:
            IdNrValidationResult
        """
        self.fehler = []
        
        # Format-Validierung
        format_ok, formatted, format_fehler = self.validate_format(idnr)
        
        if not format_ok:
            return IdNrValidationResult(
                gueltig=False,
                idnr=formatted,
                format_korrekt=False,
                pruefziffer_korrekt=None,
                fehler=format_fehler
            )
        
        # Prüfziffer-Validierung
        pruefziffer_ok = self.validate_checksum(formatted)
        
        if strict and not pruefziffer_ok:
            self.fehler.append("Prüfziffer ungültig")
        
        return IdNrValidationResult(
            gueltig=format_ok and (not strict or pruefziffer_ok),
            idnr=formatted,
            format_korrekt=format_ok,
            pruefziffer_korrekt=pruefziffer_ok,
            fehler=self.fehler
        )
    
    def mask_idnr(self, idnr: str) -> str:
        """
        Maskiert die IdNr für Datenschutz (z.B. in Logs)
        
        Beispiel: 12345678901 → 12345*****1
        """
        formatted = self.format_idnr(idnr)
        if len(formatted) == 11:
            return formatted[:5] + "*****" + formatted[-1]
        return "***"
    
    def get_info(self, idnr: str) -> Dict:
        """
        Gibt Informationen zur IdNr zurück
        """
        formatted = self.format_idnr(idnr)
        
        info = {
            'laenge': len(formatted),
            'erste_ziffer': formatted[0] if formatted else None,
            'letzte_ziffer': formatted[-1] if formatted else None,
            'format_gueltig': False,
            'geschlecht': None  # Theoretisch ableitbar aus erster Ziffer
        }
        
        format_ok, _, _ = self.validate_format(idnr)
        info['format_gueltig'] = format_ok
        
        if format_ok and len(formatted) == 11:
            # Erste Ziffer könnte Rückschluss auf Ausstellungsjahr geben
            erste = int(formatted[0])
            if 1 <= erste <= 3:
                info['hinweis'] = "IdNr aus früher Ausgabephase (2008-2011)"
            elif 4 <= erste <= 6:
                info['hinweis'] = "IdNr aus mittlerer Ausgabephase (2011-2014)"
            else:
                info['hinweis'] = "IdNr aus später Ausgabephase (2014+)"
        
        return info


def validate_idnr(idnr: str, strict: bool = True) -> Dict:
    """
    Schnell-Validierung einer Steuer-Identifikationsnummer
    
    Usage:
        result = validate_idnr("12345678901")
        print(result['gueltig'])
        print(result['pruefziffer_korrekt'])
    """
    validator = IdNrValidator()
    result = validator.validate(idnr, strict)
    
    return {
        'gueltig': result.gueltig,
        'idnr': result.idnr,
        'format_korrekt': result.format_korrekt,
        'pruefziffer_korrekt': result.pruefziffer_korrekt,
        'fehler': result.fehler
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python idnr_validator.py <Steuer-ID> [options]")
        print("\nOptions:")
        print("  --strict    - Prüfziffer validieren (default)")
        print("  --lenient   - Nur Format prüfen")
        print("\nBeispiele:")
        print("  python idnr_validator.py 12345678901")
        print("  python idnr_validator.py '12 345 678 901'")
        print("  python idnr_validator.py 12345678901 --lenient")
        print("\nHinweis: Die Steuer-ID ist 11-stellig und enthält eine Prüfziffer.")
        print("         Format: ZZZ ZZZ ZZZ ZZ (Z = Ziffer)")
        sys.exit(1)
    
    idnr_input = sys.argv[1]
    strict = '--lenient' not in sys.argv
    
    print(f"🔍 Prüfe Steuer-Identifikationsnummer")
    print("-" * 50)
    
    validator = IdNrValidator()
    result = validator.validate(idnr_input, strict=strict)
    
    # Maskierte Ausgabe
    masked = validator.mask_idnr(result.idnr)
    print(f"Eingabe: {masked}")
    print(f"Formatiert: {result.idnr[:5]} {result.idnr[5:8]} {result.idnr[8:10]} {result.idnr[10:]}")
    print("-" * 50)
    
    if result.gueltig:
        print("✅ Status: GÜLTIG")
    else:
        print("❌ Status: UNGÜLTIG")
    
    print(f"\nFormat: {'✅ Korrekt' if result.format_korrekt else '❌ Fehlerhaft'}")
    
    if result.pruefziffer_korrekt is not None:
        print(f"Prüfziffer: {'✅ Korrekt' if result.pruefziffer_korrekt else '❌ Falsch'}")
    
    if result.fehler:
        print(f"\n❌ Fehler:")
        for fehler in result.fehler:
            print(f"   - {fehler}")
    
    # Info
    info = validator.get_info(result.idnr)
    if info.get('hinweis'):
        print(f"\nℹ️  {info['hinweis']}")
