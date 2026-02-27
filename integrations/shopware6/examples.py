"""
Shopware 6 Integration - Beispiel-Skripte
Deutsche eCommerce-Automatisierung für NAVII
"""

import os
from datetime import datetime, timedelta
from shopware6_client import Shopware6Client, create_product_payload, create_customer_payload


def example_product_sync():
    """
    Beispiel: Produktimport aus CSV/Excel
    """
    client = Shopware6Client(
        base_url=os.getenv("SHOPWARE_URL"),
        client_id=os.getenv("SHOPWARE_CLIENT_ID"),
        client_secret=os.getenv("SHOPWARE_CLIENT_SECRET")
    )
    
    # Beispiel-Produkte (normalerweise aus CSV/PIM)
    products = [
        {
            "name": "Premium Kaffeemaschine",
            "productNumber": "KF-2024-001",
            "price_gross": 299.99,
            "stock": 25,
            "description": "Professionelle Kaffeemaschine für Büro und Zuhause"
        },
        {
            "name": "Bio Kaffeebohnen 1kg",
            "productNumber": "KF-2024-002", 
            "price_gross": 24.99,
            "stock": 150,
            "description": "Fairtrade Bio-Arabica aus Äthiopien"
        }
    ]
    
    for prod in products:
        try:
            payload = create_product_payload(
                name=prod["name"],
                product_number=prod["productNumber"],
                price_gross=prod["price_gross"],
                stock=prod["stock"],
                description=prod["description"]
            )
            
            result = client.create_product(payload)
            print(f"✅ Produkt erstellt: {prod['productNumber']}")
            
        except Exception as e:
            print(f"❌ Fehler bei {prod['productNumber']}: {e}")
    
    client.close()


def example_customer_import():
    """
    Beispiel: B2B Kundenimport
    """
    client = Shopware6Client(
        base_url=os.getenv("SHOPWARE_URL"),
        client_id=os.getenv("SHOPWARE_CLIENT_ID"),
        client_secret=os.getenv("SHOPWARE_CLIENT_SECRET")
    )
    
    # B2B Kunde erstellen
    customer = create_customer_payload(
        email="max.mustermann@musterfirma.de",
        first_name="Max",
        last_name="Mustermann",
        password="SicheresPasswort123!",
        company="Musterfirma GmbH",
        street="Musterstraße 123",
        zipcode="10115",
        city="Berlin"
    )
    
    try:
        result = client.create_customer(customer)
        print(f"✅ B2B Kunde erstellt: {result['data']['id']}")
    except Exception as e:
        print(f"❌ Fehler: {e}")
    
    client.close()


def example_order_processing():
    """
    Beispiel: Neue Bestellungen verarbeiten
    """
    with Shopware6Client(
        base_url=os.getenv("SHOPWARE_URL"),
        client_id=os.getenv("SHOPWARE_CLIENT_ID"),
        client_secret=os.getenv("SHOPWARE_CLIENT_SECRET")
    ) as client:
        
        # Bestellungen der letzten 24h
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        
        orders = client.get_orders(
            limit=50,
            filters={"orderDate": {"gte": yesterday}},
            sort="-orderDate"
        )
        
        print(f"📦 {len(orders['data'])} neue Bestellungen gefunden")
        
        for order in orders['data']:
            attrs = order['attributes']
            print(f"\n  Bestellung: {attrs['orderNumber']}")
            print(f"  Betrag: {attrs['amountTotal']}€")
            print(f"  Kunde: {attrs['billingAddress']['email']}")
            
            # Hier: An WMS/Lagerverwaltung übertragen
            # wms_api.create_pick_order(order)


def example_inventory_report():
    """
    Beispiel: Lagerbestandsbericht generieren
    """
    with Shopware6Client(
        base_url=os.getenv("SHOPWARE_URL"),
        client_id=os.getenv("SHOPWARE_CLIENT_ID"),
        client_secret=os.getenv("SHOPWARE_CLIENT_SECRET")
    ) as client:
        
        print("📊 Lagerbestandsbericht")
        print("=" * 60)
        
        low_stock_items = []
        total_value = 0
        
        for product in client.get_entity_list("product", limit=100):
            attrs = product['attributes']
            stock = attrs.get('stock', 0)
            price = attrs.get('price', [{}])[0].get('gross', 0)
            
            product_value = stock * price
            total_value += product_value
            
            if stock < 10:
                low_stock_items.append({
                    "sku": attrs['productNumber'],
                    "name": attrs['name'],
                    "stock": stock
                })
            
            print(f"{attrs['productNumber']:15} | {attrs['name'][:30]:30} | {stock:5} Stk. | {product_value:8.2f}€")
        
        print("=" * 60)
        print(f"Gesamtwert Lagerbestand: {total_value:.2f}€")
        
        if low_stock_items:
            print(f"\n⚠️  Niedrige Bestände ({len(low_stock_items)} Artikel):")
            for item in low_stock_items:
                print(f"   - {item['sku']}: {item['name']} (nur {item['stock']} Stk.)")


def example_bulk_price_update():
    """
    Beispiel: Massenpreisaktualisierung
    """
    with Shopware6Client(
        base_url=os.getenv("SHOPWARE_URL"),
        client_id=os.getenv("SHOPWARE_CLIENT_ID"),
        client_secret=os.getenv("SHOPWARE_CLIENT_SECRET")
    ) as client:
        
        # Alle Produkte mit "Sonderangebot" im Namen um 10% reduzieren
        products = client.get_products(
            search="Sonderangebot",
            limit=100
        )
        
        updates = []
        for product in products.get('data', []):
            attrs = product['attributes']
            current_price = attrs['price'][0]['gross']
            new_price = round(current_price * 0.9, 2)  # 10% Rabatt
            
            updates.append({
                "id": product['id'],
                "price": [{
                    "currencyId": "b7d2554b0ce847cd82f3ac9bd1c0dfca",
                    "gross": new_price,
                    "net": round(new_price / 1.19, 2),
                    "linked": True
                }]
            })
            
            print(f"💰 {attrs['productNumber']}: {current_price}€ → {new_price}€")
        
        # Bulk update
        if updates:
            result = client.sync_products(updates)
            print(f"\n✅ {len(updates)} Produkte aktualisiert")


if __name__ == "__main__":
    print("=" * 60)
    print("Shopware 6 Integration - Beispiele")
    print("=" * 60)
    
    # Umgebungsvariablen prüfen
    required = ["SHOPWARE_URL", "SHOPWARE_CLIENT_ID", "SHOPWARE_CLIENT_SECRET"]
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        print(f"\n⚠️  Fehlende Umgebungsvariablen: {', '.join(missing)}")
        print("\nBitte .env Datei erstellen:")
        print("  SHOPWARE_URL=https://shop.example.com")
        print("  SHOPWARE_CLIENT_ID=SWIAXXX...")
        print("  SHOPWARE_CLIENT_SECRET=...")
        exit(1)
    
    # Beispiele ausführen (kommentieren Sie aus, was nicht benötigt wird)
    
    print("\n1️⃣  API-Verbindung testen...")
    with Shopware6Client(
        base_url=os.getenv("SHOPWARE_URL"),
        client_id=os.getenv("SHOPWARE_CLIENT_ID"),
        client_secret=os.getenv("SHOPWARE_CLIENT_SECRET")
    ) as client:
        health = client.get_health()
        print(f"   Status: {health['status']}")
        print(f"   Verbunden: {health['connected']}")
    
    # print("\n2️⃣  Produktimport...")
    # example_product_sync()
    
    # print("\n3️⃣  Kundenimport...")
    # example_customer_import()
    
    # print("\n4️⃣  Bestellverarbeitung...")
    # example_order_processing()
    
    # print("\n5️⃣  Lagerbericht...")
    # example_inventory_report()
    
    # print("\n6️⃣  Preisaktualisierung...")
    # example_bulk_price_update()
    
    print("\n✅ Beispiele abgeschlossen!")
