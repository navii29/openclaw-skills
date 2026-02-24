# Notion CRM Template

## Datenbank: Lead Pipeline

### Properties (Eigenschaften)

| Property Name | Type | Options / Format |
|--------------|------|------------------|
| **Name** | Title | - |
| **Firma** | Text | - |
| **E-Mail** | Email | - |
| **Telefon** | Phone | - |
| **LinkedIn** | URL | - |
| **Stage** | Select | New Lead → Contacted → Response → Call Booked → Offer Sent → Negotiation → Closed Won → Closed Lost → Nurturing |
| **ICP** | Select | Marketing-Berater, Webdesign-Agentur, Business-Coach, Andere |
| **Quelle** | Select | LinkedIn, Xing, Clutch, Referral, Inbound, Kaltakquise |
| **Budget** | Select | Ja, Nein, Unklar |
| **Timeline** | Select | Sofort, 1-3 Monate, 3-6 Monate, Unklar |
| **BANT Score** | Number | 0-100 (Formel: Budget×25 + Authority×20 + Need×25 + Timeline×15) |
| **Angebotssumme** | Number | € |
| **Wahrscheinlichkeit** | Number | % |
| **Erwarteter Umsatz** | Formula | prop("Angebotssumme") × prop("Wahrscheinlichkeit") / 100 |
| **Letzter Kontakt** | Date | - |
| **Nächster Follow-up** | Date | - |
| **Notizen** | Text | - |
| **Created** | Created time | - |
| **Last Edited** | Last edited time | - |

---

## Views (Ansichten)

### 1. Pipeline (Board View)
- **Group by:** Stage
- **Sort:** Nächster Follow-up (Ascending)
- **Cards:** Name, Firma, ICP, BANT Score, Nächster Follow-up

### 2. Follow-up Heute (List View)
- **Filter:** Nächster Follow-up ≤ Today AND Stage ≠ Closed Won AND Stage ≠ Closed Lost
- **Sort:** Nächster Follow-up (Ascending)
- **Columns:** Name, Firma, Stage, Letzter Kontakt

### 3. Hot Leads (List View)
- **Filter:** BANT Score ≥ 70 AND Stage ≠ Closed Won AND Stage ≠ Closed Lost
- **Sort:** BANT Score (Descending)
- **Columns:** Name, Firma, BANT Score, Timeline, Angebotssumme

### 4. Won Deals (List View)
- **Filter:** Stage = Closed Won
- **Sort:** Last Edited (Descending)
- **Columns:** Name, Firma, Angebotssumme, Created

### 5. Lost Deals (List View)
- **Filter:** Stage = Closed Lost
- **Sort:** Last Edited (Descending)
- **Columns:** Name, Firma, Notizen

### 6. Nurturing (List View)
- **Filter:** Stage = Nurturing
- **Sort:** Letzter Kontakt (Ascending)
- **Columns:** Name, Firma, Letzter Kontakt, Notizen

---

## Templates (Vorlagen)

### Neuer Lead
```
**Qualifizierung:**
- Budget: [Ja/Nein/Unklar]
- Authority: [Entscheider/Influencer/Unklar]
- Need: [Hoch/Mittel/Niedrig]
- Timeline: [Sofort/1-3M/3-6M/Unklar]

**Erster Kontakt:**
- Datum: 
- Kanal: [LinkedIn/E-Mail/Call]
- Notizen:

**Nächster Schritt:**
- Aktion: 
- Datum: 
```

---

## Import-Datei (CSV)

Für schnellen Start: 10 Beispiel-Leads

```csv
Name,Firma,E-Mail,LinkedIn,Stage,ICP,Quelle,Budget,Timeline,BANT Score
Max Mustermann,Mustermann Marketing,max@mustermann.de,https://linkedin.com/in/maxmustermann,New Lead,Marketing-Berater,LinkedIn,Ja,1-3 Monate,85
Lisa Schmidt,Schmidt Digital,lisa@schmidtdigital.de,https://linkedin.com/in/lisaschmidt,New Lead,Webdesign-Agentur,LinkedIn,Ja,Sofort,75
Dr. Anna Weber,Weber Coaching,anna@webercoaching.de,https://linkedin.com/in/annaweber,New Lead,Business-Coach,Xing,Unklar,1-3 Monate,60
... (weitere 7 Beispiele)
```

---

## Automatisierungen (Notion)

### 1. Follow-up Erinnerung
- **Trigger:** Nächster Follow-up = Today
- **Action:** Sende Slack/Telegram Notification

### 2. Stage-Change Log
- **Trigger:** Stage changed
- **Action:** Append to Notizen: "[Datum]: Stage changed from X to Y"

---

## Setup-Anleitung (5 Minuten)

1. **Notion öffnen** → Neue Seite "NAVII CRM"
2. **Datenbank erstellen** → "Lead Pipeline"
3. **Properties einfügen** (siehe oben)
4. **Views konfigurieren** (siehe oben)
5. **Template erstellen** (siehe oben)
6. **Erste 10 Leads eintragen**

FERTIG. GO.
