"""
Rechnungs-Matching

Automatisches Matching von Zahlungen zu offenen Rechnungen.
Optimiert für DATEV-Export und deutsche Buchhaltungsstandards.
"""

import csv
import re
import json
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP


class MatchingError(Exception):
    """Allgemeiner Matching-Fehler"""
    pass


class DuplicatePaymentError(MatchingError):
    """Doppelte Zahlung erkannt"""
    pass


class InvalidFormatError(MatchingError):
    """Ungültiges CSV-Format"""
    pass


class ToleranzUeberschrittenError(MatchingError):
    """Betrag außerhalb Toleranz"""
    pass


@dataclass
class Rechnung:
    """Repräsentiert eine offene Rechnung"""
    nr: str
    kunde_id: str
    betrag: Decimal
    datum: str
    faellig: Optional[str] = None
    waehrung: str = "EUR"
    bezahlt: Decimal = field(default_factory=lambda: Decimal("0.00"))
    status: str = "offen"  # offen, teilbezahlt, bezahlt
    
    def __post_init__(self):
        if isinstance(self.betrag, (int, float, str)):
            self.betrag = Decimal(str(self.betrag)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if isinstance(self.bezahlt, (int, float, str)):
            self.bezahlt = Decimal(str(self.bezahlt)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    @property
    def restbetrag(self) -> Decimal:
        """Verbleibender offener Betrag"""
        return self.betrag - self.bezahlt
    
    @property
    def ist_teilbezahlt(self) -> bool:
        """Ist die Rechnung teilweise bezahlt?"""
        return self.bezahlt > 0 and self.bezahlt < self.betrag
    
    def zahlung_hinzufuegen(self, betrag: Decimal) -> None:
        """Fügt eine Zahlung zur Rechnung hinzu"""
        self.bezahlt += betrag
        if self.bezahlt >= self.betrag:
            self.status = "bezahlt"
        elif self.bezahlt > 0:
            self.status = "teilbezahlt"


@dataclass
class Zahlung:
    """Repräsentiert eine Zahlung (Bankumsatz)"""
    datum: str
    betrag: Decimal
    zweck: str = ""
    referenz: str = ""
    kunde_id: Optional[str] = None
    gematcht: bool = False
    rechnung_nr: Optional[str] = None
    
    def __post_init__(self):
        if isinstance(self.betrag, (int, float, str)):
            self.betrag = Decimal(str(self.betrag)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    def extrahiere_rechnungsnr(self) -> Optional[str]:
        """Extrahiert Rechnungsnummer aus Verwendungszweck"""
        # Muster: RE-001, Rechnung 123, Rnr: 456, etc.
        patterns = [
            r'RE-?(\d+)',           # RE-001, RE001
            r'Rechnung[:\s]+(\d+)', # Rechnung: 001
            r'Rnr[:\s]+(\d+)',      # Rnr: 001
            r'Rg[:\s]+(\d+)',       # Rg: 001
            r'Inv[:\s]+(\d+)',      # Inv: 001
        ]
        
        text = f"{self.zweck} {self.referenz}"
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None
    
    def extrahiere_kundenid(self) -> Optional[str]:
        """Extrahiert Kunden-ID aus Verwendungszweck"""
        # Muster: K001, Kd-Nr: 123, etc.
        patterns = [
            r'K(\d{3,})',           # K001
            r'Kd[-]?Nr[:\s]+(\d+)', # Kd-Nr: 001
            r'Kunde[:\s]+(\d+)',    # Kunde: 001
        ]
        
        text = f"{self.zweck} {self.referenz}"
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None


@dataclass
class MatchErgebnis:
    """Ergebnis eines Matchings"""
    rechnung: Rechnung
    zahlung: Zahlung
    methode: str  # 'exakt', 'fuzzy', 'referenz', 'teil'
    differenz: Decimal
    vertrauen: float  # 0.0 - 1.0


class InvoiceMatcher:
    """
    Matcher für Rechnungen und Zahlungen.
    
    Unterstützt:
    - Exaktes Matching (Betrag + Referenz)
    - Fuzzy Matching (Betrag mit Toleranz)
    - Teilzahlungen
    - Mehrfachzahlungen
    """
    
    def __init__(
        self,
        toleranz_prozent: float = 1.0,
        toleranz_absolut: float = 5.0,
        datum_toleranz_tage: int = 5
    ):
        """
        Initialisiert den Matcher.
        
        Args:
            toleranz_prozent: Prozentuale Toleranz für Beträge (z.B. 1.0 = 1%)
            toleranz_absolut: Absolute Toleranz in EUR (z.B. 5.0 = ±5 EUR)
            datum_toleranz_tage: Toleranz für Datumsabweichung
        """
        self.toleranz_prozent = toleranz_prozent
        self.toleranz_absolut = toleranz_absolut
        self.datum_toleranz_tage = datum_toleranz_tage
        
        self.rechnungen: List[Rechnung] = []
        self.zahlungen: List[Zahlung] = []
        self.matches: List[MatchErgebnis] = []
        self.unmatched_zahlungen: List[Zahlung] = []
        self.doppelte_zahlungen: List[Zahlung] = []
    
    def lade_rechnungen(self, rechnungen: List[Dict]) -> None:
        """
        Lädt Rechnungen aus Dictionary-Liste.
        
        Args:
            rechnungen: Liste von Dicts mit 'nr', 'kunde_id', 'betrag', etc.
        """
        self.rechnungen = []
        for r in rechnungen:
            try:
                rechnung = Rechnung(
                    nr=str(r.get('nr', r.get('Rechnungsnr', ''))),
                    kunde_id=str(r.get('kunde_id', r.get('Kundennummer', ''))),
                    betrag=r.get('betrag', r.get('Betrag', 0)),
                    datum=str(r.get('datum', r.get('Datum', ''))),
                    faellig=str(r.get('faellig', r.get('Faellig', ''))) if r.get('faellig', r.get('Faellig')) else None,
                    waehrung=str(r.get('waehrung', r.get('Waehrung', 'EUR'))),
                )
                self.rechnungen.append(rechnung)
            except (ValueError, TypeError, Exception) as e:
                raise InvalidFormatError(f"Ungültiges Rechnungsformat: {r} - {e}")
    
    def lade_rechnungen_csv(self, csv_path: str, encoding: str = 'utf-8') -> None:
        """Lädt Rechnungen aus CSV-Datei"""
        rechnungen = []
        with open(csv_path, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                rechnungen.append(row)
        self.lade_rechnungen(rechnungen)
    
    def lade_zahlungen(self, zahlungen: List[Dict]) -> None:
        """
        Lädt Zahlungen aus Dictionary-Liste.
        
        Args:
            zahlungen: Liste von Dicts mit 'datum', 'betrag', 'zweck', etc.
        """
        self.zahlungen = []
        for z in zahlungen:
            try:
                zahlung = Zahlung(
                    datum=str(z.get('datum', z.get('Datum', ''))),
                    betrag=z.get('betrag', z.get('Betrag', 0)),
                    zweck=str(z.get('zweck', z.get('Zweck', ''))),
                    referenz=str(z.get('referenz', z.get('Referenz', ''))),
                    kunde_id=str(z.get('kunde_id', z.get('Kundennummer', ''))) if z.get('kunde_id', z.get('Kundennummer')) else None,
                )
                self.zahlungen.append(zahlung)
            except (ValueError, TypeError, Exception) as e:
                raise InvalidFormatError(f"Ungültiges Zahlungsformat: {z} - {e}")
    
    def lade_zahlungen_csv(self, csv_path: str, encoding: str = 'utf-8') -> None:
        """Lädt Zahlungen aus CSV-Datei"""
        zahlungen = []
        with open(csv_path, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                zahlungen.append(row)
        self.lade_zahlungen(zahlungen)
    
    def match(self) -> Dict[str, Any]:
        """
        Führt das Matching durch.
        
        Returns:
            Dict mit matches, unmatched_zahlungen, stats
        """
        self.matches = []
        self.unmatched_zahlungen = []
        self.doppelte_zahlungen = []
        
        # Doppelte Zahlungen erkennen (gleicher Betrag + gleicher Zweck)
        zahlung_schluessel = {}
        for z in self.zahlungen:
            schluessel = (str(z.betrag), z.zweck.strip().lower())
            if schluessel in zahlung_schluessel:
                self.doppelte_zahlungen.append(z)
            else:
                zahlung_schluessel[schluessel] = z
        
        # Matching durchführen
        for zahlung in self.zahlungen:
            if zahlung in self.doppelte_zahlungen:
                continue
            
            match = self._finde_besten_match(zahlung)
            if match:
                self.matches.append(match)
                match.rechnung.zahlung_hinzufuegen(match.zahlung.betrag)
                zahlung.gematcht = True
                zahlung.rechnung_nr = match.rechnung.nr
            else:
                self.unmatched_zahlungen.append(zahlung)
        
        return self._build_ergebnis()
    
    def _finde_besten_match(self, zahlung: Zahlung) -> Optional[MatchErgebnis]:
        """Findet den besten Match für eine Zahlung"""
        beste_matches = []
        
        # Extrahiere Referenzen aus Zahlung
        rechnungsnr = zahlung.extrahiere_rechnungsnr()
        kundenid = zahlung.extrahiere_kundenid()
        
        for rechnung in self.rechnungen:
            # Nur offene Rechnungen betrachten
            if rechnung.status == "bezahlt":
                continue
            
            # Methode 1: Exaktes Matching (Rechnungsnummer + Betrag)
            if rechnungsnr and rechnungsnr.lower() in rechnung.nr.lower():
                if self._betrage_stimmen_ueberein(zahlung.betrag, rechnung.restbetrag):
                    return MatchErgebnis(
                        rechnung=rechnung,
                        zahlung=zahlung,
                        methode='exakt_referenz',
                        differenz=Decimal("0.00"),
                        vertrauen=1.0
                    )
            
            # Methode 2: Kunden-ID + Betrag
            if kundenid and kundenid.lower() in rechnung.kunde_id.lower():
                if self._betrage_stimmen_ueberein(zahlung.betrag, rechnung.restbetrag):
                    beste_matches.append(MatchErgebnis(
                        rechnung=rechnung,
                        zahlung=zahlung,
                        methode='kunde_betrag',
                        differenz=abs(zahlung.betrag - rechnung.restbetrag),
                        vertrauen=0.9
                    ))
            
            # Methode 3: Fuzzy Matching (nur Betrag)
            if self._betrage_stimmen_ueberein(zahlung.betrag, rechnung.restbetrag):
                beste_matches.append(MatchErgebnis(
                    rechnung=rechnung,
                    zahlung=zahlung,
                    methode='fuzzy_betrag',
                    differenz=abs(zahlung.betrag - rechnung.restbetrag),
                    vertrauen=0.7
                ))
            
            # Methode 4: Teilzahlung
            if zahlung.betrag < rechnung.restbetrag and zahlung.betrag > 0:
                if rechnung.ist_teilbezahlt or self._betrage_in_toleranz(zahlung.betrag, rechnung.restbetrag * Decimal("0.5")):
                    beste_matches.append(MatchErgebnis(
                        rechnung=rechnung,
                        zahlung=zahlung,
                        methode='teilzahlung',
                        differenz=rechnung.restbetrag - zahlung.betrag,
                        vertrauen=0.5
                    ))
        
        # Besten Match auswählen (höchstes Vertrauen)
        if beste_matches:
            return max(beste_matches, key=lambda m: m.vertrauen)
        
        return None
    
    def _betrage_stimmen_ueberein(self, betrag1: Decimal, betrag2: Decimal) -> bool:
        """Prüft ob zwei Beträge übereinstimmen (mit Toleranz)"""
        return self._betrage_in_toleranz(betrag1, betrag2)
    
    def _betrage_in_toleranz(self, betrag1: Decimal, betrag2: Decimal) -> bool:
        """Prüft ob Betrag innerhalb Toleranz liegt"""
        differenz = abs(betrag1 - betrag2)
        prozent_toleranz = betrag2 * Decimal(str(self.toleranz_prozent / 100))
        
        return differenz <= Decimal(str(self.toleranz_absolut)) or differenz <= prozent_toleranz
    
    def _build_ergebnis(self) -> Dict[str, Any]:
        """Baut das Ergebnis-Dictionary"""
        total_zahlungen = len(self.zahlungen)
        gematchte_zahlungen = len(self.matches)
        unmatched_count = len(self.unmatched_zahlungen)
        doppelte_count = len(self.doppelte_zahlungen)
        
        return {
            'matches': self.matches,
            'unmatched_zahlungen': self.unmatched_zahlungen,
            'doppelte_zahlungen': self.doppelte_zahlungen,
            'stats': {
                'total_rechnungen': len(self.rechnungen),
                'total_zahlungen': total_zahlungen,
                'gematcht': gematchte_zahlungen,
                'unmatched': unmatched_count,
                'doppelte': doppelte_count,
                'match_rate': gematchte_zahlungen / total_zahlungen if total_zahlungen > 0 else 0,
            }
        }
    
    def get_offene_posten(self) -> List[Rechnung]:
        """Gibt alle noch offenen Rechnungen zurück"""
        return [r for r in self.rechnungen if r.status != "bezahlt"]
    
    def get_bericht(self) -> str:
        """Gibt einen Text-Bericht zurück"""
        ergebnis = self._build_ergebnis()
        stats = ergebnis['stats']
        
        lines = [
            "=" * 60,
            "MATCHING-BERICHT",
            "=" * 60,
            f"Rechnungen gesamt: {stats['total_rechnungen']}",
            f"Zahlungen gesamt:  {stats['total_zahlungen']}",
            f"Erfolgreich gematcht: {stats['gematcht']} ({stats['match_rate']*100:.1f}%)",
            f"Unmatched: {stats['unmatched']}",
            f"Doppelte Zahlungen: {stats['doppelte']}",
            "-" * 60,
        ]
        
        if self.matches:
            lines.append("\nGEMATCHTE ZAHLUNGEN:")
            for m in self.matches:
                lines.append(f"  {m.zahlung.datum} | {m.zahlung.betrag:>10} EUR | {m.methode:<15} | {m.rechnung.nr}")
        
        if self.unmatched_zahlungen:
            lines.append("\nUNMATCHED ZAHLUNGEN:")
            for z in self.unmatched_zahlungen:
                lines.append(f"  {z.datum} | {z.betrag:>10} EUR | {z.zweck[:40]}")
        
        if self.doppelte_zahlungen:
            lines.append("\nDOPPELTE ZAHLUNGEN (Warnung!):")
            for z in self.doppelte_zahlungen:
                lines.append(f"  {z.datum} | {z.betrag:>10} EUR | {z.zweck[:40]}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)


class DATEVExporter:
    """
    Exportiert Matching-Ergebnisse im DATEV-Standardformat.
    """
    
    # Standardkonten für DATEV (SKR03)
    KONTEN = {
        'kasse': '1000',
        'bank': '1200',
        'ford_kunden': '1400',
        'erloese_19': '8400',
        'erloese_7': '8300',
        'ust_19': '1776',
        'ust_7': '1775',
    }
    
    def __init__(self, kontenrahmen: str = 'SKR03'):
        """
        Initialisiert den Exporter.
        
        Args:
            kontenrahmen: 'SKR03' oder 'SKR04'
        """
        self.kontenrahmen = kontenrahmen
    
    def export_csv(
        self,
        ergebnis: Dict[str, Any],
        output_path: str,
        konto_bank: str = '1200',
        konto_erloese: str = '8400'
    ) -> str:
        """
        Exportiert gematchte Zahlungen als DATEV-CSV.
        
        Args:
            ergebnis: Ergebnis vom InvoiceMatcher.match()
            output_path: Pfad zur Ausgabedatei
            konto_bank: Bankkonto (Soll)
            konto_erloese: Erlöskonto (Haben)
            
        Returns:
            Pfad zur erstellten Datei
        """
        matches = ergebnis.get('matches', [])
        
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_MINIMAL)
            
            # Header
            writer.writerow([
                'Datum', 'Konto', 'Gegenkonto', 'Buchungstext',
                'Umsatz Soll', 'Umsatz Haben', 'Belegnr'
            ])
            
            # Buchungssätze
            for match in matches:
                z = match.zahlung
                r = match.rechnung
                
                # Format: DD.MM.YYYY
                datum = self._format_datum(z.datum)
                
                writer.writerow([
                    datum,
                    konto_bank,
                    konto_erloese,
                    f"{r.nr} {r.kunde_id}",
                    str(z.betrag).replace('.', ','),
                    '',
                    r.nr,
                ])
        
        return output_path
    
    def export_offene_posten(
        self,
        rechnungen: List[Rechnung],
        output_path: str
    ) -> str:
        """Exportiert offene Posten als CSV"""
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow([
                'Rechnungsnr', 'Kunde', 'Betrag', 'Bezahlt',
                'Restbetrag', 'Status', 'Datum', 'Fällig'
            ])
            
            for r in rechnungen:
                writer.writerow([
                    r.nr,
                    r.kunde_id,
                    str(r.betrag).replace('.', ','),
                    str(r.bezahlt).replace('.', ','),
                    str(r.restbetrag).replace('.', ','),
                    r.status,
                    r.datum,
                    r.faellig or '',
                ])
        
        return output_path
    
    def _format_datum(self, datum: str) -> str:
        """Formatiert Datum als DD.MM.YYYY"""
        # Versuche verschiedene Formate
        for fmt in ['%Y-%m-%d', '%d.%m.%Y', '%d/%m/%Y']:
            try:
                d = datetime.strptime(datum, fmt)
                return d.strftime('%d.%m.%Y')
            except ValueError:
                continue
        return datum


def quick_match(
    rechnungen: List[Dict],
    zahlungen: List[Dict],
    toleranz_prozent: float = 1.0
) -> Dict[str, Any]:
    """
    Schnelles Matching ohne Instanziierung.
    
    Args:
        rechnungen: Liste von Rechnungs-Dicts
        zahlungen: Liste von Zahlungs-Dicts
        toleranz_prozent: Toleranz für Beträge
        
    Returns:
        Matching-Ergebnis
    """
    matcher = InvoiceMatcher(toleranz_prozent=toleranz_prozent)
    matcher.lade_rechnungen(rechnungen)
    matcher.lade_zahlungen(zahlungen)
    return matcher.match()
