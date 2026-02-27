"""
GoBD Compliance Checker

Prüft Rechnungen und Buchungsdaten auf Einhaltung der GoBD
(Grundsätze zur ordnungsmäßigen Führung und Aufbewahrung von Büchern).

Prüft alle 11 Pflichtangaben nach § 14 UStG:
1. Name und Anschrift des leistenden Unternehmers
2. Name und Anschrift des Leistungsempfängers
3. Steuernummer oder USt-IdNr des leistenden Unternehmers
4. Ausstellungsdatum
5. Rechnungsnummer (fortlaufend, eindeutig)
6. Menge und Bezeichnung der gelieferten Gegenstände/Dienstleistungen
7. Zeitpunkt der Lieferung/Leistung
8. Entgelt (netto)
9. Steuersatz oder Steuerbefreiung
10. Umsatzsteuerbetrag
11. Unveränderbarkeit (Hash)
"""

import re
import hashlib
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from decimal import Decimal


class GoBDError(Exception):
    """Basis-Exception für GoBD-Fehler"""
    pass


class InvalidRechnungError(GoBDError):
    """Ungültige Rechnung"""
    pass


class ChronologieFehler(GoBDError):
    """Fehler in der Rechnungsnummern-Chronologie"""
    pass


@dataclass
class Rechnungsposition:
    """Eine Position auf einer Rechnung"""
    bezeichnung: str
    menge: float
    preis: float  # Netto-Einzelpreis
    steuersatz: float  # z.B. 19.0 oder 7.0
    einheit: str = "Stk"
    
    @property
    def netto(self) -> float:
        """Netto-Gesamtbetrag der Position"""
        return self.menge * self.preis
    
    @property
    def ust(self) -> float:
        """Umsatzsteuer der Position"""
        return self.netto * (self.steuersatz / 100)
    
    @property
    def brutto(self) -> float:
        """Brutto-Gesamtbetrag der Position"""
        return self.netto + self.ust


@dataclass
class Rechnung:
    """
    Repräsentiert eine Rechnung mit allen GoBD-relevanten Feldern.
    """
    # Rechnungsnummer (Pflichtangabe 5)
    rechnungsnr: str
    
    # Daten (Pflichtangabe 4)
    ausstellungsdatum: str  # ISO-Format: YYYY-MM-DD
    
    # Lieferdatum/Leistungsdatum (Pflichtangabe 7)
    lieferdatum: str  # ISO-Format: YYYY-MM-DD
    
    # Leistender Unternehmer (Pflichtangabe 1, 3)
    steller_name: str
    steller_anschrift: str
    empfaenger_name: str
    empfaenger_anschrift: str
    
    # Optional: Steuer-IDs
    steller_ustid: Optional[str] = None
    steller_steuernummer: Optional[str] = None
    
    # Positionen (Pflichtangabe 6)
    positionen: List[Rechnungsposition] = field(default_factory=list)
    
    # Metadaten
    waehrung: str = "EUR"
    notizen: str = ""
    
    @property
    def netto_gesamt(self) -> float:
        """Gesamt-Nettobetrag"""
        return sum(pos.netto for pos in self.positionen)
    
    @property
    def ust_gesamt(self) -> float:
        """Gesamt-Umsatzsteuer"""
        return sum(pos.ust for pos in self.positionen)
    
    @property
    def brutto_gesamt(self) -> float:
        """Gesamt-Bruttobetrag"""
        return self.netto_gesamt + self.ust_gesamt
    
    @property
    def hat_steuerbefreiung(self) -> bool:
        """Hat die Rechnung steuerbefreite Positionen?"""
        return any(pos.steuersatz == 0 for pos in self.positionen)
    
    def zu_dict(self) -> Dict[str, Any]:
        """Konvertiert Rechnung in Dictionary (für Hash)"""
        return {
            'rechnungsnr': self.rechnungsnr,
            'ausstellungsdatum': self.ausstellungsdatum,
            'lieferdatum': self.lieferdatum,
            'steller_name': self.steller_name,
            'steller_anschrift': self.steller_anschrift,
            'steller_ustid': self.steller_ustid,
            'steller_steuernummer': self.steller_steuernummer,
            'empfaenger_name': self.empfaenger_name,
            'empfaenger_anschrift': self.empfaenger_anschrift,
            'positionen': [
                {
                    'bezeichnung': pos.bezeichnung,
                    'menge': pos.menge,
                    'preis': pos.preis,
                    'steuersatz': pos.steuersatz,
                }
                for pos in self.positionen
            ],
            'waehrung': self.waehrung,
        }


@dataclass
class PruefErgebnis:
    """Ergebnis einer GoBD-Prüfung"""
    ist_konform: bool
    pflichtangaben: Dict[str, bool]
    mangel: List[str]
    empfohlene_aktionen: List[str]
    hash: Optional[str] = None
    
    def zu_dict(self) -> Dict[str, Any]:
        """Konvertiert Ergebnis in Dictionary"""
        return {
            'ist_konform': self.ist_konform,
            'pflichtangaben': self.pflichtangaben,
            'mangel': self.mangel,
            'empfohlene_aktionen': self.empfohlene_aktionen,
            'hash': self.hash,
        }


class GoBDChecker:
    """
    Prüft Rechnungen auf GoBD-Konformität.
    
    Überprüft alle 11 Pflichtangaben nach § 14 UStG und GoBD.
    """
    
    def __init__(self, mindest_steuer: float = 0.01):
        """
        Initialisiert den Checker.
        
        Args:
            mindest_steuer: Mindestbetrag für Steuerpflicht (in EUR)
        """
        self.mindest_steuer = mindest_steuer
    
    def pruefe_rechnung(self, rechnung: Rechnung, mit_hash: bool = True) -> PruefErgebnis:
        """
        Prüft eine Rechnung auf GoBD-Konformität.
        
        Args:
            rechnung: Die zu prüfende Rechnung
            mit_hash: Soll ein Hash berechnet werden?
            
        Returns:
            PruefErgebnis mit Details
        """
        mangel = []
        empfohlene_aktionen = []
        pflichtangaben = {}
        
        # 1. Name und Anschrift des leistenden Unternehmers
        pflichtangaben['steller_name'] = self._ist_nicht_leer(rechnung.steller_name)
        pflichtangaben['steller_anschrift'] = self._ist_nicht_leer(rechnung.steller_anschrift)
        
        if not pflichtangaben['steller_name']:
            mangel.append("Fehlender Name des leistenden Unternehmers (Pflichtangabe 1)")
            empfohlene_aktionen.append("Namen des Rechnungsstellers ergänzen")
        
        if not pflichtangaben['steller_anschrift']:
            mangel.append("Fehlende Anschrift des leistenden Unternehmers (Pflichtangabe 1)")
            empfohlene_aktionen.append("Anschrift des Rechnungsstellers ergänzen")
        
        # 2. Name und Anschrift des Leistungsempfängers
        pflichtangaben['empfaenger_name'] = self._ist_nicht_leer(rechnung.empfaenger_name)
        pflichtangaben['empfaenger_anschrift'] = self._ist_nicht_leer(rechnung.empfaenger_anschrift)
        
        if not pflichtangaben['empfaenger_name']:
            mangel.append("Fehlender Name des Leistungsempfängers (Pflichtangabe 2)")
        
        if not pflichtangaben['empfaenger_anschrift']:
            mangel.append("Fehlende Anschrift des Leistungsempfängers (Pflichtangabe 2)")
        
        # 3. Steuernummer oder USt-IdNr des leistenden Unternehmers
        ustid_valid = self._validate_ustid(rechnung.steller_ustid)
        stnr_valid = self._validate_steuernummer(rechnung.steller_steuernummer)
        pflichtangaben['steller_steuerid'] = ustid_valid or stnr_valid
        
        if not pflichtangaben['steller_steuerid']:
            mangel.append("Fehlende USt-IdNr oder Steuernummer des Rechnungsstellers (Pflichtangabe 3)")
            empfohlene_aktionen.append("USt-IdNr (DE123456789) oder Steuernummer ergänzen")
        
        # 4. Ausstellungsdatum
        pflichtangaben['ausstellungsdatum'] = self._validate_datum(rechnung.ausstellungsdatum)
        
        if not pflichtangaben['ausstellungsdatum']:
            mangel.append("Fehlendes oder ungültiges Ausstellungsdatum (Pflichtangabe 4)")
            empfohlene_aktionen.append("Ausstellungsdatum im Format YYYY-MM-DD ergänzen")
        
        # 5. Rechnungsnummer
        pflichtangaben['rechnungsnr'] = self._ist_nicht_leer(rechnung.rechnungsnr)
        
        if not pflichtangaben['rechnungsnr']:
            mangel.append("Fehlende Rechnungsnummer (Pflichtangabe 5)")
            empfohlene_aktionen.append("Eindeutige Rechnungsnummer vergeben")
        
        # 6. Menge und Bezeichnung der Positionen
        pflichtangaben['positionen'] = len(rechnung.positionen) > 0
        
        if not pflichtangaben['positionen']:
            mangel.append("Keine Rechnungspositionen vorhanden (Pflichtangabe 6)")
            empfohlene_aktionen.append("Mindestens eine Rechnungsposition hinzufügen")
        else:
            for i, pos in enumerate(rechnung.positionen, 1):
                if not self._ist_nicht_leer(pos.bezeichnung):
                    mangel.append(f"Position {i}: Fehlende Bezeichnung (Pflichtangabe 6)")
                if pos.menge <= 0:
                    mangel.append(f"Position {i}: Ungültige Menge (Pflichtangabe 6)")
                if pos.preis < 0:
                    mangel.append(f"Position {i}: Negativer Preis (Pflichtangabe 6)")
        
        # 7. Lieferdatum/Leistungsdatum
        pflichtangaben['lieferdatum'] = self._validate_datum(rechnung.lieferdatum)
        
        if not pflichtangaben['lieferdatum']:
            mangel.append("Fehlendes oder ungültiges Lieferdatum/Leistungsdatum (Pflichtangabe 7)")
            empfohlene_aktionen.append("Lieferdatum/Leistungsdatum im Format YYYY-MM-DD ergänzen")
        
        # 8. Entgelt (netto) - wird über Positionen geprüft
        pflichtangaben['entgelt'] = rechnung.netto_gesamt >= 0
        
        if not pflichtangaben['entgelt']:
            mangel.append("Fehlendes Entgelt (Pflichtangabe 8)")
        
        # 9. Steuersatz oder Steuerbefreiung
        pflichtangaben['steuersatz'] = all(
            pos.steuersatz >= 0 for pos in rechnung.positionen
        )
        
        if not pflichtangaben['steuersatz']:
            mangel.append("Fehlender Steuersatz (Pflichtangabe 9)")
        elif rechnung.hat_steuerbefreiung:
            empfohlene_aktionen.append("Steuerbefreiung gesondert kennzeichnen (§ 14 Abs. 3 UStG)")
        
        # 10. Umsatzsteuerbetrag
        pflichtangaben['steuerbetrag'] = rechnung.ust_gesamt >= 0
        
        if not pflichtangaben['steuerbetrag']:
            mangel.append("Fehlender Umsatzsteuerbetrag (Pflichtangabe 10)")
        
        # Hash berechnen (Pflichtangabe 11 - Unveränderbarkeit)
        hash_wert = None
        if mit_hash:
            hash_wert = self.berechne_hash(rechnung)
            pflichtangaben['hash'] = hash_wert is not None
        
        # Gesamtergebnis
        ist_konform = all(pflichtangaben.values()) and len(mangel) == 0
        
        return PruefErgebnis(
            ist_konform=ist_konform,
            pflichtangaben=pflichtangaben,
            mangel=mangel,
            empfohlene_aktionen=empfohlene_aktionen,
            hash=hash_wert
        )
    
    def berechne_hash(self, rechnung: Rechnung) -> str:
        """
        Berechnet einen SHA-256 Hash der Rechnung für Unveränderbarkeit.
        
        Args:
            rechnung: Die Rechnung
            
        Returns:
            SHA-256 Hash als Hex-String
        """
        # Rechnung als JSON serialisieren (sortiert für Konsistenz)
        data = json.dumps(rechnung.zu_dict(), sort_keys=True, ensure_ascii=False)
        
        # Hash berechnen
        sha256 = hashlib.sha256()
        sha256.update(data.encode('utf-8'))
        
        return f"sha256:{sha256.hexdigest()}"
    
    def verifiziere_hash(self, rechnung: Rechnung, erwarteter_hash: str) -> bool:
        """
        Verifiziert ob die Rechnung mit dem erwarteten Hash übereinstimmt.
        
        Args:
            rechnung: Die Rechnung
            erwarteter_hash: Der erwartete Hash-Wert
            
        Returns:
            True wenn Hash übereinstimmt
        """
        aktueller_hash = self.berechne_hash(rechnung)
        return aktueller_hash == erwarteter_hash
    
    def pruefe_batch(self, rechnungen: List[Rechnung]) -> Dict[str, Any]:
        """
        Prüft mehrere Rechnungen auf einmal.
        
        Args:
            rechnungen: Liste von Rechnungen
            
        Returns:
            Batch-Prüfergebnis
        """
        ergebnisse = []
        konforme = 0
        nicht_konforme = 0
        
        for rechnung in rechnungen:
            ergebnis = self.pruefe_rechnung(rechnung)
            ergebnisse.append({
                'rechnungsnr': rechnung.rechnungsnr,
                'ergebnis': ergebnis
            })
            
            if ergebnis.ist_konform:
                konforme += 1
            else:
                nicht_konforme += 1
        
        return {
            'gesamt': len(rechnungen),
            'konform': konforme,
            'nicht_konform': nicht_konforme,
            'konformitaetsrate': konforme / len(rechnungen) if rechnungen else 0,
            'einzelergebnisse': ergebnisse,
        }
    
    def _ist_nicht_leer(self, wert: Optional[str]) -> bool:
        """Prüft ob ein String-Wert nicht leer ist"""
        return wert is not None and len(wert.strip()) > 0
    
    def _validate_ustid(self, ustid: Optional[str]) -> bool:
        """Validiert eine USt-IdNr"""
        if not ustid:
            return False
        
        ustid = ustid.upper().replace(' ', '')
        
        # DE gefolgt von 9 Ziffern
        if not ustid.startswith('DE'):
            return False
        
        ziffern = ustid[2:]
        return len(ziffern) == 9 and ziffern.isdigit()
    
    def _validate_steuernummer(self, stnr: Optional[str]) -> bool:
        """Validiert eine Steuernummer (vereinfacht)"""
        if not stnr:
            return False
        
        # Mindestens 10 Ziffern
        ziffern = re.sub(r'\D', '', stnr)
        return len(ziffern) >= 10
    
    def _validate_datum(self, datum: Optional[str]) -> bool:
        """Validiert ein Datum im Format YYYY-MM-DD"""
        if not datum:
            return False
        
        try:
            datetime.strptime(datum, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    def generiere_bericht(self, ergebnis: PruefErgebnis, rechnung: Rechnung) -> str:
        """
        Generiert einen menschenlesbaren Prüfbericht.
        
        Args:
            ergebnis: Das Prüfergebnis
            rechnung: Die geprüfte Rechnung
            
        Returns:
            Formatted string mit Bericht
        """
        lines = [
            "=" * 60,
            "GoBD-PRÜFUNGSBERICHT",
            "=" * 60,
            f"Rechnungsnummer: {rechnung.rechnungsnr}",
            f"Ausstellungsdatum: {rechnung.ausstellungsdatum}",
            f"Rechnungssteller: {rechnung.steller_name}",
            f"Rechnungsempfänger: {rechnung.empfaenger_name}",
            f"Nettobetrag: {rechnung.netto_gesamt:.2f} EUR",
            f"USt: {rechnung.ust_gesamt:.2f} EUR",
            f"Bruttobetrag: {rechnung.brutto_gesamt:.2f} EUR",
            "-" * 60,
        ]
        
        if ergebnis.ist_konform:
            lines.append("✅ RECHNUNG IST GoBD-KONFORM")
        else:
            lines.append("❌ RECHNUNG IST NICHT GoBD-KONFORM")
            lines.append("")
            lines.append("MÄNGEL:")
            for mangel in ergebnis.mangel:
                lines.append(f"  • {mangel}")
            
            if ergebnis.empfohlene_aktionen:
                lines.append("")
                lines.append("EMPFOHLENE AKTIONEN:")
                for aktion in set(ergebnis.empfohlene_aktionen):
                    lines.append(f"  → {aktion}")
        
        if ergebnis.hash:
            lines.append("")
            lines.append(f"Hash (Unveränderbarkeit): {ergebnis.hash}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)


class ChronologiePruefer:
    """
    Prüft die Chronologie von Rechnungsnummern.
    
    GoBD-Anforderung: Rechnungsnummern müssen fortlaufend vergeben werden.
    """
    
    def __init__(self, prefix: str = ""):
        """
        Initialisiert den Prüfer.
        
        Args:
            prefix: Optionaler Präfix vor der Nummer (z.B. "RE-")
        """
        self.prefix = prefix
    
    def pruefe_fortlaufend(self, rechnungsnummern: List[str]) -> Dict[str, Any]:
        """
        Prüft ob Rechnungsnummern fortlaufend sind.
        
        Args:
            rechnungsnummern: Liste von Rechnungsnummern
            
        Returns:
            Ergebnis mit Lücken und Dopplungen
        """
        if not rechnungsnummern:
            return {
                'ist_fortlaufend': True,
                'luecken': [],
                'doppelte': [],
                'warnungen': [],
            }
        
        # Nummern extrahieren
        nummern = []
        for nr in rechnungsnummern:
            num = self._extrahiere_nummer(nr)
            if num is not None:
                nummern.append((nr, num))
        
        # Sortieren nach Nummer
        nummern.sort(key=lambda x: x[1])
        
        luecken = []
        doppelte = []
        warnungen = []
        
        # Doppelte prüfen
        gesehen = {}
        for original, num in nummern:
            if num in gesehen:
                doppelte.append(original)
                warnungen.append(f"Doppelte Rechnungsnummer: {original}")
            gesehen[num] = original
        
        # Lücken prüfen
        if len(nummern) > 1:
            for i in range(1, len(nummern)):
                vorherige_num = nummern[i-1][1]
                aktuelle_num = nummern[i][1]
                
                if aktuelle_num - vorherige_num > 1:
                    # Lücke gefunden
                    for fehlende in range(vorherige_num + 1, aktuelle_num):
                        luecken.append(f"{self.prefix}{fehlende:03d}")
                    warnungen.append(
                        f"Lücke zwischen {nummern[i-1][0]} und {nummern[i][0]}"
                    )
        
        ist_fortlaufend = len(luecken) == 0 and len(doppelte) == 0
        
        return {
            'ist_fortlaufend': ist_fortlaufend,
            'luecken': luecken,
            'doppelte': doppelte,
            'warnungen': warnungen,
        }
    
    def _extrahiere_nummer(self, rechnungsnr: str) -> Optional[int]:
        """Extrahiert die numerische Komponente einer Rechnungsnummer"""
        # Entferne Präfix
        if self.prefix and rechnungsnr.startswith(self.prefix):
            num_str = rechnungsnr[len(self.prefix):]
        else:
            # Versuche Ziffern am Ende zu finden
            match = re.search(r'(\d+)$', rechnungsnr)
            if match:
                num_str = match.group(1)
            else:
                return None
        
        try:
            return int(num_str)
        except ValueError:
            return None
    
    def generiere_vorschlag(self, letzte_nummer: str, inkrement: int = 1) -> str:
        """
        Generiert einen Vorschlag für die nächste Rechnungsnummer.
        
        Args:
            letzte_nummer: Die letzte verwendete Nummer
            inkrement: Um wie viel erhöht werden soll
            
        Returns:
            Nächste Rechnungsnummer
        """
        num = self._extrahiere_nummer(letzte_nummer)
        if num is None:
            return f"{self.prefix}001"
        
        return f"{self.prefix}{num + inkrement:03d}"


def quick_check(rechnung_dict: Dict[str, Any]) -> PruefErgebnis:
    """
    Schnelle Prüfung einer Rechnung aus Dictionary.
    
    Args:
        rechnung_dict: Dictionary mit Rechnungsdaten
        
    Returns:
        PruefErgebnis
    """
    checker = GoBDChecker()
    
    # Positionen konvertieren
    positionen = [
        Rechnungsposition(
            bezeichnung=p.get('bezeichnung', ''),
            menge=p.get('menge', 0),
            preis=p.get('preis', 0),
            steuersatz=p.get('steuersatz', 19),
            einheit=p.get('einheit', 'Stk'),
        )
        for p in rechnung_dict.get('positionen', [])
    ]
    
    rechnung = Rechnung(
        rechnungsnr=rechnung_dict.get('rechnungsnr', ''),
        ausstellungsdatum=rechnung_dict.get('ausstellungsdatum', ''),
        lieferdatum=rechnung_dict.get('lieferdatum', ''),
        steller_name=rechnung_dict.get('steller_name', ''),
        steller_anschrift=rechnung_dict.get('steller_anschrift', ''),
        steller_ustid=rechnung_dict.get('steller_ustid'),
        steller_steuernummer=rechnung_dict.get('steller_steuernummer'),
        empfaenger_name=rechnung_dict.get('empfaenger_name', ''),
        empfaenger_anschrift=rechnung_dict.get('empfaenger_anschrift', ''),
        positionen=positionen,
        waehrung=rechnung_dict.get('waehrung', 'EUR'),
    )
    
    return checker.pruefe_rechnung(rechnung)
