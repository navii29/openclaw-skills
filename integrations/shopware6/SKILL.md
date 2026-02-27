# Shopware 6 Integration

> **Deutsche eCommerce-Plattform Integration** – Vollständige REST API Unterstützung für Shopware 6 Onlineshops

## Übersicht

| Attribut | Wert |
|----------|------|
| **Plattform** | Shopware 6 (DACH-Marktführer) |
| **API Version** | Admin API v3+ |
| **Auth** | OAuth2 Client Credentials |
| **Rate Limit** | 100 req/10s (konfigurierbar) |
| **Format** | JSON REST API |
| **Sprache** | Python 3.8+ |

## Installation

```bash
# Abhängigkeiten
pip install requests

# Client importieren
from shopware6_client import Shopware6Client, create_product_payload
```

## Konfiguration

```python
client = Shopware6Client(
    base_url="https://shop.example.com",
    client_id="SWI...",           # Aus Shopware Admin → Integrationen
    client_secret="...",          # Einmalig kopieren!
    timeout=30,
    max_retries=3
)
```

## Quick Start

```python
# Verbindung testen
health = client.get_health()
print(health)  # {'status': 'healthy', 'connected': True}

# Produkte abrufen
products = client.get_products(limit=50, search="Laptop")
for product in products['data']:
    print(f"{product['attributes']['productNumber']}: {product['attributes']['name']}")

# Neues Produkt anlegen
new_product = client.create_product({
    "name": "Premium Laptop Stand",
    "productNumber": "ACC-001",
    "stock": 100,
    "active": True,
    "price": [{
        "currencyId": "b7d2554b0ce847cd82f3ac9bd1c0dfca",  # EUR
        "gross": 49.99,
        "net": 42.01,
        "linked": True
    }],
    "tax": {"taxRate": 19}
})
```

## Use Cases

### 1. Produkt-Synchronisation (PIM Integration)

**Szenario:** Zentrales Produktinformationssystem (PIM) soll mit Shopware synchronisiert werden.

```python
def sync_pim_to_shopware(pim_products):
    """
    Bulk-Synchronisation von PIM zu Shopware
    Erstellt neue Produkte, aktualisiert bestehende
    """
    shopware_products = []
    
    for pim in pim_products:
        product = {
            "id": pim.get("shopware_id"),  # Für Updates
            "name": pim["name"],
            "productNumber": pim["sku"],
            "ean": pim.get("ean"),
            "stock": pim["quantity"],
            "active": pim["active"],
            "description": pim["description"],
            "price": [{
                "currencyId": "b7d2554b0ce847cd82f3ac9bd1c0dfca",
                "gross": pim["price_gross"],
                "net": pim["price_net"],
                "linked": True
            }],
            "tax": {"taxRate": pim.get("vat_rate", 19)}
        }
        shopware_products.append(product)
    
    # Bulk upsert (max 500 pro Request empfohlen)
    result = client.sync_products(shopware_products)
    return result
```

**Vorteile:**
- Einzelne Quelle der Wahrheit
- Automatische Aktualisierung
- Fehlerhandling bei Import

---

### 2. Kunden-CRM Integration

**Szenario:** Shopware-Kundendaten mit externem CRM (z.B. HubSpot, Salesforce) synchronisieren.

```python
def sync_customers_to_crm(client, crm_api):
    """
    Neue Shopware-Kunden an CRM übertragen
    """
    # Alle Kunden seit letztem Sync
    last_sync = "2024-01-01T00:00:00Z"
    customers = client.get_customers(
        limit=100,
        filters={"createdAt": {"gte": last_sync}}
    )
    
    for customer in customers['data']:
        attrs = customer['attributes']
        
        crm_contact = {
            "email": attrs['email'],
            "firstname": attrs['firstName'],
            "lastname": attrs['lastName'],
            "company": attrs.get('company'),
            "shopware_id": customer['id'],
            "customer_number": attrs.get('customerNumber'),
            "created_at": attrs['createdAt']
        }
        
        crm_api.create_or_update_contact(crm_contact)
```

**Erweitert – B2B Kunden:**
```python
def handle_b2b_customer_registration(customer_id):
    """
    B2B-Kunden freischalten und zu spezieller Gruppe zuweisen
    """
    customer = client.get_customer(customer_id)
    company = customer['attributes'].get('company')
    
    if company:
        # Zu B2B-Kundengruppe verschieben
        client.update_customer(customer_id, {
            "groupId": "B2B_GROUP_UUID",
            "tags": [{"name": "B2B"}]
        })
        
        # E-Mail an Vertrieb senden
        notify_sales_team(customer)
```

---

### 3. Bestell-Automatisierung & Fulfillment

**Szenario:** Bestellungen automatisch an Lagerverwaltung/WMS übergeben.

```python
def process_new_orders(client, wms_api):
    """
    Neue, bezahlte Bestellungen an WMS übertragen
    """
    # Offene Bestellungen abrufen
    orders = client.get_orders(
        limit=50,
        filters={
            "stateMachineState.technicalName": "open"
        },
        sort="-orderDate"
    )
    
    for order in orders['data']:
        order_id = order['id']
        attrs = order['attributes']
        
        # Bestellung detailliert laden
        full_order = client.get_order(order_id)
        
        # An WMS senden
        wms_payload = {
            "reference": attrs['orderNumber'],
            "external_id": order_id,
            "shipping_address": {
                "name": f"{attrs['billingAddress']['firstName']} {attrs['billingAddress']['lastName']}",
                "company": attrs['billingAddress'].get('company'),
                "street": attrs['billingAddress']['street'],
                "zip": attrs['billingAddress']['zipcode'],
                "city": attrs['billingAddress']['city'],
                "country": attrs['billingAddress']['country']['name']
            },
            "items": [
                {
                    "sku": item['product']['productNumber'],
                    "quantity": item['quantity']
                }
                for item in full_order['included']
                if item['type'] == 'order_line_item'
            ]
        }
        
        # WMS Auftrag erstellen
        wms_response = wms_api.create_order(wms_payload)
        
        # Status in Shopware aktualisieren
        if wms_response['success']:
            client.update_order_status(order_id, "IN_PROGRESS_STATE_UUID")
            print(f"✅ Bestellung {attrs['orderNumber']} an WMS übertragen")
```

---

### 4. Inventar-Management & Stock-Sync

**Szenario:** Echtzeit-Bestandsabgleich zwischen ERP und Shopware.

```python
def sync_inventory_from_erp(client, erp_api):
    """
    Lagerbestände aus ERP synchronisieren
    """
    # Alle Produkte durchgehen
    for product in client.get_entity_list("product", limit=100):
        sku = product['attributes']['productNumber']
        
        # ERP-Bestand abfragen
        erp_stock = erp_api.get_stock_by_sku(sku)
        
        if erp_stock is not None:
            # Shopware aktualisieren
            client.update_product(product['id'], {
                "stock": erp_stock['quantity_available']
            })
            
            # Bei Niedrigbestand warnen
            if erp_stock['quantity_available'] < 10:
                send_low_stock_alert(sku, erp_stock['quantity_available'])
```

---

### 5. Kategorien-Management

**Szenario:** Automatische Kategorisierung basierend auf Produktattributen.

```python
def auto_categorize_products(client):
    """
    Produkte automatisch in Kategorien einsortieren
    """
    # Kategorien laden
    categories = client.get_categories(limit=100)
    category_map = {c['attributes']['name']: c['id'] for c in categories['data']}
    
    for product in client.get_entity_list("product", limit=100):
        attrs = product['attributes']
        
        # Logik für Kategorie-Zuweisung
        if 'Laptop' in attrs.get('name', ''):
            target_category = category_map.get('Computer')
        elif 'T-Shirt' in attrs.get('name', ''):
            target_category = category_map.get('Bekleidung')
        else:
            continue
        
        if target_category:
            client.update_product(product['id'], {
                "categories": [{"id": target_category}]
            })
```

---

### 6. Preis-Automatisierung (Dynamische Preise)

**Szenario:** Dynamische Preisanpassung basierend auf Wettbewerbsdaten.

```python
def adjust_prices_competitor_based(client, competitor_api):
    """
    Preise basierend auf Wettbewerbsdaten anpassen
    """
    for product in client.get_products(limit=100)['data']:
        ean = product['attributes'].get('ean')
        if not ean:
            continue
        
        # Wettbewerberpreise abfragen
        competitor_prices = competitor_api.get_prices(ean)
        
        if competitor_prices:
            lowest_competitor = min(p['price'] for p in competitor_prices)
            my_price = product['attributes']['price'][0]['gross']
            
            # 5% unter dem günstigsten Wettbewerber
            new_price = round(lowest_competitor * 0.95, 2)
            
            # Nur anpassen wenn sinnvoll (z.B. > 5% Differenz)
            if abs(new_price - my_price) / my_price > 0.05:
                client.update_product(product['id'], {
                    "price": [{
                        "currencyId": "b7d2554b0ce847cd82f3ac9bd1c0dfca",
                        "gross": new_price,
                        "net": round(new_price / 1.19, 2),
                        "linked": True
                    }]
                })
                print(f"💰 Preis für {product['attributes']['productNumber']}: {my_price}€ → {new_price}€")
```

---

## Fehlerhandling

```python
from shopware6_client import (
    Shopware6Client,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError
)

try:
    client = Shopware6Client(...)
    product = client.get_product("INVALID_ID")
    
except AuthenticationError as e:
    print(f"❌ Auth fehlgeschlagen: {e}")
    # Zugangsdaten prüfen, ggf. Admin benachrichtigen
    
except RateLimitError as e:
    print(f"⏱️ Rate Limit erreicht: {e}")
    # Später wieder versuchen
    
except NotFoundError as e:
    print(f"🔍 Nicht gefunden: {e}")
    # Produkt existiert nicht mehr
    
except ValidationError as e:
    print(f"⚠️ Validierungsfehler: {e}")
    # Daten prüfen und korrigieren
    
except Exception as e:
    print(f"🚨 Unerwarteter Fehler: {e}")
```

## Best Practices

### 1. Bulk Operations nutzen
```python
# ❌ Langsam: Einzelne Requests
for product in products:
    client.create_product(product)

# ✅ Schnell: Bulk Sync
client.sync_products(products)  # 500 Produkte in einem Request
```

### 2. Pagination für große Datenmengen
```python
# Generator nutzen für alle Produkte
for product in client.get_entity_list("product", limit=100):
    process_product(product)  # Speichersparend
```

### 3. Context Manager für sauberes Schließen
```python
with Shopware6Client(...) as client:
    # Arbeit durchführen
    client.sync_products(products)
# Session automatisch geschlossen
```

### 4. Rate Limiting beachten
- Max 100 Requests / 10 Sekunden (Standard)
- Client hat eingebautes Retry mit Exponential Backoff
- Bei großen Imports: Pausen einbauen

## Entity Referenz

| Entity | CRUD | Beschreibung |
|--------|------|--------------|
| `product` | ✅ | Produkte, Varianten |
| `customer` | ✅ | Kunden, Adressen |
| `order` | ✅ | Bestellungen, Positionen |
| `category` | ✅ | Kategorien, Navigation |
| `property_group` | ✅ | Eigenschaften/Filter |
| `manufacturer` | ✅ | Hersteller |
| `media` | ✅ | Bilder, Dateien |
| `rule` | ✅ | Regeln, Bedingungen |
| `sales_channel` | ✅ | Verkaufskanäle |

## Shopware Setup

### API-Zugang einrichten:

1. **Admin öffnen** → Einstellungen → System → Integrationen
2. **Neue Integration** erstellen
3. **Berechtigungen** vergeben:
   - `product:read`, `product:write`
   - `customer:read`, `customer:write`
   - `order:read`, `order:write`
   - `category:read`, `category:write`
4. **Client ID & Secret** kopieren (Secret nur einmal sichtbar!)

### CORS-Konfiguration (falls von externer Domain):

```yaml
# config/packages/shopware.yml
shopware:
    admin_api:
        cors_origins:
            - 'https://automation.example.com'
```

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| `401 Unauthorized` | Token abgelaufen – Client erneut initialisieren |
| `403 Forbidden` | Integration hat nicht alle Berechtigungen |
| `404 Not Found` | Entity ID existiert nicht |
| `422 Validation` | Pflichtfelder fehlen oder falsches Format |
| Rate Limit | Warten oder Batch-Größe reduzieren |

## Nächste Schritte

- [ ] Webhook-Integration für Echtzeit-Events
- [ ] Store API für Frontend-Integrationen
- [ ] Plugin-Entwicklung für erweiterte Funktionen
- [ ] Multi-Tenancy Support für Agenturen

---

**Made with ❤️ by NAVII Automation**  
Für Shopware Agenturen & Händler im DACH-Raum
