# Standard-Architektur: Lead-to-Meeting

## System-Übersicht

```
Lead-Quelle (Formular/E-Mail) 
    ↓
OpenClaw Agent (Qualifizierung)
    ↓
Entscheidung:
    ├─ Nicht qualifiziert → Abfuhr-Mail
    ├─ Unklar → Nachfrage-Mail
    └─ Qualifiziert → Terminlink + Benachrichtigung
    ↓
Kalender-Buchung
    ↓
Erinnerungen + Vorbereitung
```

## Komponenten

### 1. Lead-Eingang
**Option A: Kontaktformular**
- Webhook an OpenClaw
- Felder: Name, E-Mail, Firma, Budget, Timeline, Projektbeschreibung

**Option B: E-Mail-Monitoring**
- Dedicated Inbox (leads@kunde.de)
- OpenClaw liest und verarbeitet

### 2. Qualifizierungs-Agent
**Prompt-Logik:**
```
Du bist ein Sales-Qualifikations-Agent.

Bewerte diesen Lead nach:
1. BUDGET: Explizit genannt oder implizit erkennbar? (0-10)
2. TIMELINE: Konkreter Zeitrahmen oder "irgendwann"? (0-10)
3. FIT: Passen wir als Lösung? (0-10)

SCORE ≥ 20: Qualifiziert
SCORE 10-19: Nachfragen nötig
SCORE < 10: Nicht qualifiziert

Output als JSON.
```

### 3. Antwort-Router
- **Qualifiziert:** Sende Calendly-Link + Slack-Benachrichtigung
- **Nachfrage:** Stelle gezielte Rückfragen
- **Abgelehnt:** Höfliche Standard-Antwort

### 4. Post-Booking
- 24h vorher: Erinnerung an Lead
- 1h vorher: Erinnerung an Lead + Zusammenfassung an Verkäufer
- Nach Meeting: Follow-up-Template

## Technische Basis
- **OpenClaw:** Core-Logik + Agenten
- **n8n:** Workflows (Webhook → Verarbeitung → Aktionen)
- **Calendly/Google Calendar:** Terminbuchung
- **Telegram/Discord:** Notifications

## Customization-Points
Pro Kunde anpassbar:
- Qualifizierungs-Kriterien
- E-Mail-Templates
- Benachrichtigungs-Kanäle
- CRM-Integration (optional)
