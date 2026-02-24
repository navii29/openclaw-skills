# Shopify API Integration - Prototype

## Overview
E-Commerce Automation für deutsche Shopify-Händler. Diese Integration ermöglicht:
- Automatische Bestellungsverarbeitung
- Inventory Management
- Kunden-Sync mit CRM
- Retouren-Automation

## API Basics

### Base URL
```
https://{shop-name}.myshopify.com/admin/api/2024-01/
```

### Authentication
- **Typ**: Private App Access Token
- **Header**: `X-Shopify-Access-Token: {access_token}`
- **Scopes**: read_orders, write_orders, read_products, write_products, read_customers, write_customers

### Rate Limits
- **GraphQL**: 50 Punkte/Sekunde (Leaky Bucket)
- **REST**: 2 calls/second (Shopify Plus: 4 calls/second)

## Core Endpoints

### Orders
```
GET  /orders.json?status=any&limit=250
GET  /orders/{order_id}.json
POST /orders.json
PUT  /orders/{order_id}.json
```

### Products
```
GET  /products.json?limit=250
GET  /products/{product_id}.json
POST /products.json
PUT  /products/{product_id}.json
```

### Customers
```
GET  /customers.json?limit=250
POST /customers.json
PUT  /customers/{customer_id}.json
```

### Inventory
```
GET  /inventory_levels.json?location_ids={id}
POST /inventory_levels/adjust.json
```

## Use Cases für Navii Kunden

### 1. Automatische Rechnungserstellung
```
Trigger: Shopify Order Created
Action: Create Invoice in sevDesk/DATEV
```

### 2. Retouren-Workflow
```
Trigger: Shopify Refund Created
Action: Update Inventory + Create Credit Note
```

### 3. Kunden-Sync zu HubSpot
```
Trigger: Customer Updated in Shopify
Action: Sync to HubSpot Contact
```

### 4. Low-Stock Alerts
```
Trigger: Inventory Level < Threshold
Action: Send Alert + Auto-Reorder
```

## Error Codes
- `429` - Rate limit exceeded (Retry-After header beachten!)
- `403` - Insufficient permissions
- `404` - Resource not found
- `422` - Validation error

## Webhooks
Empfohlene Webhook-Topics:
- `orders/create`
- `orders/updated`
- `orders/paid`
- `orders/cancelled`
- `refunds/create`
- `products/update`
- `inventory_levels/update`

## Test Shop
```
Shop: navii-test-store.myshopify.com
```

## Status
🟡 PROTOTYPE - Ready for testing
