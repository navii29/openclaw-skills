# CRM-Struktur: Lead Pipeline

## Übersicht

**Tool:** Notion (kostenlos) oder Airtable  
**Ziel:** Alle Leads systematisch tracken, Follow-ups nicht vergessen

---

## Pipeline-Stages

| Stage | Beschreibung | Wahrscheinlichkeit |
|-------|--------------|-------------------|
| **Neuer Lead** | Kontakt erfasst, noch nicht kontaktiert | 5% |
| **Kontaktiert** | Erste Nachricht gesendet | 10% |
| **Antwort erhalten** | Lead hat geantwortet (egal wie) | 30% |
| **Call gebucht** | Termin vereinbart | 60% |
| **Angebot gesendet** | Schriftliches Angebot übermittelt | 40% |
| **Verhandlung** | Preis/Scope diskutiert | 50% |
| **Geschlossen Gewonnen** | Deal abgeschlossen | 100% |
| **Geschlossen Verloren** | Deal nicht zustande gekommen | 0% |
| **Nurturing** | Nicht jetzt relevant, aber potenziell | 10% |

---

## Lead-Datenfelder

### Basis-Informationen
- **Name** (Text)
- **Firma** (Text)
- **Position** (Text)
- **Branche** (Select: Marketingberatung, Webdesign, Coaching, Rechtsberatung, Steuerberatung, Andere)
- **Firmengröße** (Select: 1, 2-5, 6-10, 11-25, 25+)
- **Website** (URL)
- **LinkedIn-Profil** (URL)

### Kontakt
- **E-Mail** (Email)
- **Telefon** (Phone)
- **Quelle** (Select: LinkedIn, Netzwerk, Referral, Inbound, Kaltakquise)
- **Erstkontakt-Datum** (Date)

### Qualifizierung (BANT)
- **Budget vorhanden?** (Select: Ja, Nein, Unklar)
- **Authority** (Select: Entscheider, Influencer, Unklar)
- **Need** (Select: Hoch, Mittel, Niedrig)
- **Timeline** (Select: Sofort, 1-3 Monate, 3-6 Monate, Unklar)
- **Score** (Formula: Je nach BANT-Antworten 0-100)

### Aktivität
- **Stage** (Select: Siehe oben)
- **Letzter Kontakt** (Date)
- **Nächster Follow-up** (Date)
- **Letzte Aktivität** (Text: Was wurde zuletzt gemacht?)
- **Nächste Aktivität** (Text: Was ist als nächstes geplant?)
- **Anzahl Touchpoints** (Number)

### Deal
- **Angebotssumme** (Number: €)
- **Wahrscheinlichkeit** (Number: %)
- **Erwarteter Umsatz** (Formula: Angebotssumme × Wahrscheinlichkeit)
- **Geschlossen am** (Date)
- **Abschlussgrund** (Select: Preis, Timing, Scope, Konkurrenz, Kein Bedarf, Sonstiges)
- **Notizen** (Long Text)

---

## Views (Ansichten)

### 1. Pipeline-Ansicht (Kanban)
- **Gruppierung:** Stage
- **Sortierung:** Nächster Follow-up (aufsteigend)
- **Anzeige:** Name, Firma, Branche, Nächster Follow-up, Angebotssumme

### 2. Follow-up Heute (Liste)
- **Filter:** Nächster Follow-up ≤ Heute AND Stage ≠ Geschlossen
- **Sortierung:** Nächster Follow-up (aufsteigend)
- **Anzeige:** Name, Firma, Letzte Aktivität, Nächste Aktivität

### 3. Hot Leads (Liste)
- **Filter:** Score ≥ 70 AND Stage ≠ Geschlossen
- **Sortierung:** Score (absteigend)
- **Anzeige:** Name, Firma, Score, Timeline, Angebotssumme

### 4. Won Deals (Liste)
- **Filter:** Stage = Geschlossen Gewonnen
- **Sortierung:** Geschlossen am (absteigend)
- **Anzeige:** Name, Firma, Angebotssumme, Geschlossen am

### 5. Lost Deals (Liste)
- **Filter:** Stage = Geschlossen Verloren
- **Sortierung:** Geschlossen am (absteigend)
- **Anzeige:** Name, Firma, Abschlussgrund, Notizen

### 6. Nurturing (Liste)
- **Filter:** Stage = Nurturing
- **Sortierung:** Letzter Kontakt (aufsteigend)
- **Anzeige:** Name, Firma, Letzter Kontakt, Notizen

---

## KPI-Dashboard

### Metriken (wöchentlich aktualisieren)

| Metrik | Formel | Ziel |
|--------|--------|------|
| **Neue Leads/Woche** | COUNT(Leads where Erstkontakt-Datum ≥ letzte 7 Tage) | ≥ 10 |
| **Conversion Lead → Call** | Calls gebucht / Neue Leads | ≥ 20% |
| **Conversion Call → Angebot** | Angebote gesendet / Calls gebucht | ≥ 50% |
| **Conversion Angebot → Deal** | Geschlossen Gewonnen / Angebote gesendet | ≥ 30% |
| **Durchschnittliche Deal-Größe** | SUM(Angebotssumme) / COUNT(Won Deals) | ≥ €2.500 |
| **Pipeline-Wert** | SUM(Erwarteter Umsatz) where Stage ≠ Geschlossen | ≥ €50.000 |
| **Follow-up Rate** | Leads mit Nächster Follow-up / Alle offene Leads | 100% |

### Visualisierungen
- **Pipeline-Funnel:** Chart mit Stages und Conversion-Rates
- **Umsatz nach Monat:** Bar Chart (Won Deals gruppiert nach Geschlossen am)
- **Top Quellen:** Pie Chart (Leads gruppiert nach Quelle)
- **Verlorene Deals nach Grund:** Bar Chart (Lost Deals gruppiert nach Abschlussgrund)

---

## Workflow & Prozesse

### Täglich (10 Minuten)
1. View "Follow-up Heute" öffnen
2. Für jeden Lead: Aktivität durchführen und eintragen
3. Nächsten Follow-up terminieren
4. Stage aktualisieren (falls nötig)

### Wöchentlich (30 Minuten)
1. Neue Leads aus Apollo.io/LinkedIn hinzufügen
2. KPI-Dashboard überprüfen
3. Hot Leads priorisieren
4. Pipeline-Funnel analysieren: Wo fallen Leads ab?

### Monatlich (1 Stunde)
1. Won Deals reviewen: Was hat funktioniert?
2. Lost Deals analysieren: Gemeinsame Muster?
3. Quellen-Performance: Welcher Kanal liefert beste Leads?
4. Ziele für nächsten Monat setzen

---

## Automatisierungs-Ideen (Optional)

Mit n8n könnten wir:
- Neue Leads automatisch aus Apollo.io importieren
- Follow-up Erinnerungen per Telegram/Discord senden
- Stage-Änderungen loggen
- KPI-Dashboard automatisch aktualisieren

---

## Notion-Template Setup

1. **Neue Datenbank erstellen:** "Lead Pipeline"
2. **Properties hinzufügen:** Alle oben genannten Felder
3. **Views erstellen:** Pipeline, Follow-up Heute, Hot Leads, Won/Lost, Nurturing
4. **Templates erstellen:** Neuer Lead (vordefinierte Werte)
5. **KPI-Dashboard:** Separate Seite mit Formeln und Charts

**Alternativ:** Airtable (bessere Automatisierungs-Optionen)

---

*CRM wird bei ersten 5 Kunden manuell geführt. Ab 10 Kunden sollten wir automatisieren.*
