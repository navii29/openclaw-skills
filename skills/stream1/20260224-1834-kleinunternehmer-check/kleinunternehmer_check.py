"""
Kleinunternehmer-Prüfung nach §19 UStG
Prüft die Einhaltung der Umsatzgrenzen für Kleinunternehmer

Fokus: German Tax Automation, E-Commerce
"""

from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import json


@dataclass
class Umsatz:
    """Einzelner Umsatz-Eintrag"""
    datum: date
    brutto: float
    netto: float
    steuer: float
    kategorie: str = ""
    notiz: str = ""


@dataclass
class KleinunternehmerStatus:
    """Status-Objekt für Kleinunternehmer-Prüfung"""
    ist_kleinunternehmer: bool
    begruendung: str
    umsatz_vorjahr: float
    umsatz_laufendes_jahr: float
    prognose_aktuelles_jahr: float
    grenzwert: float
    warnungen: List[str]
    handlungsempfehlung: str


class KleinunternehmerChecker:
    """
    Prüft §19 UStG Kleinunternehmer-Regelung
    
    Grenzen (2024/2025):
    - 22.000 € im Vorjahr
    - 50.000 € im laufenden Jahr (prognostiziert)
    """
    
    # Aktuelle Grenzwerte
    GRENZE_VORJAHR = 22_000  # €
    GRENZE_AKTUELL = 50_000  # €
    
    def __init__(self, grenze_vorjahr: float = None, grenze_aktuell: float = None):
        """
        Args:
            grenze_vorjahr: Individuelle Vorjahresgrenze (Standard: 22.000 €)
            grenze_aktuell: Individuelle Aktuellgrenze (Standard: 50.000 €)
        """
        self.grenze_vorjahr = grenze_vorjahr or self.GRENZE_VORJAHR
        self.grenze_aktuell = grenze_aktuell or self.GRENZE_AKTUELL
    
    def check_status(self, 
                     umsatz_vorjahr: float,
                     umsatz_laufendes_jahr: float,
                     aktuelles_datum: date = None) -> KleinunternehmerStatus:
        """
        Prüft den Kleinunternehmer-Status
        
        Args:
            umsatz_vorjahr: Gesamtumsatz des Vorjahres (brutto)
            umsatz_laufendes_jahr: Bisheriger Umsatz laufendes Jahr
            aktuelles_datum: Aktuelles Datum (default: heute)
        
        Returns:
            KleinunternehmerStatus mit Entscheidung
        """
        if aktuelles_datum is None:
            aktuelles_datum = date.today()
        
        warnungen = []
        
        # Prognose für laufendes Jahr
        prognose = self._berechne_prognose(umsatz_laufendes_jahr, aktuelles_datum)
        
        # Prüfung Vorjahresgrenze
        vorjahr_ok = umsatz_vorjahr <= self.grenze_vorjahr
        
        # Prüfung aktuelles Jahr
        aktuell_ok = prognose <= self.grenze_aktuell
        
        # Entscheidung
        ist_kleinunternehmer = vorjahr_ok and aktuell_ok
        
        # Warnungen
        if not vorjahr_ok:
            warnungen.append(f"Vorjahresumsatz ({umsatz_vorjahr:,.2f} €) über Grenze ({self.grenze_vorjahr:,.2f} €)")
        
        if not aktuell_ok:
            warnungen.append(f"Prognose ({prognose:,.2f} €) über Grenze ({self.grenze_aktuell:,.2f} €)")
        
        # Grenzwarnung (90% Grenze)
        if umsatz_laufendes_jahr > (self.grenze_aktuell * 0.9 * aktuelles_datum.timetuple().tm_yday / 365):
            warnungen.append("⚠️  ACHTUNG: Umsatz nähert sich der 50.000 €-Grenze!")
        
        # Begründung
        if ist_kleinunternehmer:
            begruendung = f"✅ Kleinunternehmer: Vorjahr {umsatz_vorjahr:,.2f} € ≤ {self.grenze_vorjahr:,.2f} €, Prognose {prognose:,.2f} € ≤ {self.grenze_aktuell:,.2f} €"
        else:
            gruende = []
            if not vorjahr_ok:
                gruende.append(f"Vorjahresumsatz zu hoch")
            if not aktuell_ok:
                gruende.append(f"Prognose über Grenze")
            begruendung = f"❌ Kein Kleinunternehmer: {', '.join(gruende)}"
        
        # Handlungsempfehlung
        handlung = self._get_handlungsempfehlung(ist_kleinunternehmer, vorjahr_ok, aktuell_ok, umsatz_laufendes_jahr)
        
        return KleinunternehmerStatus(
            ist_kleinunternehmer=ist_kleinunternehmer,
            begruendung=begruendung,
            umsatz_vorjahr=umsatz_vorjahr,
            umsatz_laufendes_jahr=umsatz_laufendes_jahr,
            prognose_aktuelles_jahr=prognose,
            grenzwert=self.grenze_aktuell,
            warnungen=warnungen,
            handlungsempfehlung=handlung
        )
    
    def _berechne_prognose(self, umsatz_bisher: float, datum: date) -> float:
        """
        Berechnet die Jahresprognose basierend auf bisherigem Umsatz
        """
        if umsatz_bisher == 0:
            return 0
        
        tag_im_jahr = datum.timetuple().tm_yday
        tage_gesamt = 366 if self._ist_schaltjahr(datum.year) else 365
        
        # Lineare Hochrechnung
        prognose = umsatz_bisher / tag_im_jahr * tage_gesamt
        return round(prognose, 2)
    
    def _ist_schaltjahr(self, jahr: int) -> bool:
        """Prüft ob Schaltjahr"""
        return (jahr % 4 == 0 and jahr % 100 != 0) or (jahr % 400 == 0)
    
    def _get_handlungsempfehlung(self, 
                                  ist_kleinunternehmer: bool,
                                  vorjahr_ok: bool,
                                  aktuell_ok: bool,
                                  umsatz_laufendes_jahr: float) -> str:
        """Erstellt Handlungsempfehlung"""
        if ist_kleinunternehmer:
            return "✅ USt nicht ausweisen, aber Hinweis 'Kleinunternehmer gem. §19 UStG' auf Rechnungen"
        
        if not vorjahr_ok and not aktuell_ok:
            return "⚠️  USt-Pflicht ab Januar! Regelmäßige USt-Voranmeldung prüfen, USt auf Rechnungen ausweisen"
        
        if not aktuell_ok:
            return "⚠️  USt-Pflicht tritt ein! Ab Überschreiten der 50.000 €-Grenze: USt ausweisen"
        
        return "⚠️  Steuerberater konsultieren"
    
    def check_monatsgrenze(self, monatlicher_durchschnitt: float) -> Dict:
        """
        Prüft ob monatlicher Durchschnitt die Grenzen gefährdet
        """
        prognose = monatlicher_durchschnitt * 12
        
        return {
            'monatlicher_durchschnitt': monatlicher_durchschnitt,
            'prognose_jahr': prognose,
            'grenze_erreicht': prognose > self.grenze_aktuell,
            'prozent_grenze': round(prognose / self.grenze_aktuell * 100, 1),
            'warnstufe': 'kritisch' if prognose > self.grenze_aktuell else 
                        'warnung' if prognose > self.grenze_aktuell * 0.8 else 'ok'
        }
    
    def calculate_rechnung(self, betrag: float, ist_kleinunternehmer: bool) -> Dict:
        """
        Berechnet Rechnungsbetrag mit/ohne USt
        
        Args:
            betrag: Netto-Betrag
            ist_kleinunternehmer: Aktueller Status
        """
        if ist_kleinunternehmer:
            return {
                'netto': betrag,
                'steuersatz': 0,
                'steuerbetrag': 0,
                'brutto': betrag,
                'hinweis': 'Kleinunternehmer gem. §19 UStG - keine USt ausgewiesen'
            }
        else:
            ust_19 = round(betrag * 0.19, 2)
            return {
                'netto': betrag,
                'steuersatz': 19,
                'steuerbetrag': ust_19,
                'brutto': round(betrag + ust_19, 2),
                'hinweis': '19% USt'
            }


def check_kleinunternehmer(umsatz_vorjahr: float, 
                           umsatz_aktuell: float,
                           datum: date = None) -> Dict:
    """
    Schnell-Prüfung Kleinunternehmer-Status
    
    Usage:
        result = check_kleinunternehmer(20000, 15000)
        result = check_kleinunternehmer(25000, 45000)
    """
    checker = KleinunternehmerChecker()
    status = checker.check_status(umsatz_vorjahr, umsatz_aktuell, datum)
    
    return {
        'ist_kleinunternehmer': status.ist_kleinunternehmer,
        'begruendung': status.begruendung,
        'umsatz_vorjahr': status.umsatz_vorjahr,
        'umsatz_aktuell': status.umsatz_laufendes_jahr,
        'prognose': status.prognose_aktuelles_jahr,
        'grenzwert': status.grenzwert,
        'warnungen': status.warnungen,
        'handlungsempfehlung': status.handlungsempfehlung
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python kleinunternehmer_check.py <Umsatz_Vorjahr> <Umsatz_aktuell>")
        print("\nBeispiele:")
        print("  python kleinunternehmer_check.py 20000 15000")
        print("  python kleinunternehmer_check.py 25000 40000")
        print("\nGrenzen (§19 UStG):")
        print("  - Vorjahr: max. 22.000 €")
        print("  - Aktuelles Jahr: max. 50.000 € (prognostiziert)")
        sys.exit(1)
    
    try:
        vorjahr = float(sys.argv[1])
        aktuell = float(sys.argv[2])
    except ValueError:
        print("❌ Fehler: Umsätze müssen Zahlen sein")
        sys.exit(1)
    
    print(f"🔍 Prüfe Kleinunternehmer-Status (§19 UStG)")
    print("-" * 60)
    print(f"Vorjahresumsatz: {vorjahr:,.2f} €")
    print(f"Aktueller Umsatz: {aktuell:,.2f} €")
    print("-" * 60)
    
    result = check_kleinunternehmer(vorjahr, aktuell)
    
    print(f"\n{'✅' if result['ist_kleinunternehmer'] else '❌'} Status: {'KLEINUNTERNEHMER' if result['ist_kleinunternehmer'] else 'KEIN KLEINUNTERNEHMER'}")
    print(f"\n📊 Prognose: {result['prognose']:,.2f} € (Grenze: {result['grenzwert']:,.2f} €)")
    
    if result['warnungen']:
        print(f"\n⚠️  Warnungen:")
        for w in result['warnungen']:
            print(f"   - {w}")
    
    print(f"\n📋 Handlungsempfehlung:")
    print(f"   {result['handlungsempfehlung']}")
