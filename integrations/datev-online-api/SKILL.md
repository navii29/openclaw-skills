# DATEV Online API Integration

**Version:** 1.0.0  
**Preis:** Auf Anfrage (Enterprise)  
**Support:** DE/EN  

Vollständige Python-Integration für die DATEV Online API mit OAuth2, Dokumenten-Management und deutscher GoBD-Konformität.

---

## 🎯 Warum DATEV?

DATEV ist das **Rückgrat der deutschen Buchhaltung**:
- **40.000+** Steuerberater nutzen DATEV
- **3,5 Millionen** Unternehmen sind angebunden
- **Marktstandard** für deutsche Buchhaltung
- **GoBD-konform** nach deutschem Recht

### Die Marktlücke

Die meisten API-Integrationen ignorieren den deutschen Markt. DATEV ist **notoriously difficult** zu integrieren:
- OAuth2 mit PKCE erforderlich
- Single-use Refresh Tokens
- Komplexe Mandanten-Struktur
- Keine einfache Dokumentation

**Diese Integration schließt die Lücke.**

---

## ✅ Features

### Authentifizierung
- ✅ OAuth2 Authorization Code Flow mit PKCE
- ✅ Automatische Token-Refresh (berücksichtigt single-use tokens)
- ✅ Windows SSO Support (DATEV-Benutzer)
- ✅ Sandbox & Production Umgebungen

### Dokumenten-Management
- ✅ Upload zu DATEV Unternehmen online (Belege online)
- ✅ Metadaten (Belegtyp, Notizen)
- ✅ Mandanten-übergreifende Verwaltung
- ✅ Filename-Sanitization (DATEV-konform)

### Fehlerbehandlung
- ✅ Umfassende Exception-Hierarchie
- ✅ Rate-Limiting mit Retry-Logic
- ✅ Detaillierte Fehlermeldungen
- ✅ Automatische Token-Refresh bei 401

### Enterprise-Ready
- ✅ Idempotency-Keys für Retry-Sicherheit
- ✅ Connection Pooling & Timeouts
- ✅ Logging & Monitoring
- ✅ Type Hints & Dokumentation

---

## 📋 Voraussetzungen

### DATEV Developer Portal

1. **Registrierung** bei [developer.datev.de](https://developer.datev.de)
2. **Organisation** erstellen oder beitreten
3. **App erstellen** mit:
   - Client ID & Client Secret
   - Redirect URI(s)
   - API-Produkt: `accounting:documents`
4. **Technical Review** für Production-Zugang

### Python

```bash
pip install -r requirements.txt
```

---

## 🚀 Quick Start

### 1. OAuth2 Flow

```python
from datev_client import DATEVClient

client = DATEVClient(
    client_id="your-client-id",
    client_secret="your-client-secret",
    sandbox=True
)

# Auth-URL generieren
auth_url = client.get_authorization_url(
    redirect_uri="http://localhost:8080/callback"
)
print(f"Öffne: {auth_url}")

# Nach Callback: Code exchange
token = client.exchange_code(
    code="authorization-code-from-callback",
    redirect_uri="http://localhost:8080/callback"
)
print(f"Access Token: {token.access_token}")
```

### 2. Mandanten Listen

```python
clients = client.list_clients()
for c in clients:
    print(f"{c.client_id}: {c.name}")
    # Ausgabe: 12345-1: Muster GmbH
```

### 3. Dokument Hochladen

```python
from datev_client import DATEVDocument

doc = DATEVDocument(
    file_path="/path/to/rechnung.pdf",
    document_type="Rechnungseingang",
    note="Rechnung #2025-001 von Muster GmbH"
)

result = client.upload_document(
    client_id="12345-1",
    document=doc
)

if result.success:
    print(f"✅ Hochgeladen: {result.document_id}")
else:
    print(f"❌ Fehler: {result.error}")
```

---

## 📚 Use Cases

### Use Case 1: Rechnungs-Workflow (WooCommerce → DATEV)

```python
"""
Automatisierter Rechnungs-Export aus WooCommerce
 direkt in die DATEV-Buchhaltung des Steuerberaters.
"""
from datev_client import DATEVClient, DATEVDocument

def sync_woocommerce_to_datev(order):
    """
    WooCommerce Bestellung → DATEV Dokument
    """
    client = DATEVClient.from_env()
    
    # PDF Rechnung generieren
    invoice_pdf = generate_invoice_pdf(order)
    
    # Zu DATEV hochladen
    doc = DATEVDocument(
        file_content=invoice_pdf,
        filename=f"RE-{order['id']}.pdf",
        document_type="Rechnungsausgang",
        note=f"Kunde: {order['customer_name']}, "
             f"Betrag: {order['total']} EUR"
    )
    
    result = client.upload_document(
        client_id=os.environ["DATEV_CLIENT_ID"],
        document=doc
    )
    
    if result.success:
        # In WooCommerce markieren
        mark_as_synced(order['id'], result.document_id)
        return True
    
    return False
```

**Vorteile:**
- Steuerberater sieht Rechnung sofort
- Kein manueller PDF-Export
- GoBD-konforme Archivierung

---

### Use Case 2: Eingangsrechnungen (E-Mail → DATEV)

```python
"""
E-Mail Anhänge automatisch an DATEV übermitteln.
"""
import email
from datev_client import DATEVClient, DATEVDocument

def process_invoice_email(msg: email.message.Message):
    """
    E-Mail mit Rechnung verarbeiten und zu DATEV senden.
    """
    client = DATEVClient.from_env()
    
    # Anhänge extrahieren
    for attachment in get_attachments(msg):
        if is_pdf_or_image(attachment.filename):
            # OCR oder Metadaten aus E-Mail
            doc = DATEVDocument(
                file_content=attachment.content,
                filename=attachment.filename,
                document_type="Rechnungseingang",
                note=f"Von: {msg['From']}, "
                     f"Betreff: {msg['Subject']}"
            )
            
            result = client.upload_document(
                client_id="12345-1",
                document=doc,
                idempotent_key=msg['Message-ID']  # Deduplication
            )
            
            if result.success:
                move_to_folder(msg, "DATEV_Synced")
```

**Vorteile:**
- Keine manuelle Weiterleitung
- Automatische Deduplication
- Steuerberater hat sofort Zugriff

---

### Use Case 3: Beleg-Digitalisierung (Scanner → DATEV)

```python
"""
Papierbelege scannen und direkt an DATEV senden.
"""
from datev_client import DATEVClient, DATEVDocument

def scan_and_upload_document(scanner_output: bytes, filename: str):
    """
    Gescannter Beleg → DATEV
    """
    client = DATEVClient.from_env()
    
    # OCR für automatische Kategorisierung
    ocr_text = perform_ocr(scanner_output)
    doc_type = classify_document_type(ocr_text)
    
    doc = DATEVDocument(
        file_content=scanner_output,
        filename=sanitize_filename(filename),
        document_type=doc_type,  # z.B. "Rechnungseingang"
        note=f"OCR: {ocr_text[:100]}..."
    )
    
    result = client.upload_document(
        client_id=os.environ["DATEV_CLIENT_ID"],
        document=doc
    )
    
    return result.success

def classify_document_type(text: str) -> str:
    """
    Dokumenttyp basierend auf OCR-Text klassifizieren.
    """
    keywords = {
        "Rechnungseingang": ["rechnung", "invoice", "zahlbar bis"],
        "Angebot": ["angebot", "quotation", "angebotspreis"],
        "Lieferschein": ["lieferschein", "delivery note"],
        "Gutschrift": ["gutschrift", "credit note"],
    }
    
    text_lower = text.lower()
    for doc_type, words in keywords.items():
        if any(word in text_lower for word in words):
            return doc_type
    
    return None  # Ohne Belegtyp
```

**Vorteile:**
- Papierlose Buchhaltung
- Automatische Kategorisierung
- Direkte Archivierung

---

### Use Case 4: Multi-Mandanten Management

```python
"""
Verwaltung mehrerer Mandanten (z.B. für Steuerberater)
"""
from datev_client import DATEVClient

def sync_all_clients():
    """
    Alle Mandanten synchronisieren.
    """
    client = DATEVClient.from_env()
    
    # Alle zugänglichen Mandanten listen
    clients = client.list_clients()
    
    for c in clients:
        print(f"Syncing: {c.name} ({c.client_id})")
        
        # Belegtypen für Mandant anzeigen
        doc_types = client.list_document_types(c.client_id)
        available_types = [t.name for t in doc_types]
        
        # Mandant-spezifische Sync-Logik
        sync_client_documents(
            client_id=c.client_id,
            allowed_types=available_types
        )
```

**Vorteile:**
- Zentrale Verwaltung
- Mandanten-isolation
- Skalierbar für Kanzleien

---

### Use Case 5: Error-Resilient Batch-Upload

```python
"""
Robuster Batch-Upload mit Retry-Logic.
"""
from datev_client import DATEVClient, DATEVDocument, DATEVRateLimitError
import time

def batch_upload_with_retry(client: DATEVClient, documents: list):
    """
    Mehrere Dokumente mit Fehlerbehandlung hochladen.
    """
    results = []
    
    for doc in documents:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = client.upload_document(
                    client_id="12345-1",
                    document=doc,
                    idempotent_key=doc.id  # Retry-sicher
                )
                results.append(result)
                
                if result.success:
                    print(f"✅ {doc.filename}")
                else:
                    print(f"❌ {doc.filename}: {result.error}")
                break
                
            except DATEVRateLimitError as e:
                print(f"⏳ Rate limit, waiting {e.retry_after}s...")
                time.sleep(e.retry_after)
                
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"❌ {doc.filename}: Final error {e}")
                    results.append(UploadResult(
                        success=False, error=str(e)
                    ))
                else:
                    time.sleep(2 ** attempt)  # Exponential backoff
    
    return results
```

---

## 🔧 API Referenz

### DATEVClient

#### Konstruktor

```python
DATEVClient(
    client_id: str,
    client_secret: str,
    sandbox: bool = True,
    token: Optional[DATEVToken] = None,
    rate_limit_max: int = 60,
    rate_limit_window: int = 60
)
```

#### Authentifizierung

| Methode | Beschreibung |
|---------|-------------|
| `get_authorization_url(redirect_uri)` | OAuth2 Auth-URL generieren |
| `exchange_code(code, redirect_uri)` | Code gegen Token tauschen |
| `refresh_token()` | Token aktualisieren |
| `revoke_token(token_type)` | Token widerrufen |

#### Mandanten (Clients)

| Methode | Beschreibung |
|---------|-------------|
| `list_clients()` | Alle zugänglichen Mandanten |
| `get_client(client_id)` | Einzelnen Mandant abrufen |

#### Dokumente

| Methode | Beschreibung |
|---------|-------------|
| `upload_document(client_id, document)` | Dokument hochladen |
| `upload_document_with_id(client_id, doc_id, document)` | Mit spezifischer ID |
| `list_document_types(client_id)` | Verfügbare Belegtypen |

### DATEVDocument

```python
DATEVDocument(
    file_path: Optional[str] = None,      # Lokaler Pfad
    file_content: Optional[bytes] = None, # Binär-Content
    filename: Optional[str] = None,       # Dateiname
    content_type: Optional[str] = None,   # MIME-Type
    document_type: Optional[str] = None,  # z.B. "Rechnungseingang"
    note: Optional[str] = None            # Notiz für Steuerberater
)
```

---

## ⚠️ Wichtige Hinweise

### Rate Limiting

- **60 Requests/Minute** im Standard
- `Retry-After` Header wird beachtet
- Automatisches Retry bei 429

### Token-Lebenszeit

- **Access Token**: 15 Minuten
- **Refresh Token**: 11 Stunden (standard)
- **Single-Use**: Jeder Refresh invalidiert den alten Token

### File Restrictions

- **Max Dateigröße**: 20 MB pro Datei
- **Max Paketgröße**: 500 MB
- **Keine ZIP-Dateien**
- **Erlaubte Zeichen**: ` &()+-._ 0-9A-Za-zÀ-ÿ`

### Produktion-Zugang

Für Production-Zugriff benötigt man:
1. Technisches Review durch DATEV
2. Termin buchen: [go.datev.de/online-kalender-schnittstellen](https://go.datev.de/online-kalender-schnittstellen)
3. Redirect-URLs müssen HTTPS sein (kein localhost)

---

## 🔐 Security Best Practices

```python
# ✅ Richtig: Token aus Umgebungsvariablen
client = DATEVClient.from_env()

# ❌ Falsch: Hardcoded Credentials
client = DATEVClient(
    client_id="abc123",  # NIE so!
    client_secret="xyz"
)
```

```python
# ✅ Richtig: Idempotency für Retries
result = client.upload_document(
    client_id="12345-1",
    document=doc,
    idempotent_key=unique_message_id
)
```

---

## 📊 Preisgestaltung

| Plan | Preis | Features |
|------|-------|----------|
| **Sandbox** | Kostenlos | Entwicklung & Testing |
| **Production** | Auf Anfrage | Live-Integration |
| **Enterprise** | Custom | Multi-Mandant, Support |

**Hinweis:** DATEV erhebt eigene Gebühren für API-Nutzung.

---

## 🆘 Support

### DATEV Developer Portal
- Dokumentation: [developer.datev.de](https://developer.datev.de)
- Hilfe: [developer.datev.de/en/help](https://developer.datev.de/en/help)
- Beratung: [terminland.de/datev_schnittstellenberatung](https://www.terminland.de/datev_schnittstellenberatung/)

### Navii Automation
- Email: kontakt@navii-automation.de
- Website: [navii-automation.de](https://navii-automation.de)

---

## 📝 Changelog

### v1.0.0 (2025-02-26)
- 🆕 Initiale Version
- 🆕 OAuth2 mit PKCE
- 🆕 Dokumenten-Upload
- 🆕 Mandanten-Verwaltung
- 🆕 Rate-Limiting
- 🆕 Fehlerbehandlung

---

## 📄 Lizenz

Proprietär - Navii Automation GmbH

---

*Made with ❤️ in Germany for German Accounting*
