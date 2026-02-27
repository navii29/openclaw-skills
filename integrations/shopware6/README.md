# Shopware 6 Integration 🛒

Vollständige Python-Integration für **Shopware 6** – die führende deutsche eCommerce-Plattform.

## 🇩🇪 Deutsche Marktlücke

Shopware ist der Marktführer im DACH-Raum mit über 100.000 aktiven Shops. Diese Integration schließt die Lücke zwischen Shopware und moderner Workflow-Automation.

## Features

✅ **OAuth2 Authentication** – Sichere Client Credentials  
✅ **CRUD Operations** – Produkte, Kunden, Bestellungen, Kategorien  
✅ **Bulk Operations** – Effiziente Massen-Importe/-Updates  
✅ **Rate Limiting** – Automatisches Retry mit Exponential Backoff  
✅ **Error Handling** – Spezifische Exceptions für alle Fehlerfälle  
✅ **Type Hints** – Vollständig typisiert für bessere IDE-Unterstützung  

## Installation

```bash
cd integrations/shopware6
pip install -r requirements.txt

# Konfiguration
cp .env.example .env
# .env mit Ihren Shopware-Zugangsdaten bearbeiten
```

## Schnellstart

```python
from shopware6_client import Shopware6Client

# Client initialisieren
client = Shopware6Client(
    base_url="https://shop.example.com",
    client_id="SWIA...",
    client_secret="..."
)

# Produkte abrufen
products = client.get_products(limit=10)
print(f"{len(products['data'])} Produkte gefunden")

# Neues Produkt erstellen
client.create_product({
    "name": "Premium Produkt",
    "productNumber": "PROD-001",
    "stock": 100,
    "price": [{"currencyId": "b7d2554b0ce847cd82f3ac9bd1c0dfca", "gross": 99.99, "net": 84.03}],
    "tax": {"taxRate": 19}
})

client.close()
```

## Dateistruktur

```
shopware6/
├── shopware6_client.py    # Haupt-Client-Klasse
├── SKILL.md               # Detaillierte Dokumentation & Use-Cases
├── examples.py            # Praxisbeispiele
├── requirements.txt       # Python-Abhängigkeiten
├── .env.example          # Konfigurations-Template
└── README.md             # Diese Datei
```

## Use-Cases

| Szenario | Beschreibung |
|----------|--------------|
| **PIM-Integration** | Produktdaten aus zentralem PIM synchronisieren |
| **CRM-Integration** | Kundendaten mit HubSpot/Salesforce syncen |
| **Fulfillment** | Bestellungen automatisch an Lager übergeben |
| **Inventar-Sync** | Echtzeit-Bestandsabgleich mit ERP |
| **Preis-Automation** | Dynamische Preisanpassung |

Details siehe [SKILL.md](./SKILL.md)

## Shopware Setup

1. **Admin öffnen** → Einstellungen → System → Integrationen
2. **Neue Integration** erstellen
3. **Berechtigungen** vergeben:
   - `product:read`, `product:write`
   - `customer:read`, `customer:write`
   - `order:read`, `order:write`
4. **Client ID & Secret** kopieren (Secret nur einmal sichtbar!)

## API-Limits

- **Rate Limit:** 100 Requests / 10 Sekunden (Standard)
- **Bulk Limit:** 500 Entities pro Sync-Request
- **Pagination:** Max 100 Items pro Seite

## Lizenz

MIT License – Für NAVII Automation Kunden & Partner

---

**Made with ❤️ in Germany**  
NAVII Automation | navii-automation.de
