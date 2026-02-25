# Skill-to-Repository Mapping

**Bestehende Repositories:**
1. dokument-processing
2. lead-qualification
3. competitive-intelligence
4. voice-workflow
5. executive-kalender
6. inbox-ai-template

---

## Mapping: Neue Skills → Bestehende Repos

### 1. dokument-processing (ERWEITERN)
**Bereits vorhanden:**
- PDF Processing (vermutlich)

**Neu hinzufügen:**
| Skill | Warum hier |
|-------|-----------|
| gobd-rechnungsvalidator | PDF → Daten-Extraktion |
| zugferd-generator | PDF → E-Rechnung |
| datev-csv-export | Daten → CSV Export |
| sepa_xml_generator | Daten → XML Export |

**Neuer Repo-Name:** `dokument-processing` → `german-accounting-suite`

---

### 2. lead-qualification (ERWEITERN)
**Bereits vorhanden:**
- Lead Qualification (vermutlich)

**Neu hinzufügen:**
| Skill | Warum hier |
|-------|-----------|
| calendly-notion-crm | Lead → Termin → CRM |
| website-lead-alerts | Website → Lead |
| email-slack-tickets | Lead → Support-Ticket |

**Neuer Repo-Name:** `lead-qualification` → `lead-pipeline-suite`

---

### 3. competitive-intelligence (PASST)
**Bereits vorhanden:**
- Competitive Intelligence

**Neu hinzufügen:**
| Skill | Warum hier |
|-------|-----------|
| ebay-kleinanzeigen-scraper | Markt-Preise beobachten |
| google-reviews-monitor | Wettbewerber-Bewertungen |
| amazon-seller-alerts | Wettbewerber-Tracking |

---

### 4. voice-workflow (OPTIONAL)
**Neu hinzufügen:**
Keine direkten Voice-Skills gebaut (außer inbox-ai hat TTS)

**Alternative:** Skills mit Voice-Integration versehen?

---

### 5. executive-kalender (ERWEITERN)
**Bereits vorhanden:**
- Executive Kalender

**Neu hinzufügen:**
| Skill | Warum hier |
|-------|-----------|
| notion-ical-sync | Kalender-Sync |
| linkedin-scheduler | Content-Planung |
| meta-business-automation | Social Media |

**Neuer Repo-Name:** `executive-kalender` → `executive-productivity-suite`

---

### 6. inbox-ai-template (ERWEITERN → CORE)
**Bereits vorhanden:**
- Inbox AI Template

**Neu hinzufügen:**
| Skill | Warum hier |
|-------|-----------|
| inbox-ai v2.2.0 | Haupt-Email-Skill |
| sevdesk v2.4.0 | Rechnung → Email → Buchhaltung |
| gmail-auto-responder | Email-Automation |
| email-slack-tickets | Email → Support |

**Neuer Repo-Name:** `inbox-ai-template` → `inbox-ai-core`

---

## Neue Repositories (Vorschläge)

### 7. tiktok-shop-integration (NEU)
TikTok ist spezialisiert → eigenes Repo

### 8. e-commerce-automation (NEU)
Alternative: Alle E-Commerce Skills zusammen
- amazon-seller-alerts
- ebay-kleinanzeigen-scraper
- shopify-telegram-alerts
- woocommerce-alerts
- stripe-payment-alerts

---

## Empfohlene Struktur

### Option A: Umbenennen + Erweitern (empfohlen)
```
navii29/
├── german-accounting-suite/      (ex: dokument-processing)
│   ├── gobd-rechnungsvalidator/
│   ├── zugferd-generator/
│   ├── datev-csv-export/
│   └── sepa-xml-generator/
│
├── lead-pipeline-suite/          (ex: lead-qualification)
│   ├── calendly-notion-crm/
│   ├── website-lead-alerts/
│   └── email-slack-tickets/
│
├── competitive-intelligence/     (bleibt)
│   ├── competitive-intelligence/
│   ├── ebay-kleinanzeigen-scraper/
│   ├── google-reviews-monitor/
│   └── amazon-seller-alerts/
│
├── executive-productivity-suite/ (ex: executive-kalender)
│   ├── executive-kalender/
│   ├── notion-ical-sync/
│   ├── linkedin-scheduler/
│   └── meta-business-automation/
│
├── inbox-ai-core/                (ex: inbox-ai-template)
│   ├── inbox-ai/
│   ├── sevdesk/
│   └── gmail-auto-responder/
│
├── voice-workflow/               (bleibt)
│   └── (erweitern mit TTS-Skills)
│
└── e-commerce-automation/        (neu)
    ├── tiktok-shop-integration/
    ├── shopify-telegram-alerts/
    ├── woocommerce-alerts/
    └── stripe-payment-alerts/
```

---

## Git Push Strategie

### Schritt 1: Bestehende Repos klonen
```bash
# Für jedes Repo:
git clone https://github.com/navii29/dokument-processing.git
git clone https://github.com/navii29/lead-qualification.git
# ... usw.
```

### Schritt 2: Skills kopieren
```bash
# German Accounting Suite
cp -r workspace/skills/gobd-rechnungsvalidator/* dokument-processing/
cp -r workspace/skills/zugferd-generator/* dokument-processing/
cp -r workspace/skills/datev-csv-export/* dokument-processing/
cp -r workspace/skills/sepa_xml_generator/* dokument-processing/
```

### Schritt 3: Commit & Push
```bash
cd dokument-processing
git add .
git commit -m "feat: Add ZUGFeRD, DATEV, SEPA skills - German Accounting Suite"
git push origin main
```

---

## Integrationen (innerhalb der Suites)

### German Accounting Suite
```python
# Beispiel-Integration
from gobd_validator import GoBDValidator
from zugferd_generator import ZUGFeRDGenerator
from datev_export import DATEVExporter
from sepa_generator import SEPAGenerator

# PDF → Validierung → E-Rechnung → Buchhaltung → Zahlung
validator = GoBDValidator()
result = validator.validate("rechnung.pdf")

if result.zugferd_compatible:
    # E-Rechnung generieren
    zugferd = validator.generate_zugferd("rechnung.pdf")
    
    # DATEV Buchung erstellen
    exporter = DATEVExporter()
    exporter.add_rechnung_from_gobd(result)
    exporter.export("datev.csv")
    
    # SEPA Zahlung vorbereiten
    sepa = SEPAGenerator()
    sepa.create_payment_from_invoice(result)
```

---

## Fragen an dich:

1. **Soll ich die Repos umbenennen** (z.B. dokument-processing → german-accounting-suite)?

2. **Soll ich neue Repos erstellen** für:
   - E-Commerce (alle Shop-Skills zusammen)?
   - TikTok (separat)?

3. **GitHub Zugriff:** Hast du ein Personal Access Token?
   ```bash
   git remote set-url origin https://TOKEN@github.com/navii29/REPO.git
   ```

4. **Soll ich die Integrationen jetzt bauen** (die Suite-Verbindungen)?
