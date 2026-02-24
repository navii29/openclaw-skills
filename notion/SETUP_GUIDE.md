# 🎯 LinkedIn Lead Pipeline - Notion Setup Guide

## Datenbank-Struktur (Properties)

Füge diese Properties zur Datenbank hinzu:

| Property | Type | Options/Format |
|----------|------|----------------|
| Name | Title | (default) |
| Firma | Text | - |
| Titel | Text | - |
| Score | Number | 0-100 |
| Tier | Select | 🔥 HOT, ⚡ WARM, 🧊 COLD |
| Status | Select | NEW, CONTACTED, REPLY, MEETING, WON, LOST |
| Location | Text | - |
| LinkedIn | URL | - |
| Outreach | Text | - |
| Signals | Text | Komma-separiert |

## Views einrichten

### 1. Table View (Default)
- Alle Properties anzeigen
- Sort: Score (descending)

### 2. Board View (Kanban)
- Group by: Tier
- Columns: 🔥 HOT | ⚡ WARM | 🧊 COLD

### 3. Gallery View
- Card preview: Name + Firma
- Show: Score, Status

### 4. Filtered Views
- **Hot Leads:** Tier = 🔥 HOT
- **To Contact:** Status = NEW
- **Follow-up:** Status = CONTACTED oder REPLY

## CSV Import

Die Datei `notion/leads-import.csv` enthält Demo-Daten:

```csv
Name,Firma,Titel,Score,Tier,Status,Location,LinkedIn,Outreach,Signals
Max Mustermann,TechStart GmbH,CEO & Co-Founder,100,HOT,NEW,Berlin,https://linkedin.com/in/saas-founder-berlin,"Hi Max...","CEO (+25), SaaS (+15)"
```

### Import-Schritte:
1. Datenbank öffnen
2. `...` → "Merge with CSV"
3. Datei auswählen
4. Spalten zuweisen
5. Importieren

## Automation (optional)

### Notion Automations:
- Wenn Status = MEETING → Datum setzen
- Wenn Score > 80 → Tier = 🔥 HOT

### OpenClaw Integration:
```bash
# Lead hinzufügen
node agents/linkedin-orchestrator.js process <linkedin-url>

# Export nach Notion
node agents/export-to-notion.js
```

## Formeln (optional)

**Lead Quality Score (Formula):**
```
if(prop("Score") >= 80, "🔥 HOT", if(prop("Score") >= 60, "⚡ WARM", "🧊 COLD"))
```

## Schnelleinstieg

1. Seite erstellen: `🎯 LinkedIn Lead Pipeline`
2. `/database` → Empty database
3. Properties hinzufügen (siehe Tabelle)
4. Views erstellen (Board + Table)
5. CSV importieren
6. Fertig!
