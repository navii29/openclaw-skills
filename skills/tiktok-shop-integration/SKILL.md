# Skill: TikTok Shop Integration

## Description
Synchronisiere Produkte mit TikTok Shop. Verwalte Inventar, Preise und Bestellungen – automatisiert über die TikTok Shop API.

## Capabilities
- `tiktok.product_sync` - Sync Produkte zu TikTok Shop
- `tiktok.inventory_update` - Aktualisiere Lagerbestände
- `tiktok.order_fetch` - Hole Bestellungen
- `tiktok.price_update` - Aktualisiere Preise

## API Keys Required
- TikTok Shop App Key
- TikTok Shop App Secret
- Shop ID
- Access Token

## Setup Time
10-15 Minuten

## Use Cases
- Multi-Channel E-Commerce
- TikTok Shop Automation
- Product Feed Sync

## Tags
tiktok, shop, e-commerce, api, product-sync, inventory

## Configuration

```bash
export TIKTOK_APP_KEY="your_key"
export TIKTOK_APP_SECRET="your_secret"
export TIKTOK_SHOP_ID="your_shop_id"
export TIKTOK_ACCESS_TOKEN="your_token"
```

## Usage

```bash
# Sync products from JSON
python tiktok_shop.py --sync products.json

# Update inventory
python tiktok_shop.py --update-stock SKU123 50

# Fetch orders
python tiktok_shop.py --orders --status PENDING
```
