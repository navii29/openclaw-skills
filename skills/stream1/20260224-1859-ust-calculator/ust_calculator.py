"""
German VAT (USt) Calculator
Berechnet USt für deutsche Steuersätze (19%, 7%, 0%)

Fokus: German Tax, E-Commerce, Invoicing
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum


class UStSatz(Enum):
    """Deutsche USt-Sätze"""
    VOLL = 19.0
    ERMÄSSIGT = 7.0
    NULL = 0.0


@dataclass
class UStBerechnung:
    """Ergebnis einer USt-Berechnung"""
    netto: float
    steuersatz: float
    ust_betrag: float
    brutto: float
    steuerkategorie: str


class UStCalculator:
    """
    Berechnet deutsche Umsatzsteuer
    
    Unterstützt:
    - 19% (Regelsatz)
    - 7% (ermäßigter Satz)
    - 0% (steuerfrei)
    
    Brutto/Netto-Umrechnung in beide Richtungen
    """
    
    # Steuersätze mit Beschreibung
    STEUER_SAETZE = {
        19.0: {'name': 'Regelsatz', 'beschreibung': 'Standard (19%)'},
        7.0: {'name': 'Ermäßigt', 'beschreibung': 'Ermäßigter Satz (7%)'},
        0.0: {'name': 'Null', 'beschreibung': 'Steuerfrei (0%)'}
    }
    
    # Gültige USt-Schlüssel (DATEV)
    UST_SCHLUESSEL = {
        '1': {'satz': 19.0, 'typ': 'Voll'},
        '2': {'satz': 7.0, 'typ': 'Ermäßigt'},
        '3': {'satz': 0.0, 'typ': 'Steuerfrei'},
        '4': {'satz': 19.0, 'typ': 'Voll (IG Erwerb)'},
        '5': {'satz': 7.0, 'typ': 'Ermäßigt (IG Erwerb)'},
    }
    
    def __init__(self, rundung: int = 2):
        """
        Args:
            rundung: Anzahl Nachkommastellen (default: 2)
        """
        self.rundung = rundung
    
    def netto_zu_brutto(self, netto: float, steuersatz: float = 19.0) -> UStBerechnung:
        """
        Berechnet Brutto aus Netto
        
        Args:
            netto: Nettobetrag
            steuersatz: Steuersatz in Prozent (default: 19%)
        
        Returns:
            UStBerechnung mit allen Werten
        """
        ust_betrag = round(netto * (steuersatz / 100), self.rundung)
        brutto = round(netto + ust_betrag, self.rundung)
        
        kategorie = self.STEUER_SAETZE.get(steuersatz, {}).get('name', 'Unbekannt')
        
        return UStBerechnung(
            netto=netto,
            steuersatz=steuersatz,
            ust_betrag=ust_betrag,
            brutto=brutto,
            steuerkategorie=kategorie
        )
    
    def brutto_zu_netto(self, brutto: float, steuersatz: float = 19.0) -> UStBerechnung:
        """
        Berechnet Netto aus Brutto (Brutto-Entschlüsselung)
        
        Formel: Netto = Brutto / (1 + Steuersatz/100)
        """
        faktor = 1 + (steuersatz / 100)
        netto = round(brutto / faktor, self.rundung)
        ust_betrag = round(brutto - netto, self.rundung)
        
        kategorie = self.STEUER_SAETZE.get(steuersatz, {}).get('name', 'Unbekannt')
        
        return UStBerechnung(
            netto=netto,
            steuersatz=steuersatz,
            ust_betrag=ust_betrag,
            brutto=brutto,
            steuerkategorie=kategorie
        )
    
    def skonto_berechnen(self, brutto: float, skonto_prozent: float, 
                         steuersatz: float = 19.0) -> Dict:
        """
        Berechnet Skonto auf Brutto-Betrag
        
        Args:
            brutto: Bruttobetrag
            skonto_prozent: Skonto-Satz (z.B. 2 für 2%)
            steuersatz: USt-Satz
        """
        skonto_betrag = round(brutto * (skonto_prozent / 100), self.rundung)
        zahlungsbetrag = round(brutto - skonto_betrag, self.rundung)
        
        # Skonto betrifft auch USt
        netto_brutto = self.brutto_zu_netto(brutto, steuersatz)
        skonto_netto = round(netto_brutto.netto * (skonto_prozent / 100), self.rundung)
        skonto_ust = round(skonto_betrag - skonto_netto, self.rundung)
        
        return {
            'brutto': brutto,
            'skonto_prozent': skonto_prozent,
            'skonto_betrag': skonto_betrag,
            'zahlungsbetrag': zahlungsbetrag,
            'skonto_netto': skonto_netto,
            'skonto_ust': skonto_ust
        }
    
    def mehrwertsteuer_differenz(self, netto_a: float, netto_b: float,
                                  steuersatz: float = 19.0) -> Dict:
        """
        Berechnet USt-Differenz zwischen zwei Netto-Beträgen
        """
        diff_netto = round(netto_b - netto_a, self.rundung)
        diff_ust = round(diff_netto * (steuersatz / 100), self.rundung)
        
        return {
            'differenz_netto': diff_netto,
            'differenz_ust': diff_ust,
            'steuersatz': steuersatz
        }
    
    def rabatt_berechnen(self, original_netto: float, rabatt_prozent: float,
                         steuersatz: float = 19.0) -> Dict:
        """
        Berechnet Rabatt auf Netto-Basis (B2B-Standard)
        
        Der Rabatt wird vom Netto abgezogen, dann USt berechnet
        """
        rabatt_netto = round(original_netto * (rabatt_prozent / 100), self.rundung)
        netto_nach_rabatt = round(original_netto - rabatt_netto, self.rundung)
        
        # USt auf reduzierten Betrag
        ust = round(netto_nach_rabatt * (steuersatz / 100), self.rundung)
        brutto = round(netto_nach_rabatt + ust, self.rundung)
        
        return {
            'original_netto': original_netto,
            'rabatt_prozent': rabatt_prozent,
            'rabatt_betrag': rabatt_netto,
            'netto_nach_rabatt': netto_nach_rabatt,
            'ust': ust,
            'brutto': brutto,
            'ersparnis': rabatt_netto
        }
    
    def get_steuer_satz_für_produkt(self, produkt_kategorie: str) -> float:
        """
        Gibt den Steuersatz für eine Produktkategorie zurück
        
        Args:
            produkt_kategorie: z.B. 'lebensmittel', 'buecher', 'standard'
        """
        kategorie_map = {
            'standard': 19.0,
            'default': 19.0,
            'lebensmittel': 7.0,
            'buecher': 7.0,
            'zeitungen': 7.0,
            'zeitschriften': 7.0,
            'kultur': 7.0,
            'hotels': 7.0,
            'medizin': 7.0,
            'steuerfrei': 0.0,
            'export': 0.0,
            'innergemeinschaftlich': 0.0
        }
        
        return kategorie_map.get(produkt_kategorie.lower(), 19.0)
    
    def format_euro(self, betrag: float) -> str:
        """Formatiert Betrag als Euro-String"""
        return f"{betrag:,.2f} €".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    def rechnungsposition(self, menge: float, einzelpreis_netto: float,
                          steuersatz: float = 19.0, rabatt_prozent: float = 0.0) -> Dict:
        """
        Berechnet eine komplette Rechnungsposition
        """
        gesamt_netto = round(menge * einzelpreis_netto, self.rundung)
        
        # Rabatt abziehen
        if rabatt_prozent > 0:
            rabatt_betrag = round(gesamt_netto * (rabatt_prozent / 100), self.rundung)
            netto_nach_rabatt = round(gesamt_netto - rabatt_betrag, self.rundung)
        else:
            rabatt_betrag = 0.0
            netto_nach_rabatt = gesamt_netto
        
        # USt berechnen
        ust = round(netto_nach_rabatt * (steuersatz / 100), self.rundung)
        brutto = round(netto_nach_rabatt + ust, self.rundung)
        
        return {
            'menge': menge,
            'einzelpreis_netto': einzelpreis_netto,
            'gesamt_netto': gesamt_netto,
            'rabatt_prozent': rabatt_prozent,
            'rabatt_betrag': rabatt_betrag,
            'netto_nach_rabatt': netto_nach_rabatt,
            'steuersatz': steuersatz,
            'ust_betrag': ust,
            'gesamt_brutto': brutto
        }


def calculate_vat(net_amount: float = None, gross_amount: float = None,
                  vat_rate: float = 19.0) -> Dict:
    """
    Schnell-Berechnung der USt
    
    Entweder net_amount ODER gross_amount angeben!
    
    Usage:
        # Netto zu Brutto
        result = calculate_vat(net_amount=100, vat_rate=19)
        
        # Brutto zu Netto
        result = calculate_vat(gross_amount=119, vat_rate=19)
    """
    calc = UStCalculator()
    
    if net_amount is not None:
        result = calc.netto_zu_brutto(net_amount, vat_rate)
    elif gross_amount is not None:
        result = calc.brutto_zu_netto(gross_amount, vat_rate)
    else:
        raise ValueError("Entweder net_amount oder gross_amount angeben")
    
    return {
        'netto': result.netto,
        'steuersatz': result.steuersatz,
        'ust_betrag': result.ust_betrag,
        'brutto': result.brutto,
        'kategorie': result.steuerkategorie
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ust_calculator.py <command> [args]")
        print("\nCommands:")
        print("  netto-zu-brutto <betrag> [satz]  - Netto zu Brutto")
        print("  brutto-zu-netto <betrag> [satz]  - Brutto zu Netto")
        print("  skonto <brutto> <skonto%>       - Skonto berechnen")
        print("  rabatt <netto> <rabatt%>         - Rabatt berechnen")
        print("  position <menge> <preis> [satz]  - Rechnungsposition")
        print("\nBeispiele:")
        print("  python ust_calculator.py netto-zu-brutto 100")
        print("  python ust_calculator.py netto-zu-brutto 100 7")
        print("  python ust_calculator.py skonto 119 2")
        print("  python ust_calculator.py position 5 19.99")
        sys.exit(1)
    
    command = sys.argv[1]
    calc = UStCalculator()
    
    if command == "netto-zu-brutto":
        if len(sys.argv) < 3:
            print("❌ Fehler: Betrag angeben")
            sys.exit(1)
        
        netto = float(sys.argv[2])
        satz = float(sys.argv[3]) if len(sys.argv) > 3 else 19.0
        
        result = calc.netto_zu_brutto(netto, satz)
        
        print(f"💰 Netto → Brutto ({satz}% USt)")
        print("-" * 50)
        print(f"Nettobetrag:   {calc.format_euro(result.netto)}")
        print(f"USt ({satz}%):    {calc.format_euro(result.ust_betrag)}")
        print("-" * 50)
        print(f"Bruttobetrag:  {calc.format_euro(result.brutto)}")
    
    elif command == "brutto-zu-netto":
        if len(sys.argv) < 3:
            print("❌ Fehler: Betrag angeben")
            sys.exit(1)
        
        brutto = float(sys.argv[2])
        satz = float(sys.argv[3]) if len(sys.argv) > 3 else 19.0
        
        result = calc.brutto_zu_netto(brutto, satz)
        
        print(f"💰 Brutto → Netto ({satz}% USt)")
        print("-" * 50)
        print(f"Bruttobetrag:  {calc.format_euro(result.brutto)}")
        print(f"USt ({satz}%):    {calc.format_euro(result.ust_betrag)}")
        print("-" * 50)
        print(f"Nettobetrag:   {calc.format_euro(result.netto)}")
    
    elif command == "skonto":
        if len(sys.argv) < 4:
            print("❌ Fehler: Brutto-Betrag und Skonto-% angeben")
            sys.exit(1)
        
        brutto = float(sys.argv[2])
        skonto = float(sys.argv[3])
        
        result = calc.skonto_berechnen(brutto, skonto)
        
        print(f"💰 Skonto-Berechnung ({skonto}%)")
        print("-" * 50)
        print(f"Bruttobetrag:   {calc.format_euro(result['brutto'])}")
        print(f"Skonto ({skonto}%):  -{calc.format_euro(result['skonto_betrag'])}")
        print("-" * 50)
        print(f"Zahlungsbetrag: {calc.format_euro(result['zahlungsbetrag'])}")
    
    elif command == "rabatt":
        if len(sys.argv) < 4:
            print("❌ Fehler: Netto-Betrag und Rabatt-% angeben")
            sys.exit(1)
        
        netto = float(sys.argv[2])
        rabatt = float(sys.argv[3])
        satz = float(sys.argv[4]) if len(sys.argv) > 4 else 19.0
        
        result = calc.rabatt_berechnen(netto, rabatt, satz)
        
        print(f"💰 Rabatt-Berechnung ({rabatt}%)")
        print("-" * 50)
        print(f"Original Netto:    {calc.format_euro(result['original_netto'])}")
        print(f"Rabatt ({rabatt}%):     -{calc.format_euro(result['rabatt_betrag'])}")
        print(f"Netto nach Rabatt: {calc.format_euro(result['netto_nach_rabatt'])}")
        print(f"USt ({satz}%):         {calc.format_euro(result['ust'])}")
        print("-" * 50)
        print(f"Brutto:            {calc.format_euro(result['brutto'])}")
    
    elif command == "position":
        if len(sys.argv) < 4:
            print("❌ Fehler: Menge und Einzelpreis angeben")
            sys.exit(1)
        
        menge = float(sys.argv[2])
        preis = float(sys.argv[3])
        satz = float(sys.argv[4]) if len(sys.argv) > 4 else 19.0
        
        result = calc.rechnungsposition(menge, preis, satz)
        
        print(f"📋 Rechnungsposition ({menge} × {calc.format_euro(preis)})")
        print("-" * 50)
        print(f"Gesamt Netto:   {calc.format_euro(result['gesamt_netto'])}")
        print(f"USt ({satz}%):      {calc.format_euro(result['ust_betrag'])}")
        print("-" * 50)
        print(f"Gesamt Brutto:  {calc.format_euro(result['gesamt_brutto'])}")
    
    else:
        print(f"❌ Unbekannter Befehl: {command}")
