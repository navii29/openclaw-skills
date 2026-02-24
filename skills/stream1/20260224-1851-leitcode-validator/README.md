# 📦 Deutsche Post Leitcode/Sendungsverfolgung Validator

Validiert Leitcodes für Massensendungen und Sendungsnummern für E-Commerce-Tracking.

## 🎯 Use Cases

- **E-Commerce**: Validierung von Tracking-Nummern
- **Massensendungen**: Leitcode-Validierung für Warenpost
- **Fulfillment**: Automatische Tracking-URL-Generierung
- **Logistik**: Sendungstyp-Erkennung

## 📋 Unterstützte Formate

| Typ | Format | Beispiel |
|-----|--------|----------|
| **Leitcode** | 14 Ziffern | 12345671234567 |
| **DHL Packet** | 12 Ziffern | 003404341606 |
| **DHL Packet Int.** | XX123456789DE | RX123456789DE |
| **DHL Express** | 10-11 Ziffern | 1234567890 |
| **Identcode** | 11 Ziffern | 12345678901 |

## 📦 Installation

```bash
# Keine externen Dependencies
python3 leitcode_validator.py validate-sendung 003404341606
```

## 🚀 Quick Start

### Als Python-Modul

```python
from leitcode_validator import (
    validate_leitcode, 
    validate_sendungsnummer,
    DeutschePostValidator
)

# Leitcode validieren
result = validate_leitcode("12345671234567")
print(result['gueltig'])
print(result['frachtpost'])

# Sendungsnummer validieren
result = validate_sendungsnummer("003404341606")
print(result['typ'])  # DHL_PACKET
print(result['tracking_url'])

# Mit Validator-Objekt
validator = DeutschePostValidator()
url = validator.get_tracking_url("RX123456789DE")
```

### CLI Usage

```bash
# Leitcode validieren
python leitcode_validator.py validate-leitcode 12345671234567

# Sendungsnummer validieren
python leitcode_validator.py validate-sendung 003404341606
python leitcode_validator.py validate-sendung RX123456789DE

# Identcode validieren
python leitcode_validator.py validate-ident 12345678901

# Tracking-URL anzeigen
python leitcode_validator.py tracking-url 003404341606
```

## 🔢 Leitcode Format

```
12345671234567
││││││││││││└─ Prüfziffer Teil 2
││││││└┴┴┴┴┴┴── Daten Teil 2 (6 Stellen)
│││││└────────── Prüfziffer Teil 1
└┴┴┴┴─────────── Daten Teil 1 (6 Stellen)

Format: 2 × (6 Daten + 1 Prüfziffer) = 14 Stellen
```

### Prüfziffer-Berechnung (Modulo 10)

```
Gewichtung: 4-2-1 wiederholend
Beispiel: 1234567

1×4 + 2×2 + 3×1 + 4×4 + 5×2 + 6×1 = 4+4+3+16+10+6 = 43
Prüfziffer = 43 % 10 = 3
```

## 📊 Rückgabewerte

### Leitcode
```python
{
    'gueltig': True,
    'leitcode': '12345671234567',
    'frachtpost': False,
    'fehler': []
}
```

### Sendungsnummer
```python
{
    'gueltig': True,
    'sendungsnummer': '003404341606',
    'typ': 'DHL_PACKET',  # oder DHL_PACKET_INTERNATIONAL, DHL_EXPRESS, ...
    'tracking_url': 'https://www.dhl.de/...',
    'fehler': []
}
```

## ⚡ Automation-Ready

### E-Commerce Order Fulfillment

```python
def process_shipping(order):
    validator = DeutschePostValidator()
    
    # Tracking-Nummer validieren
    result = validator.validate_sendungsnummer(order['tracking_number'])
    
    if not result.gueltig:
        return {
            'status': 'ERROR',
            'message': f"Ungültige Tracking-Nummer: {result.fehler}"
        }
    
    # Tracking-URL für Kunden
    tracking_url = validator.get_tracking_url(order['tracking_number'])
    
    # E-Mail an Kunden senden
    send_tracking_email(
        customer=order['customer_email'],
        order_id=order['id'],
        tracking_url=tracking_url,
        carrier=result.typ
    )
    
    return {'status': 'OK', 'tracking_url': tracking_url}
```

### Massensendungen (Leitcode)

```python
def validate_bulk_shipment(leitcodes):
    validator = DeutschePostValidator()
    frachtpost_count = 0
    
    for code in leitcodes:
        result = validator.validate_leitcode(code)
        
        if not result.gueltig:
            log_error(f"Ungültiger Leitcode: {code}")
            continue
        
        if result.frachtpost:
            frachtpost_count += 1
            route_to_frachtpost(code)
        else:
            route_to_standard(code)
    
    return {'frachtpost': frachtpost_count, 'standard': len(leitcodes) - frachtpost_count}
```

### Tracking-URL-Generierung

```python
def generate_tracking_links(tracking_numbers):
    validator = DeutschePostValidator()
    links = []
    
    for num in tracking_numbers:
        url = validator.get_tracking_url(num)
        if url:
            links.append({
                'number': num,
                'url': url,
                'qr': f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={url}"
            })
    
    return links
```

## 📝 Sendungstypen

| Typ | Muster | Verwendung |
|-----|--------|------------|
| DHL_PACKET | `^[0-9]{12}$` | Inlandspakete |
| DHL_PACKET_INTERNATIONAL | `^[A-Z]{2}[0-9]{9}DE$` | Auslandspakete |
| DHL_EXPRESS | `^[0-9]{10,11}$` | Express-Sendungen |
| DEUTSCHE_POST | `^[A-Z]{2}[0-9]{9}DE$` | Briefe/Einschreiben |
| EINSCHREIBEN | `^[A-Z][0-9]{9}DE$` | Einschreiben |

## 🔗 Tracking-URLs

| Typ | URL |
|-----|-----|
| DHL Packet | `dhl.de/...?piececode={nummer}` |
| DHL Express | `dhl.com/...?tracking-id={nummer}` |
| Deutsche Post | `deutschepost.de/...?form.sendungsnummer={nummer}` |

## 🔗 Weiterführende Links

- [DHL Tracking](https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html)
- [Deutsche Post Sendungsverfolgung](https://www.deutschepost.de/sendung/simpleQuery.html)
- [DHL Entwicklerportal](https://developer.dhl.com/)
- [Leitcode (Wikipedia)](https://de.wikipedia.org/wiki/Leitcode)

## ⚠️ Wichtige Hinweise

- Leitcode = Massensendungen (nicht für Einzelpakete)
- Tracking-URLs können sich ändern
- Sendungsnummern sind nicht immer sofort trackbar
- Frachtpost-Leitcodes beginnen mit 40-45
- Identcode = Zustellnachweis (kein Tracking)
