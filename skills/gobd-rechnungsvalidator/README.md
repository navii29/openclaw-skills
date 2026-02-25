# 🧾 GoBD-Rechnungsvalidator

> Automatische Validierung von Rechnungs-PDFs auf GoBD-Konformität für deutsche Kanzleien

## ⚡ Schnellstart

```bash
# Installation
pip install -r requirements.txt

# Einzelne Rechnung prüfen
python gobd_validator.py rechnung.pdf

# Ordner mit Rechnungen batch-verarbeiten
python gobd_validator.py /pfad/zur/ordner/ --batch --output report.json
```

## 📋 GoBD-Pflichtangaben (§14 UStG)

Der Validator prüft alle 9 wichtigsten Pflichtangaben:

| Nr. | Pflichtangabe | Status |
|-----|--------------|--------|
| 1 | Lieferant (Name + Anschrift) | ✅ |
| 2 | Steuernummer oder USt-IdNr | ✅ |
| 3 | Rechnungsdatum | ✅ |
| 4 | Rechnungsnummer | ✅ |
| 5 | Leistungsbeschreibung | ✅ |
| 6 | Lieferdatum/Zeitraum | ✅ |
| 7 | Gesamtbetrag | ✅ |
| 8 | Steuersatz | ✅ |

## 🎯 Use-Cases

- **Steuerkanzleien:** Automatische Vorprüfung vor DATEV-Import
- **Buchhaltungsbüros:** Massenverarbeitung von Eingangsrechnungen
- **E-Commerce:** Kontrolle von Lieferantenrechnungen
- **Freiberufler:** Schnell-Check eigener ausgehender Rechnungen

## 📊 Beispiel-Ausgabe

```json
{
  "filename": "rechnung_001.pdf",
  "is_valid": true,
  "score": 9,
  "max_score": 9,
  "confidence": 1.0,
  "missing_fields": [],
  "extracted_data": {
    "lieferant_name": "Muster GmbH",
    "lieferant_anschrift": "Musterstraße 1, 12345 Berlin",
    "steuernummer": "12/345/67890",
    "ust_id": "DE123456789",
    "rechnungsdatum": "15.02.2024",
    "rechnungsnummer": "RE-2024-001",
    "gesamtbetrag": "1.190,00 €",
    "ust_satz": "19%"
  },
  "warnings": []
}
```

## 🔧 Python API

```python
from gobd_validator import validate_rechnung

result = validate_rechnung("rechnung.pdf")

if result.is_valid:
    print("✅ Rechnung ist GoBD-konform")
else:
    print(f"❌ Fehlende Angaben: {result.missing_fields}")
```

## 🚀 Roadmap

- [x] PDF-Text-Extraktion
- [x] 9 GoBD-Pflichtfelder
- [x] Batch-Verarbeitung
- [ ] OCR für gescannte Rechnungen
- [ ] QR-Code/ERechnung Support
- [ ] DATEV-CSV Export
- [ ] Lexware-Integration
- [ ] sevdesk API-Anbindung

## 💰 SaaS-Potenzial

| Plan | Preis | Features |
|------|-------|----------|
| Free | 0€ | 10 Rechnungen/Monat |
| Pro | 29€/Monat | 500 Rechnungen, API |
| Kanzlei | 99€/Monat | Unlimited, DATEV, Multi-User |

**Zielmarkt:** 40.000+ Steuerkanzleien in Deutschland

## 📄 Lizenz

MIT License - Frei für kommerzielle Nutzung

## 🤝 Mitwirken

PRs willkommen! Fokus auf deutsche Rechnungsformate (DATEV, Lexware, etc.)

---

Built with ❤️ for the German market
