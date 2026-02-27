# Kategorische Repository-Struktur

**Anzahl Repos:** 10 (6 bestehende aktualisiert + 4 neue)
**Total Skills:** 38
**Strategie:** Jedes Thema = eigene Repo

---

## Repository 1: german-accounting-suite
**Thema:** Deutsche Buchhaltung & Steuern
**Basis:** dokument-processing (erweitert)

| Skill | Version | Tests |
|-------|---------|-------|
| gobd-rechnungsvalidator | v2.5.0 | 26 ✅ |
| zugferd-generator | v1.0.0 | 11 ✅ |
| datev-csv-export | v2.0.0 | 13 ✅ |
| sepa-xml-generator | v1.0.0 | 27 ✅ |
| german-accounting-suite | v1.1.0 | 20 ✅ |

**Preis:** 299€/Monat (Bundle)

---

## Repository 2: lead-pipeline-suite
**Thema:** Lead Generierung & CRM
**Basis:** lead-qualification (erweitert)

| Skill | Version | Tests |
|-------|---------|-------|
| calendly-notion-crm | v1.0.0 | ? |
| website-lead-alerts | v1.0.0 | ? |
| email-slack-tickets | v1.0.0 | ? |
| lead-pipeline-suite | v1.0.0 | ? |

**Preis:** 149€/Monat (Bundle)

---

## Repository 3: competitive-intelligence
**Thema:** Markt- & Wettbewerbsanalyse
**Basis:** competitive-intelligence (erweitert)

| Skill | Version | Tests |
|-------|---------|-------|
| ebay-kleinanzeigen-scraper | v1.0.0 | 17 ✅ |
| google-reviews-monitor | v1.0.0 | 15 ✅ |
| amazon-seller-alerts | v1.0.0 | 17 ✅ |

**Preis:** 199€/Monat (Bundle)

---

## Repository 4: e-commerce-automation
**Thema:** E-Commerce Plattformen (NEU)

| Skill | Version | Tests |
|-------|---------|-------|
| shopify-telegram-alerts | v1.0.0 | ? |
| woocommerce-alerts | v1.0.0 | ? |
| stripe-payment-alerts | v1.0.0 | ? |
| tiktok-shop-integration | v1.0.0 | 5 ⚠️ |

**Preis:** 199€/Monat (Bundle)

---

## Repository 5: social-media-suite
**Thema:** Social Media Automation (NEU)

| Skill | Version | Tests |
|-------|---------|-------|
| meta-business-automation | v2.0.0 | 19 ✅ |
| linkedin-scheduler | v1.0.0 | ? |

**Preis:** 99€/Monat (Bundle)

---

## Repository 6: executive-productivity
**Thema:** Produktivität & Kalender
**Basis:** executive-kalender (erweitert)

| Skill | Version | Tests |
|-------|---------|-------|
| notion-ical-sync | v1.0.0 | ? |
| executive-kalender | v? | ? |

**Preis:** 79€/Monat (Bundle)

---

## Repository 7: inbox-ai-core
**Thema:** Email Automation & Kommunikation
**Basis:** inbox-ai-template (erweitert)

| Skill | Version | Tests |
|-------|---------|-------|
| inbox-ai | v3.0.0 | 20+ ✅ |
| sevdesk | v2.4.0 | 15+ ✅ |
| gmail-auto-responder | v1.0.0 | 11 ✅ |

**Preis:** 199€/Monat (Bundle)

---

## Repository 8: voice-automation
**Thema:** Voice & Audio Workflows
**Basis:** voice-workflow (erweitert)

| Skill | Version | Tests |
|-------|---------|-------|
| voice-workflow | v? | ? |
| (erweiterbar mit TTS/STT) | | |

**Preis:** 149€/Monat (Bundle)

---

## Repository 9: crypto-defi-suite
**Thema:** Krypto & DeFi (bestehend)

| Skill | Version | Tests |
|-------|---------|-------|
| a2a-market | v1.0 | ✅ |
| aave-liquidation-monitor | v1.0 | ✅ |

**Preis:** 99€/Monat (Bundle)

---

## Repository 10: social-platform-agents
**Thema:** Soziale Plattformen (bestehend)

| Skill | Version | Tests |
|-------|---------|-------|
| 37soul | v1.0 | ✅ |
| 24konbini | v1.0 | ✅ |

**Preis:** Freemium

---

## GitHub Push Plan

### Repositories erstellen (falls nicht vorhanden):
```bash
# Neue Repos erstellen
github-repo-create german-accounting-suite
github-repo-create lead-pipeline-suite
github-repo-create e-commerce-automation
github-repo-create social-media-suite

# Bestehende aktualisieren
github-repo-update competitive-intelligence
github-repo-update executive-productivity
github-repo-update inbox-ai-core
github-repo-update voice-automation
```

### Push Reihenfolge:
1. **german-accounting-suite** (höchste Priorität)
2. **inbox-ai-core** (Core Produkt)
3. **lead-pipeline-suite** (Verkauf)
4. **competitive-intelligence** (Marketing)
5. **e-commerce-automation** (E-Commerce)
6. **social-media-suite** (Social)
7. **executive-productivity** (Productivity)
8. **voice-automation** (Voice)
9. **crypto-defi-suite** (Krypto)
10. **social-platform-agents** (Social)

---

## Benötigte GitHub Repositories

| # | Repo Name | Status | Skills |
|---|-----------|--------|--------|
| 1 | german-accounting-suite | NEU | 5 Skills |
| 2 | lead-pipeline-suite | NEU | 4 Skills |
| 3 | competitive-intelligence | EXISTIERT | 3 Skills |
| 4 | e-commerce-automation | NEU | 4 Skills |
| 5 | social-media-suite | NEU | 2 Skills |
| 6 | executive-productivity | EXISTIERT | 2 Skills |
| 7 | inbox-ai-core | EXISTIERT | 3 Skills |
| 8 | voice-automation | EXISTIERT | 1 Skill |
| 9 | crypto-defi-suite | NEU | 2 Skills |
| 10 | social-platform-agents | NEU | 2 Skills |

**Total: 28 Skills in 10 Repos**
