"""
GoBD-konforme Rechnungsnummer-Generierung
Erstellt lückenlose, fortlaufende Rechnungsnummern nach GoBD

Fokus: German Tax Compliance, GoBD, E-Commerce
"""

import json
import os
import re
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class RechnungsnummerConfig:
    """Konfiguration für Rechnungsnummern-Schema"""
    prefix: str = "RE"           # Präfix (z.B. RE, INV, RG)
    jahr_format: str = "YYYY"    # JJJJ oder YY
    trennzeichen: str = "-"      # Trennzeichen
    ziffern: int = 5             # Mindeststellen für Nummer
    start_nummer: int = 1        # Startwert
    
    def __post_init__(self):
        """Validiere Konfiguration"""
        if self.jahr_format not in ["YYYY", "YY", ""]:
            raise ValueError("jahr_format muss 'YYYY', 'YY' oder '' sein")


class GoBDRechnungsnummer:
    """
    GoBD-konforme Rechnungsnummer-Generierung
    
    GoBD-Anforderungen:
    - Fortlaufend (keine Lücken)
    - Eindeutig
    - Chronologisch
    - Nicht manipulierbar
    """
    
    # Pfad zur Counter-Datei
    COUNTER_FILE = "rechnungsnummern_counter.json"
    
    def __init__(self, config: RechnungsnummerConfig = None, storage_path: str = None):
        """
        Args:
            config: Konfiguration für das Nummernschema
            storage_path: Pfad zur Speicherung der Counter
        """
        self.config = config or RechnungsnummerConfig()
        self.storage_path = storage_path or os.getcwd()
        self.counter_file = os.path.join(self.storage_path, self.COUNTER_FILE)
        
        # Lade oder initialisiere Counter
        self.counter = self._load_counter()
    
    def _load_counter(self) -> Dict:
        """Lädt den aktuellen Counter aus Datei"""
        if os.path.exists(self.counter_file):
            try:
                with open(self.counter_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        
        # Initialer Counter
        return {
            'schema': asdict(self.config),
            'jahr': datetime.now().year,
            'letzte_nummer': self.config.start_nummer - 1,
            'ausgegebene_nummern': []
        }
    
    def _save_counter(self):
        """Speichert den Counter in Datei"""
        os.makedirs(os.path.dirname(self.counter_file) if os.path.dirname(self.counter_file) else '.', exist_ok=True)
        with open(self.counter_file, 'w') as f:
            json.dump(self.counter, f, indent=2)
    
    def generiere(self, datum: datetime = None, speichern: bool = True) -> str:
        """
        Generiert neue GoBD-konforme Rechnungsnummer
        
        Args:
            datum: Datum für Rechnung (default: heute)
            speichern: Ob Nummer persistiert werden soll
        
        Returns:
            Rechnungsnummer als String
        """
        if datum is None:
            datum = datetime.now()
        
        # Prüfe Jahreswechsel
        if datum.year > self.counter['jahr']:
            # Neues Jahr: Reset Counter wenn gewünscht
            self.counter['jahr'] = datum.year
            # Optional: Counter zurücksetzen
            # self.counter['letzte_nummer'] = self.config.start_nummer - 1
        
        # Inkrementiere Counter
        self.counter['letzte_nummer'] += 1
        laufende_nummer = self.counter['letzte_nummer']
        
        # Baue Nummer auf
        teile = []
        
        if self.config.prefix:
            teile.append(self.config.prefix)
        
        if self.config.jahr_format == "YYYY":
            teile.append(str(datum.year))
        elif self.config.jahr_format == "YY":
            teile.append(str(datum.year)[-2:])
        
        # Laufende Nummer mit führenden Nullen
        nummer_str = str(laufende_nummer).zfill(self.config.ziffern)
        teile.append(nummer_str)
        
        rechnungsnummer = self.config.trennzeichen.join(teile)
        
        # Speichern
        if speichern:
            self.counter['ausgegebene_nummern'].append({
                'nummer': rechnungsnummer,
                'datum': datum.isoformat(),
                'timestamp': datetime.now().isoformat()
            })
            self._save_counter()
        
        return rechnungsnummer
    
    def validiere(self, nummer: str) -> Dict:
        """
        Validiert eine Rechnungsnummer gegen GoBD
        
        Returns:
            Dict mit Validierungsergebnis
        """
        result = {
            'gueltig': False,
            'nummer': nummer,
            'fehler': [],
            'warnungen': []
        }
        
        if not nummer:
            result['fehler'].append("Rechnungsnummer ist leer")
            return result
        
        # Prüfe auf erlaubte Zeichen
        if not re.match(r'^[A-Z0-9\-_\.]+$', nummer, re.IGNORECASE):
            result['fehler'].append("Ungültige Zeichen (nur Buchstaben, Zahlen, -, _, .)")
        
        # Länge prüfen
        if len(nummer) < 3:
            result['fehler'].append("Rechnungsnummer zu kurz (min. 3 Zeichen)")
        
        if len(nummer) > 50:
            result['fehler'].append("Rechnungsnummer zu lang (max. 50 Zeichen)")
        
        # Doppelte Leerzeichen/Striche
        if '  ' in nummer or '--' in nummer:
            result['warnungen'].append("Doppelte Leerzeichen oder Striche")
        
        if not result['fehler']:
            result['gueltig'] = True
        
        return result
    
    def pruefe_luecken(self) -> List[int]:
        """
        Prüft auf Lücken in den vergebenen Nummern
        
        Returns:
            Liste der fehlenden Nummern
        """
        if not self.counter['ausgegebene_nummern']:
            return []
        
        # Extrahiere laufende Nummern
        nummern = []
        for eintrag in self.counter['ausgegebene_nummern']:
            # Versuche Nummer zu extrahieren
            match = re.search(r'(\d+)$', eintrag['nummer'])
            if match:
                nummern.append(int(match.group(1)))
        
        nummern.sort()
        
        # Finde Lücken
        luecken = []
        for i in range(len(nummern) - 1):
            if nummern[i + 1] - nummern[i] > 1:
                for j in range(nummern[i] + 1, nummern[i + 1]):
                    luecken.append(j)
        
        return luecken
    
    def get_naechste_nummer(self) -> int:
        """Gibt die nächste laufende Nummer zurück (ohne zu speichern)"""
        return self.counter['letzte_nummer'] + 1
    
    def get_statistik(self) -> Dict:
        """Gibt Statistiken über vergebenen Nummern"""
        return {
            'jahr': self.counter['jahr'],
            'letzte_nummer': self.counter['letzte_nummer'],
            'anzahl_ausgegeben': len(self.counter['ausgegebene_nummern']),
            'luecken': self.pruefe_luecken(),
            'schema': self.config.prefix
        }
    
    def export_vergabe_liste(self, dateipfad: str):
        """
        Exportiert Liste aller vergebenen Nummern (GoBD-Nachweis)
        """
        with open(dateipfad, 'w') as f:
            f.write("Rechnungsnummer;Datum;Timestamp\n")
            for eintrag in self.counter['ausgegebene_nummern']:
                f.write(f"{eintrag['nummer']};{eintrag['datum']};{eintrag['timestamp']}\n")


def erstelle_rechnungsnummer(schema: str = "RE-YYYY-NNNNN", 
                              speicherpfad: str = None) -> str:
    """
    Schnell-Funktion zur Erstellung einer Rechnungsnummer
    
    Schemas:
    - RE-YYYY-NNNNN → RE-2025-00001
    - RG-YY-NNNN → RG-25-0001
    - INV-NNNNNN → INV-000001
    
    Usage:
        nummer = erstelle_rechnungsnummer("RE-YYYY-NNNNN")
        nummer = erstelle_rechnungsnummer("RG-{year}-{num:04d}")
    """
    # Parse Schema
    if "YYYY" in schema:
        config = RechnungsnummerConfig(
            prefix=schema.split('-')[0] if '-' in schema else "",
            jahr_format="YYYY",
            trennzeichen="-"
        )
    elif "YY" in schema:
        config = RechnungsnummerConfig(
            prefix=schema.split('-')[0] if '-' in schema else "",
            jahr_format="YY",
            trennzeichen="-"
        )
    else:
        config = RechnungsnummerConfig(
            prefix=schema.split('-')[0] if '-' in schema else "",
            jahr_format=""
        )
    
    generator = GoBDRechnungsnummer(config, speicherpfad)
    return generator.generiere()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python rechnungsnummer_gobd.py <command> [options]")
        print("\nCommands:")
        print("  generate [prefix]     - Neue Rechnungsnummer generieren")
        print("  validate <nummer>    - Rechnungsnummer validieren")
        print("  stats                 - Statistiken anzeigen")
        print("  check                 - Auf Lücken prüfen")
        print("\nBeispiele:")
        print("  python rechnungsnummer_gobd.py generate RE")
        print("  python rechnungsnummer_gobd.py validate RE-2025-00001")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "generate":
        prefix = sys.argv[2] if len(sys.argv) > 2 else "RE"
        config = RechnungsnummerConfig(prefix=prefix, jahr_format="YYYY")
        generator = GoBDRechnungsnummer(config)
        nummer = generator.generiere()
        print(f"✅ Neue Rechnungsnummer: {nummer}")
    
    elif command == "validate":
        if len(sys.argv) < 3:
            print("❌ Fehler: Rechnungsnummer angeben")
            sys.exit(1)
        nummer = sys.argv[2]
        generator = GoBDRechnungsnummer()
        result = generator.validiere(nummer)
        if result['gueltig']:
            print(f"✅ Rechnungsnummer '{nummer}' ist gültig")
        else:
            print(f"❌ Rechnungsnummer '{nummer}' ist ungültig")
            for fehler in result['fehler']:
                print(f"   - {fehler}")
    
    elif command == "stats":
        generator = GoBDRechnungsnummer()
        stats = generator.get_statistik()
        print("📊 Rechnungsnummer-Statistik:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
    
    elif command == "check":
        generator = GoBDRechnungsnummer()
        luecken = generator.pruefe_luecken()
        if luecken:
            print(f"⚠️  Lücken gefunden: {luecken}")
        else:
            print("✅ Keine Lücken in den Rechnungsnummern")
    
    else:
        print(f"❌ Unbekannter Befehl: {command}")
