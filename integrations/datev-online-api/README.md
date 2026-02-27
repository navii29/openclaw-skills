# DATEV Online API Integration

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)]()
[![DATEV](https://img.shields.io/badge/DATEV-API-green.svg)](https://developer.datev.de)

> 🇩🇪 **Die erste vollständige Python-Integration für die DATEV Online API**

Vollständige OAuth2-Integration mit PKCE, automatischem Token-Refresh, Dokumenten-Management und deutscher GoBD-Konformität.

---

## 🚀 Schnellstart

```bash
# Repository klonen
git clone https://github.com/navii-automation/datev-online-api.git
cd datev-online-api

# Abhängigkeiten installieren
pip install -r requirements.txt

# Umgebungsvariablen setzen
export DATEV_CLIENT_ID="your-client-id"
export DATEV_CLIENT_SECRET="your-client-secret"

# Beispiele ausführen
python examples.py
```

```python
from datev_client import DATEVClient, DATEVDocument

# Client initialisieren
client = DATEVClient(
    client_id="your-client-id",
    client_secret="your-client-secret",
    sandbox=True
)

# OAuth2 Flow
auth_url = client.get_authorization_url("http://localhost:8080/callback")
# ... User authentifiziert sich ...
token = client.exchange_code(code, "http://localhost:8080/callback")

# Dokument hochladen
doc = DATEVDocument(
    file_path="rechnung.pdf",
    document_type="Rechnungseingang",
    note="Rechnung #2025-001"
)
result = client.upload_document("12345-1", doc)
```

---

## 📦 Installation

### Via pip (empfohlen)

```bash
pip install datev-online-api
```

### Via Poetry

```bash
poetry add datev-online-api
```

### Manuell

```bash
git clone https://github.com/navii-automation/datev-online-api.git
pip install -e .
```

---

## 🎯 Features

| Feature | Beschreibung |
|---------|-------------|
| 🔐 **OAuth2 + PKCE** | Vollständiger Authorization Code Flow |
| 🔄 **Auto-Refresh** | Automatische Token-Aktualisierung (single-use) |
| 📄 **Dokumente** | Upload zu DATEV Unternehmen online |
| 🏢 **Mandanten** | Multi-Mandanten Verwaltung |
| 🏷️ **Belegtypen** | Dokumentenkategorisierung |
| ⚡ **Rate-Limiting** | Intelligentes Retry-Management |
| 🛡️ **Fehlerbehandlung** | Umfassende Exception-Hierarchie |
| 📝 **Type Hints** | Vollständig typisiert |

---

## 📚 Dokumentation

- **[SKILL.md](SKILL.md)** - Ausführliche Dokumentation mit Use Cases
- **[examples.py](examples.py)** - Praktische Code-Beispiele
- **[API Referenz](https://developer.datev.de)** - Offizielle DATEV API Doku

---

## 🏗️ Architektur

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Deine App     │────▶│  DATEVClient     │────▶│  DATEV API      │
│                 │     │                  │     │                 │
│ - WooCommerce   │     │ - OAuth2         │     │ - auth:documents│
│ - E-Mail        │     │ - Rate Limiting  │     │ - Belege online │
│ - Scanner       │     │ - Error Handling │     │ - Mandanten     │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

---

## 🔧 Konfiguration

### Umgebungsvariablen

```bash
# Erforderlich
export DATEV_CLIENT_ID="your-client-id"
export DATEV_CLIENT_SECRET="your-client-secret"

# Optional (für bestehende Token)
export DATEV_ACCESS_TOKEN="..."
export DATEV_REFRESH_TOKEN="..."
export DATEV_TOKEN_EXPIRES_AT="2025-02-26T15:00:00"
```

### DATEV Developer Portal Setup

1. **Registrieren**: [developer.datev.de](https://developer.datev.de)
2. **Organisation erstellen**
3. **App anlegen**:
   - Client ID & Secret generieren
   - Redirect URIs konfigurieren
   - API-Produkt `accounting:documents` abonnieren
4. **Production**: Technical Review buchen

---

## 💡 Use Cases

### 1. WooCommerce → DATEV

```python
# Rechnungen automatisch an Steuerberater senden
order = woocommerce.get_order(123)
pdf = generate_invoice(order)

doc = DATEVDocument(
    file_content=pdf,
    filename=f"RE-{order.id}.pdf",
    document_type="Rechnungsausgang"
)
client.upload_document("12345-1", doc)
```

### 2. E-Mail → DATEV

```python
# Rechnungen aus E-Mails extrahieren
for attachment in email.attachments:
    if attachment.is_pdf:
        doc = DATEVDocument(
            file_content=attachment.content,
            filename=attachment.filename,
            document_type="Rechnungseingang",
            note=f"Von: {email.sender}"
        )
        client.upload_document("12345-1", doc)
```

### 3. Scanner → DATEV

```python
# Papierbelege digitalisieren
scan = scanner.scan_document()
doc_type = classify_with_ai(scan.text)

doc = DATEVDocument(
    file_content=scan.image,
    filename="beleg_001.pdf",
    document_type=doc_type
)
client.upload_document("12345-1", doc)
```

---

## ⚠️ Wichtige Hinweise

### Rate Limiting

- **60 Requests/Minute**
- Automatisches Retry bei 429
- `Retry-After` Header wird beachtet

### Token-Lebenszeit

| Token | Dauer |
|-------|-------|
| Access Token | 15 Minuten |
| Refresh Token | 11 Stunden |
| Offline Token | 2 Jahre |

**Wichtig**: DATEV nutzt **single-use refresh tokens**!

### Datei-Restriktionen

- Max 20 MB pro Datei
- Max 500 MB pro Paket
- Keine ZIP-Dateien
- UTF-8 Encoding erforderlich

---

## 🧪 Testing

```bash
# Tests ausführen
pytest tests/

# Mit Coverage
pytest --cov=datev_client tests/

# Sandbox Tests
DATEV_SANDBOX=true pytest tests/
```

---

## 🤝 Contributing

1. Fork erstellen
2. Feature Branch: `git checkout -b feature/AmazingFeature`
3. Commits: `git commit -m 'Add AmazingFeature'`
4. Push: `git push origin feature/AmazingFeature`
5. Pull Request öffnen

---

## 📄 Lizenz

Proprietär - [Navii Automation GmbH](https://navii-automation.de)

---

## 🆘 Support

- 📧 Email: kontakt@navii-automation.de
- 🌐 Web: [navii-automation.de](https://navii-automation.de)
- 📖 DATEV Docs: [developer.datev.de](https://developer.datev.de)

---

<p align="center">
  <strong>Made with ❤️ in Germany for German Accounting</strong>
</p>
