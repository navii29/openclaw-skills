# Skill: PDF Rechnung zu DATEV CSV

## Use Case
Buchhaltung in deutschen Unternehmen: PDF-Rechnungen automatisch parsen und DATEV-kompatible CSVs erstellen – spart Stunden manueller Arbeit.

## Problem
- Rechnungen als PDFs manuell in DATEV eingeben
- Fehleranfällige Doppel-Erfassung
- Zeitaufwand bei hohem Rechnungsvolumen
- Unterschiedliche PDF-Formate je Lieferant

## Lösung
Python-Skript zur PDF-Extraktion:
1. PDF-Rechnung einlesen (OCR falls nötig)
2. Schlüsseldaten extrahieren (Rechnungsnr., Datum, Betrag, MwSt)
3. DATEV-CSV Format erzeugen
4. Buchungssatz-Vorschläge basierend auf Lieferant

## Inputs
- PDF-Rechnungsdateien
- Lieferanten-Mapping (Name → Konto)
- MwSt-Sätze (7%, 19%)

## Outputs
- DATEV-kompatible CSV
- Fehler-Report für manuelle Prüfung
- JSON mit extrahierten Daten

## API Keys Required
- Keine (nur Python libraries)

## Setup Time
5 Minuten

## Use Cases
- Monatliche Rechnungsbuchung
- Lieferanten-Zahlungen vorbereiten
- MwSt-Voranmeldung Daten sammeln
- Archivierung mit Metadaten

## Tags
pdf, rechnung, datev, buchhaltung, accounting, csv, fakturierung
