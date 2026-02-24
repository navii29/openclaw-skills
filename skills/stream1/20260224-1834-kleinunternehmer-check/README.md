# 🧾 Kleinunternehmer-Prüfung (§19 UStG)

Automatisierte Prüfung der Kleinunternehmer-Regelung nach §19 UStG für deutsche E-Commerce Unternehmer.

## 🎯 Use Cases

- **E-Commerce**: Automatische USt-Berechnung basierend auf Status
- **Buchhaltung**: Grenzwarnungen vor Überschreitung
- **Rechnungsstellung**: Korrekte USt-Ausweisung/Hinweise
- **Steuerplanung**: Prognosen für laufendes Jahr

## 📊 Grenzwerte (§19 UStG)

| Kriterium | Grenze | Hinweis |
|-----------|--------|---------|
| **Vorjahr** | max. 22.000 € | Tatsächlicher Umsatz |
| **Aktuelles Jahr** | max. 50.000 € | Prognostiziert |

## 📦 Installation

```bash
# Keine externen Dependencies
python3 kleinunternehmer_check.py 20000 15000
```

## 🚀 Quick Start

### Als Python-Modul

```python
from kleinunternehmer_check import check_kleinunternehmer, KleinunternehmerChecker

# Schnell-Prüfung
result = check_kleinunternehmer(
    umsatz_vorjahr=20_000,
    umsatz_aktuell=15_000
)
print(result['ist_kleinunternehmer'])  # True
print(result['handlungsempfehlung'])

# Mit Checker-Objekt
checker = KleinunternehmerChecker()
status = checker.check_status(20_000, 15_000)
print(status.ist_kleinunternehmer)
```

### CLI Usage

```bash
# Kleinunternehmer (unter Grenzen)
python kleinunternehmer_check.py 20000 15000

# Grenze überschritten
python kleinunternehmer_check.py 25000 45000
```

## 📊 Rückgabewerte

```python
{
    'ist_kleinunternehmer': True,          # Entscheidung
    'begruendung': '...',                   # Begründungstext
    'umsatz_vorjahr': 20000.0,             # Vorjahresumsatz
    'umsatz_aktuell': 15000.0,             # Aktueller Umsatz
    'prognose': 30150.68,                  # Jahresprognose
    'grenzwert': 50000,                     # Grenze aktuelles Jahr
    'warnungen': [],                        # Liste von Warnungen
    'handlungsempfehlung': '...'           # Was ist zu tun?
}
```

## ⚡ Automation-Ready

### Automatische USt-Berechnung

```python
checker = KleinunternehmerChecker()
status = checker.check_status(vorjahr, aktuell)

# Rechnung erstellen
rechnung = checker.calculate_rechnung(betrag=100, 
                                       ist_kleinunternehmer=status.ist_kleinunternehmer)
# Kleinunternehmer: 100 € (keine USt)
# Normal: 100 € + 19 € USt = 119 €
```

### Grenzwarnung im E-Commerce

```python
def process_order(order_value):
    checker = KleinunternehmerChecker()
    monat = checker.check_monatsgrenze(durchschnittlicher_monatsumsatz)
    
    if monat['warnstufe'] == 'kritisch':
        notify_accountant("Grenze gefährdet!")
    
    # ...
```

## 📋 Handlungsempfehlungen

| Status | Empfehlung |
|--------|------------|
| ✅ Kleinunternehmer | "USt nicht ausweisen, Hinweis auf Rechnungen" |
| ❌ Grenze überschritten | "USt-Pflicht! Regelmäßige USt-Voranmeldung" |

## 📝 Rechnungshinweise

### Kleinunternehmer
```
Rechnungsbetrag: 100,00 €
-------------------------------------------
Kleinunternehmer gem. §19 UStG
Umsatzsteuer wird nicht erhoben.
```

### Normal (USt-pflichtig)
```
Nettobetrag:      100,00 €
19% USt:           19,00 €
-------------------------------------------
Bruttobetrag:     119,00 €
```

## 🔗 Weiterführende Links

- [§19 UStG](https://www.gesetze-im-internet.de/ustg_1980/__19.html)
- [BZSt Kleinunternehmer](https://www.bzst.de/DE/Unternehmen/USt_und_Rechnungen/Kleinunternehmer/kleinunternehmer_node.html)
- [GoBD Hinweise](https://www.bundesfinanzministerium.de/Content/DE/Downloads/BMF_Schreiben/Weitere_Steuerthemen/Abgabenordnung/2022-11-14-Gobd-nichtveranlagung.html)

## ⚠️ Wichtige Hinweise

- Grenzwerte gelten für das **Kalenderjahr**
- Bei **Option zur Besteuerung** (§19 Abs. 2) andere Regeln
- **Innergemeinschaftliche Lieferungen/Leistungen** können außerhalb liegen
- Immer mit **Steuerberater** abklären
