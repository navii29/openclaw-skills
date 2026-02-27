"""
ELSTER USt-Voranmeldung Helper

Generiert XML-Dateien für die elektronische USt-Voranmeldung
an das deutsche Finanzamt.

Unterstützte Kennzahlen:
- Kz 81: Umsatzsteuer 19%
- Kz 86: Umsatzsteuer 7%
- Kz 66: Vorsteuer
- Kz 63: Berichtigung Vorsteuer
"""

import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


class ElsterError(Exception):
    """Basis-Exception für ELSTER-Fehler"""
    pass


class InvalidSteuernummerError(ElsterError):
    """Ungültige Steuernummer"""
    pass


class InvalidZeitraumError(ElsterError):
    """Ungültiger Zeitraum (Monat/Jahr)"""
    pass


class InvalidBetragError(ElsterError):
    """Ungültiger Betrag"""
    pass


class XMLGenerationError(ElsterError):
    """Fehler bei der XML-Generierung"""
    pass


@dataclass
class UStVABetrage:
    """Datenklasse für USt-VA Beträge"""
    kz81: int = 0  # Umsatzsteuer 19%
    kz86: int = 0  # Umsatzsteuer 7%
    kz66: int = 0  # Vorsteuer
    kz63: int = 0  # Berichtigung Vorsteuer
    
    def validate(self) -> None:
        """Validiert alle Beträge"""
        for name, value in [
            ('kz81', self.kz81), ('kz86', self.kz86),
            ('kz66', self.kz66), ('kz63', self.kz63)
        ]:
            if not isinstance(value, (int, float)):
                raise InvalidBetragError(f"{name} muss eine Zahl sein")
            if value < 0:
                raise InvalidBetragError(f"{name} darf nicht negativ sein: {value}")
            if value > 99_999_999_999:  # Max 11 Stellen
                raise InvalidBetragError(f"{name} zu groß: {value}")
    
    @property
    def ust_gesamt(self) -> int:
        """Gesamte Umsatzsteuer (Kz 81 + 86)"""
        return self.kz81 + self.kz86
    
    @property
    def vorsteuer_gesamt(self) -> int:
        """Gesamte Vorsteuer (Kz 66 + 63)"""
        return self.kz66 + self.kz63
    
    @property
    def zahllast(self) -> int:
        """Zu zahlende USt (positiv = Zahlung, negativ = Erstattung)"""
        return self.ust_gesamt - self.vorsteuer_gesamt


class SteuernummerValidator:
    """Validiert deutsche Steuernummern"""
    
    # Bundeslaender und ihre Steuernummern-Formate
    BUNDESLAENDER_PRUEFZIFFERN = {
        '01': 11,  # Schleswig-Holstein
        '02': 10,  # Hamburg
        '03': 9,   # Niedersachsen
        '04': 9,   # Bremen
        '05': 9,   # Nordrhein-Westfalen
        '06': 9,   # Hessen
        '07': 10,  # Rheinland-Pfalz
        '08': 9,   # Baden-Württemberg
        '09': 9,   # Bayern
        '10': 7,   # Saarland
        '11': 11,  # Berlin
        '12': 8,   # Brandenburg
        '13': 8,   # Mecklenburg-Vorpommern
        '14': 9,   # Sachsen
        '15': 9,   # Sachsen-Anhalt
        '16': 9,   # Thüringen
    }
    
    def validate_national(self, steuernummer: str) -> bool:
        """
        Validiert eine 13-stellige deutsche Steuernummer.
        
        Args:
            steuernummer: 13-stellige Steuernummer (nur Ziffern)
            
        Returns:
            True wenn gültig
            
        Raises:
            InvalidSteuernummerError: Bei ungültiger Nummer
        """
        # Nur Ziffern extrahieren
        clean = re.sub(r'\D', '', steuernummer)
        
        if len(clean) != 13:
            raise InvalidSteuernummerError(
                f"Steuernummer muss 13 Stellen haben, hat {len(clean)}: {steuernummer}"
            )
        
        # Bundesland aus den ersten beiden Ziffern
        bundesland = clean[:2]
        if bundesland not in self.BUNDESLAENDER_PRUEFZIFFERN:
            raise InvalidSteuernummerError(
                f"Ungültiges Bundesland in Steuernummer: {bundesland}"
            )
        
        # Grundsätzliche Formatprüfung (ohne komplexe Prüfziffer)
        # Die tatsächliche Prüfziffernberechnung ist bundeslandspezifisch
        # und sehr komplex - wir machen eine Basisprüfung
        
        return True
    
    def validate_ust_idnr(self, ust_idnr: str) -> bool:
        """
        Validiert eine USt-IdNr (DE + 9 Ziffern).
        
        Args:
            ust_idnr: USt-IdNr (z.B. "DE123456789")
            
        Returns:
            True wenn gültig
            
        Raises:
            InvalidSteuernummerError: Bei ungültiger Nummer
        """
        clean = ust_idnr.upper().replace(' ', '')
        
        if not clean.startswith('DE'):
            raise InvalidSteuernummerError(
                f"Deutsche USt-IdNr muss mit 'DE' beginnen: {ust_idnr}"
            )
        
        ziffern = clean[2:]
        if len(ziffern) != 9:
            raise InvalidSteuernummerError(
                f"USt-IdNr braucht 9 Ziffern nach 'DE', hat {len(ziffern)}: {ust_idnr}"
            )
        
        if not ziffern.isdigit():
            raise InvalidSteuernummerError(
                f"USt-IdNr enthält ungültige Zeichen: {ust_idnr}"
            )
        
        return True
    
    def format_national(self, steuernummer: str) -> str:
        """
        Formatiert eine Steuernummer im ELSTER-Format (nur Ziffern).
        
        Args:
            steuernummer: Rohe Steuernummer
            
        Returns:
            Bereinigte 13-stellige Steuernummer
        """
        clean = re.sub(r'\D', '', steuernummer)
        
        if len(clean) < 13:
            # Führende Nullen ergänzen (z.B. für Hamburg)
            clean = clean.zfill(13)
        
        return clean


class UStVAGenerator:
    """
    Generator für ELSTER USt-Voranmeldung XML.
    
    Erstellt konforme XML-Dateien für die elektronische Übermittlung
    der Umsatzsteuer-Voranmeldung.
    """
    
    # XML Namespaces
    NS = {
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'elster': 'http://www.elster.de/elsterxml/schema/v11'
    }
    
    def __init__(
        self,
        steuernummer: str,
        finanzamt: str,
        name: str,
        berater_nr: Optional[str] = None,
        mandanten_nr: Optional[str] = None
    ):
        """
        Initialisiert den Generator.
        
        Args:
            steuernummer: 13-stellige Steuernummer
            finanzamt: Finanzamt-Nummer (4-stellig)
            name: Name des Steuerpflichtigen
            berater_nr: Optionale Beraternummer
            mandanten_nr: Optionale Mandantennummer
        """
        self.validator = SteuernummerValidator()
        
        try:
            self.validator.validate_national(steuernummer)
            self.steuernummer = self.validator.format_national(steuernummer)
        except InvalidSteuernummerError:
            raise
        
        if not finanzamt or len(finanzamt) > 4:
            raise ElsterError(f"Ungültige Finanzamt-Nummer: {finanzamt}")
        
        self.finanzamt = finanzamt
        self.name = name
        self.berater_nr = berater_nr
        self.mandanten_nr = mandanten_nr
    
    def create_voranmeldung(
        self,
        jahr: int,
        monat: int,
        kz81: int = 0,
        kz86: int = 0,
        kz66: int = 0,
        kz63: int = 0,
        erstellungsdatum: Optional[str] = None
    ) -> str:
        """
        Erstellt eine USt-Voranmeldung.
        
        Args:
            jahr: Jahr (z.B. 2024)
            monat: Monat (1-12)
            kz81: Betrag für Kennziffer 81 (USt 19%) in Cent/Euro
            kz86: Betrag für Kennziffer 86 (USt 7%) in Cent/Euro
            kz66: Betrag für Kennziffer 66 (Vorsteuer) in Cent/Euro
            kz63: Betrag für Kennziffer 63 (Berichtigung) in Cent/Euro
            erstellungsdatum: Optional ISO-Datum (YYYY-MM-DD)
            
        Returns:
            XML-String
            
        Raises:
            InvalidZeitraumError: Bei ungültigem Zeitraum
            InvalidBetragError: Bei ungültigen Beträgen
            XMLGenerationError: Bei XML-Fehlern
        """
        # Zeitraum validieren
        if not (1 <= monat <= 12):
            raise InvalidZeitraumError(f"Monat muss 1-12 sein: {monat}")
        
        current_year = datetime.now().year
        if not (2000 <= jahr <= current_year + 1):
            raise InvalidZeitraumError(f"Ungültiges Jahr: {jahr}")
        
        # Beträge validieren
        betrage = UStVABetrage(kz81=kz81, kz86=kz86, kz66=kz66, kz63=kz63)
        betrage.validate()
        
        # Erstellungsdatum
        if erstellungsdatum is None:
            erstellungsdatum = datetime.now().strftime('%Y-%m-%d')
        
        try:
            xml = self._generate_xml(jahr, monat, betrage, erstellungsdatum)
            return xml
        except Exception as e:
            raise XMLGenerationError(f"XML-Generierung fehlgeschlagen: {e}") from e
    
    def _generate_xml(
        self,
        jahr: int,
        monat: int,
        betrage: UStVABetrage,
        erstellungsdatum: str
    ) -> str:
        """Generiert das XML"""
        
        # Root Element
        root = ET.Element('Elster')
        root.set('xmlns', 'http://www.elster.de/elsterxml/schema/v11')
        root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        
        # Transfer-Header
        transfer_header = ET.SubElement(root, 'TransferHeader')
        transfer_header.set('version', '11')
        
        # Verfahren
        verfahren = ET.SubElement(transfer_header, 'Verfahren')
        verfahren.text = 'ElsterBRM'
        
        # DatenArt
        daten_art = ET.SubElement(transfer_header, 'DatenArt')
        daten_art.text = 'USt-Voranmeldung'
        
        # Vorgang
        vorgang = ET.SubElement(transfer_header, 'Vorgang')
        vorgang.text = 'send-NoSignature'
        
        # Transfer-Body
        transfer_body = ET.SubElement(root, 'TransferBody')
        transfer_body.set('version', '11')
        
        # Daten-Lieferant
        daten_lieferant = ET.SubElement(transfer_body, 'DatenLieferant')
        
        # Name
        name_elem = ET.SubElement(daten_lieferant, 'Name')
        name_elem.text = self.name
        
        # Steuerfall
        steuerfall = ET.SubElement(transfer_body, 'Steuerfall')
        
        # UmsatzsteuerVoranmeldung
        ust_va = ET.SubElement(steuerfall, 'UmsatzsteuerVoranmeldung')
        ust_va.set('SteuerfallArt', 'USt-Voranmeldung')
        ust_va.set('version', '2022')
        
        # Steuerpflichtiger
        steuerpflichtiger = ET.SubElement(ust_va, 'Steuerpflichtiger')
        
        # Steuernummer
        st_nr = ET.SubElement(steuerpflichtiger, 'Steuernummer')
        st_nr.text = self.steuernummer
        
        # Finanzamt
        fz_elem = ET.SubElement(steuerpflichtiger, 'Finanzamt')
        fz_elem.text = self.finanzamt
        
        # Zeitraum
        zeitraum = ET.SubElement(ust_va, 'Zeitraum')
        
        jahr_elem = ET.SubElement(zeitraum, 'Jahr')
        jahr_elem.text = str(jahr)
        
        monat_elem = ET.SubElement(zeitraum, 'Monat')
        monat_elem.text = str(monat)
        
        # Erstellungsdatum
        erstellt = ET.SubElement(ust_va, 'Erstellungsdatum')
        erstellt.text = erstellungsdatum
        
        # Kennzahlen
        kennzahlen = ET.SubElement(ust_va, 'Kennzahlen')
        
        # Kz 81 - Umsatzsteuer 19%
        if betrage.kz81 > 0:
            kz81_elem = ET.SubElement(kennzahlen, 'Kz81')
            kz81_elem.text = str(betrage.kz81)
        
        # Kz 86 - Umsatzsteuer 7%
        if betrage.kz86 > 0:
            kz86_elem = ET.SubElement(kennzahlen, 'Kz86')
            kz86_elem.text = str(betrage.kz86)
        
        # Kz 66 - Vorsteuer
        if betrage.kz66 > 0:
            kz66_elem = ET.SubElement(kennzahlen, 'Kz66')
            kz66_elem.text = str(betrage.kz66)
        
        # Kz 63 - Berichtigung Vorsteuer
        if betrage.kz63 > 0:
            kz63_elem = ET.SubElement(kennzahlen, 'Kz63')
            kz63_elem.text = str(betrage.kz63)
        
        # Berechnete Felder
        ust_gesamt = ET.SubElement(kennzahlen, 'UStGesamt')
        ust_gesamt.text = str(betrage.ust_gesamt)
        
        vorsteuer_gesamt = ET.SubElement(kennzahlen, 'VorsteuerGesamt')
        vorsteuer_gesamt.text = str(betrage.vorsteuer_gesamt)
        
        zahllast = ET.SubElement(kennzahlen, 'Zahllast')
        zahllast.text = str(betrage.zahllast)
        
        # XML formatieren
        rough_string = ET.tostring(root, encoding='unicode')
        reparsed = minidom.parseString(rough_string)
        
        # Schöne Formatierung
        pretty_xml = reparsed.toprettyxml(indent="  ", encoding=None)
        
        # Leere Zeilen entfernen
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        
        return '\n'.join(lines)
    
    def save_to_file(
        self,
        xml_content: str,
        filename: Optional[str] = None
    ) -> str:
        """
        Speichert das XML in eine Datei.
        
        Args:
            xml_content: Der XML-String
            filename: Optionaler Dateiname
            
        Returns:
            Pfad zur gespeicherten Datei
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"UStVA_{self.steuernummer}_{timestamp}.xml"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        return filename


def batch_create_voranmeldungen(
    generator: UStVAGenerator,
    perioden: list,
    base_path: str = "./"
) -> list:
    """
    Erstellt mehrere USt-Voranmeldungen auf einmal.
    
    Args:
        generator: Initialisierter Generator
        perioden: Liste von Dicts mit 'jahr', 'monat', 'kz81', etc.
        base_path: Basis-Verzeichnis für Ausgabe
        
    Returns:
        Liste der erstellten Dateipfade
    """
    created_files = []
    
    for periode in perioden:
        try:
            xml = generator.create_voranmeldung(**periode)
            
            jahr = periode['jahr']
            monat = periode['monat']
            filename = f"{base_path}/UStVA_{jahr}_{monat:02d}.xml"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(xml)
            
            created_files.append(filename)
        except Exception as e:
            print(f"Fehler bei Periode {periode}: {e}")
            raise
    
    return created_files


# Convenience-Funktionen
def quick_voranmeldung(
    steuernummer: str,
    finanzamt: str,
    name: str,
    jahr: int,
    monat: int,
    kz81: int = 0,
    kz86: int = 0,
    kz66: int = 0,
    kz63: int = 0
) -> str:
    """
    Schnelle Einzel-Voranmeldung ohne Generator-Instanz.
    
    Returns:
        XML-String
    """
    gen = UStVAGenerator(
        steuernummer=steuernummer,
        finanzamt=finanzamt,
        name=name
    )
    
    return gen.create_voranmeldung(
        jahr=jahr,
        monat=monat,
        kz81=kz81,
        kz86=kz86,
        kz66=kz66,
        kz63=kz63
    )
